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
HANDLE_TO_NAME_MAP = {
    "@KaidaHaru": "甲斐田晴", "@GenzukiTojiro": "弦月藤士郎", "@NagaoKei": "長尾景", "@valz_ch": "VΔLZ", "@Fumi": "フミ",
    "@KaidaHaru": "甲斐田晴", "@GenzukiTojiro": "弦月藤士郎","@valz_ch": "VΔLZ", "@Fumi": "フミ",
    "@HoshikawaSara": "星川サラ", "@YamagamiKaruta": "山神カルタ", "@TodoKohaku": "東堂コハク", "@OliverEvans": "オリバー・エバンス",
    "@HarusakiAir": "春崎エアル", "@NishizonoChigusa": "西園チグサ", "@LainPaterson": "レイン・パターソン",
    "@SeraphDazzlegarden": "セラフ・ダズルガーデン", "@ShibuyaHajime": "渋谷ハジメ", "@YuhiRiri": "夕陽リリ", "@Elu": "える",
    "@SukoyaKana": "健屋花那", "@GweluOsGar": "グウェル・オス・ガール", "@AkagiWen": "赤城ウェン", "@HoshirubeSho": "星導ショウ",
    "@SakakiNess": "榊ネス", "@FrenELustario": "フレン・E・ルスタリオ", "@PontoNei": "先斗寧", "@SasakiSaku": "笹木咲",
    "@FuwaMinato": "不破湊", "@YukishiroMahiro": "雪城眞尋", "@OnomachiHaruka": "小野町春香", "@kuramochimerto": "倉持めると",
    "@SaegusaAkina": "三枝明那", "@MayuzumiKai": "黛灰", "@HonmaHimawari": "本間ひまわり", "@TakamiyaRion": "鷹宮リオン",
    "@KurusuNatsume": "来栖夏芽", "@Naraka": "奈羅花", "@WataraiHibari": "渡会雲雀", "@Ryushen": "緑仙", "@HakaseFuyuki": "葉加瀬冬雪",
    "@KoshimizuToru": "小清水透", "@HanabatakeChaika": "花畑チャイカ", "@MaimotoKeisuke": "舞元啓介", "@KagamiHayato": "加賀美ハヤト",
    "@ShiorihaRuri": "栞葉るり", "@TsukinoMito": "月ノ美兎", "@YukiChihiro": "勇気ちひろ", "@HiguchiKaede": "樋口楓", "@FushimiGaku": "伏見ガク",
    "@GilzarenIII": "ギルザレンIII世", "@KenmochiToya": "剣持刀也", "@Kanae": "叶", "@ShiinaYuika": "椎名唯華", "@Dola": "ドーラ",
    "@TodorokiKyoko": "轟京子", "@SisterClaire": "シスター・クレア", "@YashiroKizuku": "社築", "@SuzukiMasaru": "鈴木勝",
    "@MachidaChima": "町田ちま", "@JoeRikiichi": "ジョー・力一", "@BelmondBanderas": "ベルモンド・バンデラス", "@YagurumaRine": "矢車りね",
    "@KuroiShiba": "黒井しば", "@WarabedaMeiji": "童田明治", "@InuiToko": "戌亥とこ", "@LeviElipha": "レヴィ・エリファ",
    "@YorumiRena": "夜見れな", "@ArsAlmal": "アルス・アルマル", "@AibaUiha": "相羽ういは", "@AmamiyaKokoro": "天宮こころ",
    "@ElieConifer": "エリー・コニファー", "@RatnaPetit": "ラトナ・プティ", "@HayaseSou": "早瀬走", "EmmaAugust": "えま★おうがすと",
    "@LuisCammy": "ルイス・キャミー", "@ShirayukiTomoe": "白雪巴", "@MashiroMeme": "ましろ爻", "@MelissaKinrenka": "メリッサ・キンレンカ",
    "@Ibrahim": "イブラヒム", "@KitakojiHisui": "北小路ヒスイ", "@AxiaCrone": "アクシア・クローネ", "@LaurenIroas": "ローレン・イロアス",
    "@LeosVincent": "レオス・ヴィンセント", "@UmiseYotsuha": "海妹四葉", "@HyakumantenbaraSalome": "壱百満天原サロメ",
    "@FurakuKanato": "風楽奏斗", "@ShikinagiAkira": "四季凪アキラ", "@ShishidoAkari": "獅子堂あかり", "@KaburagiRoco": "鏑木ろこ",
    "@IgarashiRika": "五十嵐梨花", "@IshigamiNozomi": "石神のぞみ", "@Sophia_Valentine": "ソフィア・ヴァレンタイン",
    "@SaikiIttetsu": "佐伯イッテツ", "@UsamiRito": "宇佐美リト", "@HibachiMana": "緋八マナ", "@MurakumoKagetsu": "叢雲カゲツ",
    "@KoyanagiRou": "小柳ロウ", "@InamiRai": "伊波ライ", "@kaisei": "魁星", "@KitamiYusei": "北見遊征", "@NagisaTrout": "渚トラウト",
    "@MilanKestrel": "ミラン・ケストレル", "@SakayoriSoma": "酒寄颯馬", "@NanaseSuzuna": "七瀬すず菜", "@HitotsubashiAyato": "一橋綾人",
    "@ItsukiSakyo": "五木左京", "@TogawaNonoha": "十河ののは", "@KozueMone": "梢桃音", "@LunLun_nijisanji": "ルンルン",
    "@ShiroseIsumi": "城瀬いすみ", "@KiraraTamako": "雲母たまこ", "@Saotomeberry": "早乙女ベリー", "@KadooMikaru": "蝸堂みかる",
    "@ShigaRiko": "司賀りこ", "@TachitsuteToto": "立伝都々", "@TamanoiNana": "珠乃井ナナ", "@ShinomiyaYuno": "篠宮ゆの",
    "@Kisara_nijisanji": "綺沙良", "@NekoyashikiMiku": "猫屋敷美紅", "@SumeragiReo": "皇れお", "@HanakagoTsubasa": "花籠つばさ",
    "@VALZ_ch": "VΔLZ", "@Suzuya_Aki": "鈴谷アキ", "@Moira": "モイラ", "@SuzukaUtako": "鈴鹿詩子", "@IenagaMugi": "家長むぎ",
    "@FuminoTamaki": "文野環", "@MorinakaKazaki": "森中花咲", "@AkabaneYouko": "赤羽葉子", "@MakainoRirimu": "魔界ノりりむ",
    "@AzuchiMomo": "安土桃", "@UzukiKou": "卯月コウ", "@AsukaHina": "飛鳥ひな", "@AmemoriSayo": "雨森小夜", "@NaruseMei": "成瀬鳴",
    "@SakuraRitsuki": "桜凛月", "@YumeoiKakeru": "夢追翔", "@YuzukiRoa": "夢月ロア", "@AngeKatrina": "アンジュ・カトリーナ",
    "@LizeHelesta": "リゼ・ヘルエスタ", "@ExAlbio": "エクス・アルビオ", "@NuiSociere": "ニュイ・ソシエール", "@HayamaMarin": "葉山舞鈴",
    "@Matsukaimao": "魔使マオ", "@SuoSango": "周央サンゴ", "@AsahinaAkane": "朝日南アカネ", "@AmagaseMuyu": "天ケ瀬むゆ",
    "@AmiciaMichella": "Amicia Michella", "@XiaEkavira": "Xia-Ekavira", "@ZEACornelia": "Zea-Cornelia", "@TakaRadjiman": "Taka Radjiman",
    "@DeremKado": "Derem Kado", "@NaraHaramaung": "Nara Haramaung", "@HanaMacchia": "Hana Macchia", "@MikaMelatika": "Mika Melatika",
    "@MiyuOttavia": "Miyu Ottavia", "@LaylaAstroemeria": "Layla Astroemeria", "@RiksaDhirendra": "Riksa Dhirendra",
    "@NagisaArcinia": "Nagisa Arcinia", "@EtnaCrimson": "Etna Crimson", "@Azura Cecillia": "Azura Cecillia", "@RaiGalilei": "Rai Galilei",
    "@RezaAvanluna": "Reza Avanluna", "@BonnivierPranaja": "Bonnivier Pranaja", "@SiskaLeontyne": "Siska Leontyne",
    "@HyonaElatiora": "Hyona Elatiora", "@AkiraRay": "아키라 레이（明楽 レイ）", "@LeeRoha": "이로하（イ・ロハ）", "@OhJiyu": "오지유（オ・ジユ）",
    "@RyuHari": "류하리（リュ・ハリ）", "@Gaon": "가온（ガオン）", "@yuya_shin": "신유야（シン・ユヤ）", "@Seffyna": "세피나（セフィナ）",
    "@SoNagi": "소나기（ソ・ナギ）", "@NaSera": "나세라（ナ・セラ）", "@haYun": "하윤（ハ・ユン）", "@BanHada": "반하다（バン・ハダ）",
    "@MinSuha": "민수하（ミン・スゥーハ）", "@YangNari": "양나리（ヤン・ナリ）", "@IkeEveland": "Ike Eveland", "@AiaAmare": "Aia Amare",
    "@AlbanKnox": "Alban Knox", "@AsterArcadia": "Aster Arcadia", "@ClaudeClawmark": "Claude Clawmark", "@YugoAsuma": "Yugo Asuma",
    "@YuQ.Wilson": "YuQ.Wilson", "@VezaliusBandage": "Vezalius Bandage", "@VantacrowBringer": "VantacrowBringer",
    "@VictoriaBrightshield": "Victoria Brightshield", "@UkiVioleta": "Uki Violeta", "@DoppioDropscythe": "Doppio Dropscythe",
    "@HexHaywire": "Hex Haywire", "@EnnaAlouette": "Enna Alouette", "@EliraPendora": "Elira Pendora", "@FinanaRyugu": "Finana Ryugu",
    "@Freodore_nijisanji": "Freodore", "@ReimuEndou": "Reimu Endou", "@FulgurOvid": "Fulgur Ovid", "@MelocoKyoran": "Meloco Kyoran",
    "@KyoKaneko": "Kyo Kaneko", "@KotokaTorahime": "Kotoka Torahime", "@KaelixDebonair": "Kaelix Debonair", "@KunaiNakasato": "Kunai Nakasato",
    "@KlaraCharmwood": "Klara Charmwood", "@SonnyBrisko": "Sonny Brisko", "@ScarleYonaguni": "ScarleYonaguni", "@SelenTatsuki": "Selen Tatsuki",
    "@Seible": "Seible_nijisanji", "@petragurin": "Petra Gurin", "@PomuRainpuff": "Pomu Rainpuff", "@Rosemi_Lovelock": "Rosemi Lovelock",
    "@MariaMarionette": "Maria Marionette", "@MystaRias": "Mysta Rias", "@MillieParfait": "Millie Parfait", "@ShuYamino": "Shu Yamino",
    "@Twisty Amanozako": "Twisty Amanozako", "@VoxAkuma": "Vox Akuma", "@VerVermillion": "Ver Vermillion", "@LucaKaneshiro": "Luca Kaneshiro",
    "@ZealGinjoka": "Zeal Ginjoka", "@RenZotto": "Ren Zotto", "@RyomaBarrenwort": "Ryoma Barrenwort", "@Hoshimi-virtualreal1845": "星弥",
    "@noornijisanjiin7271": "Noor", "@PIROPARU": "字ぴろぱる", "@shibuyaHAL": "渋谷ハル", "@UTAIMEIKA": "歌衣メイカ",
    "@KanaeVCriminologist": "かなえ先生", "@Peanutskun": "ピーナッツくん", "@pokopea": "ぽんぽこ", "@_Ubiba": "ばあちゃる",
    "@lisahanabusa": "英リサ", "@TOMARI_MARI": "兎麹まり", "@uruhaichinose": "一ノ瀬うるは", "@KaminariQpi": "神威きゅぴ",
    "@hinanotachiba7": "橘ひなの", "@八雲ぺに": "八雲ぺに", "@takachan0317": "多井隆晴", "@zunmaruch": "村上淳",
    "@SuzukiTaro_CH": "鈴木たろう", "@sibukawa": "渋川難波", "@Matsumotogumi": "松本吉弘", "@RyuseiRotan": "龍惺ろたん",
    "@tenkaitsukasa": "天開司", "@sakinomoco": "咲乃もこ", "@Izumi_Yunohara": "柚原いづみ", "@OmaruPolka": "尾丸ポルカ",
    "@TakaneLui": "鷹嶺ルイ", "@MoriCalliope": "森カリオペ", "@Inaba_Haneru": "因幡はねる"
}
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

