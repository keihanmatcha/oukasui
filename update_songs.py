import json
import os

# --- 設定 ---
ARCHIVE_FILE = 'archives/archive_videos.json'
MASTER_SONGS_FILE = 'songs/videos.json'  # 読み込み専用
DRAFT_SONGS_FILE = 'songs/draft_songs.json' # 書き出し専用（下書き）

TARGET_TAGS = ["歌動画", "歌配信", "楽器配信・動画", "踊り動画", "踊り配信", "殺陣"]

def main():
    # 1. データの読み込み
    if not os.path.exists(ARCHIVE_FILE): return
    with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
        archive_data = json.load(f)
    
    # 既存のマスターデータをIDで把握（既にあるものは下書きに入れないため）
    master_songs = []
    if os.path.exists(MASTER_SONGS_FILE):
        with open(MASTER_SONGS_FILE, 'r', encoding='utf-8') as f:
            master_songs = json.load(f)
    master_ids = {v['youtubeId'] for v in master_songs}

    # 2. アーカイブから「未登録」かつ「歌系」の動画を抽出
    new_drafts = []
    for v in archive_data:
        if v['youtubeId'] in master_ids:
            continue # すでに videos.json にあるものは無視
        
        v_tags = v.get('tags', []) + v.get('category', [])
        if any(t in TARGET_TAGS for t in v_tags):
            # アーティスト名から「仮」のタグを振る（あとで人間が直す前提）
            # ここではあえて「要確認」などのタグを付けても良いかもしれません
            draft_v = v.copy()
            for song in draft_v.get('songs', []):
                song['tags'] = ["要確認(手動で修正してください)"]
            
            new_drafts.append(draft_v)

    # 3. 下書きファイルとして保存
    # videos.json には一切影響を与えません
    if new_drafts:
        with open(DRAFT_SONGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_drafts, f, indent=2, ensure_ascii=False)
        print(f"📝 新着 {len(new_drafts)} 件の下書きを {DRAFT_SONGS_FILE} に作成しました。")
    else:
        print("☕ 新着の歌・踊り動画はありませんでした。")

if __name__ == "__main__":
    main()
