import json
import os

# --- 設定 ---
# 1. YouTube API等から自動更新されるファイル
ARCHIVE_AUTO = 'archives/archive_videos.json'
# 2. 手動で情報の修正・追加を行うファイル（最優先）
ARCHIVE_EXT = 'archives/external_videos.json'
# 3. すでに完成し、サイトに掲載済みのデータ（読み込み専用・保護対象）
MASTER_SONGS = 'songs/videos.json'
# 4. これから作業が必要な新着・修正分の出力先
DRAFT_OUTPUT = 'songs/draft_songs.json'

# 下書きに抽出する対象のカテゴリ・タグ
TARGET_TAGS = ["歌動画", "歌配信", "楽器配信・動画", "踊り動画", "踊り配信", "殺陣"]

def load_json(path):
    """JSONファイルを安全に読み込む"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                print(f"⚠️ {path} の解析に失敗しました。空リストとして扱います。")
                return []
    return []

def main():
    # 各データの読み込み
    auto_data = load_json(ARCHIVE_AUTO)
    ext_data = load_json(ARCHIVE_EXT)
    master_data = load_json(MASTER_SONGS)

    # すでに本番(videos.json)に存在する動画IDをセットに記録（重複排除用）
    master_ids = {v['youtubeId'] for v in master_data if 'youtubeId' in v}

    # --- 統合処理 (Externalを優先) ---
    # まず自動取得分をベースに辞書を作成
    combined_archives = {v['youtubeId']: v for v in auto_data if 'youtubeId' in v}
    # External(手動修正分)で上書き、または新規追加
    for v in ext_data:
        yid = v.get('youtubeId')
        if yid:
            combined_archives[yid] = v

    # --- 抽出処理 ---
    new_drafts = []
    for yid, v in combined_archives.items():
        # 重要：すでに本番(videos.json)にある動画は、下書きには入れない
        if yid in master_ids:
            continue
        
        # 歌・踊りに関連する動画かチェック
        def ensure_list(data):
            if isinstance(data, list):
                return data
            if data is None:
                return []
            return [data] # 文字列などが来たら [ ] で包む

        v_tags = ensure_list(v.get('tags', [])) + ensure_list(v.get('category', []))
        
        if any(t in TARGET_TAGS for t in v_tags):
            draft_item = v.copy()
            
            # 1. songsキー自体がない、または None の場合のみ初期化
            if 'songs' not in draft_item or draft_item['songs'] is None:
                draft_item['songs'] = []

            # 2. songsが「完全に空のリスト」である場合のみ、雛形を入れる
            # すでに一つでも曲（修正後のデータ）が入っていれば、ここはスキップされます
            if len(draft_item['songs']) == 0:
                draft_item['songs'] = [{
                    "title": "要確認",
                    "artist": "",
                    "start": 0,
                    "tags": ["要確認(手動修正してください)"]
                }]
            
            new_drafts.append(draft_item)

    # 日付の降順（新しい順）で並び替え
    new_drafts.sort(key=lambda x: x.get('date', ''), reverse=True)

    # --- 保存処理 ---
    # videos.json は一切書き換えません（'w'モードで開かない）
    if new_drafts:
        with open(DRAFT_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(new_drafts, f, indent=2, ensure_ascii=False)
        print(f"✨ 処理完了: {len(new_drafts)} 件の未登録動画を {DRAFT_OUTPUT} に書き出しました。")
        print(f"ℹ️ {MASTER_SONGS} に登録済みの動画はスキップされました。")
    else:
        # 新着がない場合は、混乱を避けるため空のリストで上書きするか、メッセージを出す
        with open(DRAFT_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        print("☕ 新しく追加すべき動画（未登録の歌・踊り動画）はありませんでした。")

if __name__ == "__main__":
    main()
