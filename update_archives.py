import os
import json
import base64
import re
from datetime import datetime
from googleapiclient.discovery import build
import requests
import sys

# --- 1. 設定値 ---
# GitHub Actions等の環境変数から取得することを想定
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO_OWNER = "keihanmatcha"
GITHUB_REPO_NAME = "oukasui"
JSON_FILE_PATH = "archives/archive_videos.json"
MAX_PAGES_TO_FETCH = 100

CHANNELS = [
    {
        "id": "UCXW4MqCQn-jCaxlX-nn-BYg",
        "name": "長尾景"
    },
    {
        "id": "UCh-GyPNxvjTsza0ptjnkh1w",
        "name": "VΔLZ",
        "fixed_tags": ["甲斐田晴", "弦月藤士郎", "VΔLZ"]
    }
]

# 管理対象のチャンネル名リスト
MANAGED_CHANNEL_NAMES = [ch["name"] for ch in CHANNELS]

# --- 2. 自動タグ付け用の辞書定義 ---
CATEGORY_LIST = [
    "ゲーム実況", "雑談", "歌配信", "歌動画", "踊り動画", "踊り配信",
    "記念配信", "殺陣", "お披露目配信", "3D", "企画", "大会", "対談",
    "ライブイベント", "楽器配信・動画", "プロモーション", "公式企画・番組",
    "動画系", "公式切り抜き", "手描き動画", "ぷちさんじ"
]

# (辞書データは長いので、ロジックに必要な部分以外はご提示のものをそのまま利用します)
# ※ 実際のファイルではここに KEYWORD_GROUPS, TAG_CONVERSION_MAP, HANDLE_TO_NAME_MAP, UNIT_GROUP_MAP を配置してください
# -----------------------------------------------------------------------------
# ここにご提示いただいた辞書データ（KEYWORD_GROUPSなど）を貼り付けてください
# 今回はロジック修正のため、辞書変数は既に定義されているものとして扱います
# -----------------------------------------------------------------------------

# ★修正: パフォーマンス最適化のため、ループ外で小文字化マップを作成
HANDLE_MAP_LOWER = {k.lower(): v for k, v in HANDLE_TO_NAME_MAP.items()}

# --- 3. タグ判定関数 (修正・強化版) ---
def analyze_video_tags(title, description, fixed_tags):
    detected_category = "未分類"
    detected_keywords = set()
    
    title_lower = str(title).lower()
    description_lower = str(description).lower() if description else ""

    # 1. カテゴリ判定 (タイトルにカテゴリ名そのものが含まれる場合)
    # 文字列が長い順にソートして判定（例：「歌動画」を「動画」より先にマッチさせるため）
    for cat in sorted(CATEGORY_LIST, key=len, reverse=True):
        if cat in title:
            detected_category = cat
            break

    # 2. キーワード判定 (グループ辞書から)
    for group_name, keyword_list in KEYWORD_GROUPS.items():
        for keyword in keyword_list:
            if keyword.lower() in title_lower:
                detected_keywords.add(keyword)

    # 3. 特別判定処理
    if re.search(r'【[^】]*える[^】]*】', title):
        detected_keywords.add("える")
    if re.search(r'【[^】]*叶[^】]*】', title):
        detected_keywords.add("叶")

    # 4. 表記ゆれ・略称から正式タグを追加
    # ★ここが重要: 「歌ってみた」→「歌動画」に変換された場合、キーワードに追加される
    for slang, formal_tag in TAG_CONVERSION_MAP.items():
        if slang.lower() in title_lower:
            detected_keywords.add(formal_tag)

    # 5. ハンドルネーム(@xxxx)の検出 (最適化済みマップを使用)
    found_handles = re.findall(r'(@[\w\.\-]+)', description_lower)
    for handle in found_handles:
        if handle in HANDLE_MAP_LOWER:
            detected_keywords.add(HANDLE_MAP_LOWER[handle])

    # 6. ユニットとメンバーの相互補完
    for unit_name, members in UNIT_GROUP_MAP.items():
        # ユニット名があればメンバーを追加
        if unit_name in detected_keywords:
            for member in members:
                detected_keywords.add(member)
        # メンバーが全員揃っていればユニット名を追加
        if set(members).issubset(detected_keywords):
            detected_keywords.add(unit_name)

    # 7. チャンネル固有の固定タグを追加
    if fixed_tags:
        for tag in fixed_tags:
            detected_keywords.add(tag)

    # 8. カテゴリの自動修正 (キーワードからカテゴリを逆算)
    # ★追加機能: もしキーワードの中に「カテゴリリストにある言葉」が含まれていて、
    # 現在のカテゴリが「未分類」なら、それをカテゴリに昇格させる
    if detected_category == "未分類":
        for kw in detected_keywords:
            if kw in CATEGORY_LIST:
                detected_category = kw
                break

    # 9. ゲーム実況の判定 (既存ロジック)
    has_game_keyword = False
    games_set = set(KEYWORD_GROUPS["GAMES"])
    if not detected_keywords.isdisjoint(games_set):
        has_game_keyword = True
    
    if has_game_keyword:
        if detected_category == "未分類":
            detected_category = "ゲーム実況"
        elif detected_category != "ゲーム実況":
            detected_keywords.add("ゲーム実況")
  
    return detected_category, list(detected_keywords)

# --- 4. YouTube API ---
def get_uploads_playlist_id(youtube, channel_id):
    try:
        resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
        return resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"❌ Error getting playlist ID: {e}")
        return None

def fetch_videos_from_playlist(youtube, playlist_id, channel_name, fixed_tags):
    videos = []
    next_page_token = None
    page_count = 0
    
    print(f"🔍 {channel_name} の動画を取得開始...")
    
    while page_count < MAX_PAGES_TO_FETCH:
        try:
            request = youtube.playlistItems().list(
                part='snippet,contentDetails', playlistId=playlist_id,
                maxResults=50, pageToken=next_page_token
            )
            response = request.execute()
            items = response.get('items', [])
            if not items: break
            
            for item in items:
                snippet = item['snippet']
                if not snippet.get('publishedAt'): continue
                
                # 日付変換の安全策
                try:
                    dt = datetime.strptime(snippet['publishedAt'][:10], '%Y-%m-%d')
                    published_date = dt.strftime('%Y-%m-%d')
                except ValueError:
                    published_date = "2000-01-01" # フォールバック

                video_id = item['contentDetails']['videoId']
                
                # タグ分析
                category, keywords = analyze_video_tags(snippet['title'], snippet.get('description', ''), fixed_tags)
                
                videos.append({
                    "youtubeId": video_id,
                    "title": snippet['title'],
                    "channel": channel_name,
                    "date": published_date,
                    "thumbnail": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                    "category": category, # リストではなく文字列で格納
                    "keywords": keywords,
                    "songs": []
                })
                
            next_page_token = response.get('nextPageToken')
            page_count += 1
            print(f"  - Page {page_count}: {len(videos)} videos fetched so far.")
            
            if not next_page_token: break
            
        except Exception as e:
            print(f"⚠️ Fetch Error on page {page_count}: {e}")
            break
            
    print(f"✅ {channel_name}: 合計 {len(videos)} 件取得成功")
    return videos

# --- 5. GitHub更新処理 (修復機能付き) ---
def update_github_json(new_videos):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    contents_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{JSON_FILE_PATH}"

    # 既存ファイルの取得
    response = requests.get(contents_url, headers=headers)
    existing_videos = []
    existing_sha = None

    if response.status_code == 200:
        content_info = response.json()
        existing_content = content_info['content']
        existing_sha = content_info['sha']
        try:
            decoded_content = base64.b64decode(existing_content).decode('utf-8-sig') # BOM対策
            existing_videos = json.loads(decoded_content)
        except json.JSONDecodeError as e:
            print(f"⚠️ 【警告】GitHub上のJSONファイルが破損しています (Line {e.lineno}, Col {e.colno})。")
            print("   👉 既存データを破棄し、取得したデータでファイルを再生成（修復）します。")
            existing_videos = []
        except Exception:
            print("⚠️ 予期せぬエラーによりファイルを初期化します。")
            existing_videos = []
    else:
        print(f"ℹ️ ファイルが見つかりません (Status: {response.status_code})。新規作成します。")
        existing_videos = []

    # マージ処理
    # 他のチャンネル（外部コラボなど手動追加分）は保持する
    preserved_videos = [v for v in existing_videos if v.get('channel') not in MANAGED_CHANNEL_NAMES]
    
    # 今回更新するチャンネルの動画マップを作成
    managed_map = {v['youtubeId']: v for v in existing_videos if v.get('channel') in MANAGED_CHANNEL_NAMES}
    
    updated_count = 0
    added_count = 0

    for new_video in new_videos:
        vid_id = new_video['youtubeId']
        
        if vid_id in managed_map:
            existing_record = managed_map[vid_id]
            is_changed = False
            
            # songs情報の保護 (上書きしない)
            if 'songs' not in existing_record: existing_record['songs'] = []
            
            # カテゴリ更新
            if existing_record.get('category') != new_video['category']:
                existing_record['category'] = new_video['category']
                is_changed = True
                
            # キーワード更新 (既存のタグ + 新しいタグ で重複削除)
            current_kws = set(existing_record.get('keywords', []))
            new_kws = set(new_video['keywords'])
            
            if current_kws != new_kws:
                # 結合して更新（手動でつけたタグが消えないように和集合をとる場合）
                # 今回は自動タグ付けの精度を信じて、自動生成されたタグを優先しつつ
                # 必要なら existing_record['keywords'] = list(current_kws | new_kws) とする
                # ここでは「最新の辞書ルールを適用したい」という意図を汲み、再生成されたタグを採用します
                # ただし、手動タグを残したい場合は下記のようにします：
                # merged_keywords = list(current_kws | new_kws)
                # existing_record['keywords'] = merged_keywords
                
                # 自動タグシステムの修正目的なので、今回は最新のロジックで上書きします
                existing_record['keywords'] = list(new_kws)
                is_changed = True
            
            if is_changed: updated_count += 1
            managed_map[vid_id] = existing_record
        else:
            # 新規追加
            managed_map[vid_id] = new_video
            added_count += 1

    # 最終リストの作成 (日付順ソート)
    final_videos_list = preserved_videos + list(managed_map.values())
    final_videos_list.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    print(f"📦 コミット準備: 新規{added_count}件, 更新{updated_count}件, 総数{len(final_videos_list)}件")
    
    # JSONシリアライズ
    new_content_bytes = json.dumps(final_videos_list, indent=2, ensure_ascii=False).encode('utf-8')
    new_content_base64 = base64.b64encode(new_content_bytes).decode('utf-8')

    commit_data = {
        "message": f"ARCHIVE_BOT: Repair & Update (Add {added_count}, Update {updated_count})",
        "content": new_content_base64,
        "sha": existing_sha
    }

    put_res = requests.put(contents_url, headers=headers, json=commit_data)
    if put_res.status_code in [200, 201]:
        print(f"🚀 GitHubコミット完了！ファイルが正常に更新されました。")
    else:
        print(f"❌ コミット失敗: {put_res.status_code}")
        print(put_res.text)

# --- 6. メイン処理 ---
def main():
    print("--- 長尾景＆VΔLZ アーカイブ全件更新スクリプト開始 ---")
    if not YOUTUBE_API_KEY or not GITHUB_TOKEN:
        print("❌ エラー: 環境変数 (YOUTUBE_API_KEY, GITHUB_TOKEN) が設定されていません")
        return

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    fetched_videos = []
    
    for ch in CHANNELS:
        playlist_id = get_uploads_playlist_id(youtube, ch['id'])
        if playlist_id:
            fixed_tags = ch.get('fixed_tags', [])
            videos = fetch_videos_from_playlist(youtube, playlist_id, ch['name'], fixed_tags)
            fetched_videos.extend(videos)

    if fetched_videos:
        update_github_json(fetched_videos)
    else:
        print("⚠️ 動画が1件も取得できませんでした。")

if __name__ == "__main__":
    main()
