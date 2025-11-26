import os
import json
import base64
from datetime import datetime
from googleapiclient.discovery import build
import requests

# --- 1. 設定値 ---
# 環境変数から取得
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
GITHUB_REPO_OWNER = "keihanmatcha"
GITHUB_REPO_NAME = "oukasui"
JSON_FILE_PATH = "archives/archive_videos.json"

# 【重要】過去どこまで遡るかの設定
# 1ページあたり50件取得します。
# 100ページ設定なら、50件×100 = 5000件まで遡れます。（これなら2020年まで余裕で届きます）
# ※この新方式ならAPI消費量が少ないので、この数でも問題ありません。
MAX_PAGES_TO_FETCH = 100 

# チャンネル情報
CHANNELS = [
    {
        "id": "UCXW4MqCQn-jCaxlX-nn-BYg",
        "name": "長尾景"
        # fixed_tags がないので、自動的に「追加タグなし」として処理されます
    },
    {
        "id": "UCh-GyPNxvjTsza0ptjnkh1w",  # VΔLZ公式チャンネル
        "name": "VΔLZ",
        # このチャンネルの動画には、以下のタグを無条件で追加(append)します
        "fixed_tags": ["甲斐田晴", "弦月藤士郎", "VΔLZ"]
    }
]

# --- 2. 自動タグ付け用の辞書定義 ---
CATEGORY_list = [
    "ゲーム実況", "雑談", "歌配信", "歌動画", "踊り動画", "踊り配信",
    "記念配信", "殺陣", "お披露目配信", "3D", "企画", "大会", "ライブイベント","楽器配信"
    "プロモーション", "公式企画・番組", "動画系", "公式切り抜き",
    "手描き動画", "ぷちさんじ"
]

KEYWORD_list = [
    # --- コラボ相手 (Nijisanji & 外部 & 声優) ---
    "愛園愛美", "相羽ういは", "赤城ウェン", "赤羽葉子", "アクシア・クローネ", "朝日南アカネ", "飛鳥ひな", 
    "遠北千南", "安土桃", "天ヶ瀬むゆ", "天宮こころ", "雨森小夜", "アルス・アルマル", "アンジュ・カトリーナ", 
    "家長むぎ", "五十嵐梨花", "石神のぞみ", "出雲霞", "五木左京", "伊波ライ", "戌亥とこ", "イブラヒム", 
    "宇佐美リト", "宇志海いちご", "卯月コウ", "海妹四葉", "エクス・アルビオ", "えま★おうがすと", 
    "エリー・コニファー", "える", "御伽原江良", "小野町春香", "オリバー・エバンス", "魁星", "甲斐田晴", 
    "加賀美ハヤト","綺沙良","叶", "鏑木ろこ", "神田笑一", "北小路ヒスイ", "北見遊征", "雲母たまこ", "ギルザレンⅢ世", 
    "グウェル・オス・ガール", "葛葉", "倉持めると", "黒井しば", "来栖夏芽", "郡道美玲", "弦月藤士郎", 
    "剣持刀也", "小清水透", "小柳ロウ", "佐伯イッテツ", "早乙女ベリー", "榊ネス", "酒寄颯馬", "桜凛月", 
    "笹木咲", "椎名唯華", "シェリン・バーガンディ", "栞葉るり", "司賀りこ", "四季凪アキラ", "獅子堂あかり", 
    "静凛", "シスター・クレア", "渋谷ハジメ", "ジョー・力一", "白雪巴", "周央サンゴ", "健屋花那", "鈴鹿詩子", 
    "鈴木勝", "鈴原るる", "鈴谷アキ", "瀬戸美夜子", "セラフ・ダズルガーデン", "ソフィア・ヴァレンタイン", 
    "空星きらめ", "鷹宮リオン", "立伝都々", "珠乃井ナナ", "月ノ美兎", "でびでび・でびる", "東堂コハク", 
    "ドーラ", "轟京子", "名伽尾アズマ","渚トラウト", "七瀬すず菜", "奈羅花", "成瀬鳴", "西園チグサ", "ニュイ・ソシエール", 
    "葉加瀬冬雪", "花畑チャイカ", "早瀬走", "葉山舞鈴", "春崎エアル", "樋口楓", "一橋綾人", "緋八マナ", 
    "壱百満天原サロメ", "風楽奏斗", "伏見ガク", "フミ", "文野環", "フレン・E・ルスタリオ", "不破湊", 
    "ベルモンド・バンデラス", "星川サラ", "星導ショウ", "先斗寧", "本間ひまわり", "舞元啓介", "魔界ノりりむ", 
    "ましろ爻", "町田ちま", "魔使マオ", "黛灰", "ミラン・ケストレル", "叢雲カゲツ", "メリッサ・キンレンカ", 
    "森中花咲", "矢車りね", "社築", "山神カルタ", "勇気ちひろ", "夕陽リリ", "雪城眞尋", "夢月ロア", 
    "夢追翔", "夜見れな", "ラトナ・プティ", "リゼ・ヘルエスタ", "緑仙", "竜胆尊", "ルイス・キャミー", 
    "ルンルン", "レイン・パターソン", "レヴィ・エリファ", "レオス・ヴィンセント", "ローレン・イロアス", 
    "渡会雲雀", "童田明治", 
    # EN / ID / KR
    "Amicia Michella", "Xia-Ekavira", "Zea-Cornelia", "Taka Radjiman", 
    "Derem Kado", "Nara Haramaung", "Hana Macchia", "Mika Melatika", "Miyu Ottavia", "Layla Astroemeria", 
    "Riksa Dhirendra", "Reza Avanluna", 
    "아키라 레이（明楽 レイ）", "이로하（イ・ロハ）", "오지유（オ・ジユ）", 
    "가온（ガオン）", "신유야（シン・ユヤ）", "세피나（セフィナ）", "소나기（ソ・ナギ）", 
    "나세라（ナ・セラ）", "하윤（ハ・ユン）", "반하다（バン・ハダ）", "민수하（ミン・スゥーハ）", "양나리（ヤン・ナリ）", 
    "Ike Eveland", "Aia Amare", "Yugo Asuma", "Vezalius Bandage", "Uki Violeta", "Enna Alouette", 
    "Elira Pendora", "Endou Reimu", "Fulgur Ovid", "Kyoran Meloco", "Kaelix Debonair", "Sonny Brisko", "Selen Tatsuki", 
    "Torahime Kotoka", "Petra Gurin", "Pomu Rainpuff", "Maria Marionette", "Millie Parfait", "Shu Yamino", 
    "Luca Kaneshiro", "Ren Zotto", "星弥", "Noor", 
    # 外部・声優・その他
    "外部", "字ぴろぱる", "歌衣メイカ", "渋谷ハル", "熊谷タクマ", "かなえ先生", "天開司", 
    "浅沼晋太郎", "伊東健人", "デンジャーD", "てんぐ・横山ミル", "ヤースー", "藤川Q", "寺島惇太", "百花繚乱", 
    "ぽんぽこ", "ピーナッツくん", "ばあちゃる", "英リサ", "兎麹まり", "一ノ瀬うるは", "神威きゅぴ", 
    "橘ひなの", "八雲ぺに", "ゴモリー", "多井隆晴", "松本吉弘", "前野智昭", "土田玲央", "平川大輔", "龍惺ろたん",

    # --- コラボ・ユニット名 ---
    "VΔLZ", "エア景", "おりひめばるつ", "園児組", "年長組", "クソザコトレーナーズ", "Klime", "けいあい", 
    "southern,xxxx", "情報差分組", "女子騎士祓魔師鑑定士", "タメナンデス", "チームヘラクレス", 
    "ながおちぐ", "にじさんじダンス部", "にじさんじ放課後ゲーム部", "にじさんじベイブレード部", 
    "にじさんじポケカ部", "にじさんじロケット団", "にじさんじGTA救急隊", "にじ飯調査隊", 
    "フ景罪", "ふつまひ", "めにまにかんぱにー","えなかき",

    # --- ゲームシリーズ ---
    "アイドルマスター SideM", "あつまれどうぶつの森", "Apex Legends", "A Little to the Left",
    "ARK:Survival Ascended", "ARK:Survival Evolved", "ARK-アイランドマップ", "ARK-ラグナロクマップ", 
    "ARK-エクスティンクションマップ", "ARK-クリスタルアイルズマップ", 
    "ASTRONEER", "Blazing Sails", "Cooking Simulator", "Dead by Daylight", 
    "eFootball ウイニングイレブン", "ウマ娘　プリティダービー", "おえかきの森", 
    "Fall Guys", "Getting Over It", "Gartic Phones", "Get To Work", "Golf It!", "Fast Food Simulator",
    "Human: Fall Flat", "Left 4 Dead 2", "maimai", "Nintendo Switch Sports",
    "Operation: Tango", "Overcooked!2", "Overwatch", "Overwatch2", "Papers, Please", "PEAK",
    "Portal2", "PowerWash Simulator", "PUBG", "slither.io/wormax.io", "Stray", "BLEACH","ラブラブスクールデイズ","断罪室",
    "Ultimate Chicken Horse", "UNDERTALE", "Unrailed!", "VALORANT", 
    "ito(イト)", "エアホッケー", "オバケイドロ!", "くそいサイト", "コードネーム", "にじさんじ共通テスト","恋愛相談","Raft",
    "グランド・セフト・オートV", "クロノ・トリガー", "原神", "幻塔", "ゴッドフィールド", "7days to die","逆凸","ゆびをふる",
    "シャドウバース", "雀魂", "白猫GOLF", "スイカゲーム", "ストリートファイター6", 
    "スーパーモンキーボール バナナランブル", "やわらかあたま塾","ゴブリン・ノーム・ホーン","マイクラ肝試し","ゲームモーション研究会","同時視聴","凸待ち",
    "Splatoon", "Splatoon2", "Splatoon3","おにぎり屋さんシミュレーター","全国一般人常識チェック",
    "世界のアソビ大全51", "ゼルダの伝説 ブレス オブ ザ ワイルド", "太鼓の達人", "ツイステッドワンダーランド","逆水寒","開店コンビニ日記","牧場物語",
    "大乱闘スマッシュブラザーズSPECIAL", "テトリス99", "ダンガンロンパ", "刀剣乱舞","Detroit Become Human","大乱闘スマッシュブラザーズ",
    "ツイステッドワンダーランド", "ドキドキ文芸部", "ネコトモ", "バイオハザード ヴィレッジ", "パワフルプロ野球","ロックマンエグゼ","パワプロ","プロセカ",
    "プロジェクトセカイ カラフルステージ！ feat. 初音ミク", "ポーカーチェイス","ポケットモンスター", 
    "ポケットモンスター-金・銀", "ポケットモンスター-ユナイト", "Pokémon Trading Card Game Pocket","ポケットモンスター-ファイアレッド・リーフグリーン","ポケットモンスター-ルビー・サファイア",
    "ポケットモンスター-ブリリアントダイヤモンド・シャイニングパール", "ポケットモンスター-スカーレットバイオレット", "ポケットモンスター-ソード・シールド","Pokémon LEGENDS アルセウス",
    "マインクラフト",
    "マリオシリーズ", "スーパーマリオブラザーズ", "スーパーマリオメーカー2", 
    "マリオカート8DX", "マリオカートワールド", "マリオパーティ", "その他マリオシリーズ",
    "みんなで空気読み。", "メイド イン ワリオ", "桃太郎電鉄", "モンスターストライク", 
    "モンスターハンター：ワールド", "星のカービィシリーズ", "リズム天国", "レイトン教授と不思議な町", "一致するまで終われまテン!!",
    "任天堂", "パチスロ", "ホラーゲーム", "Chilla's Art", "PACIFY", "Poppy Playtime","Keep Talking and Nobody Explodes",
    "Protein for Muscle", "R.E.P.O.", "青鬼", "その他ホラーゲーム", "カードゲーム", "その他ゲーム","Five Nights at Freddy's","Getting Over It",

    # --- 番組・イベント ---
    "SYMPHONIA Day2", "LOCK ON FLEEK", "にじ鯖夏祭り","VTuberエンジョイカジュアル交流戦","ベース","歳の差バラエティ(?)",
    "VΔLZ1st 一唱入魂", "VΔLZ2nd 三華の樂", "にじ漢歌祭り","にじメンメドレー",
    "VTuber最協決定戦", "VTuberのあそびば", "くろのわーるがなんかやる", "Talking in English Collab", 
    "ゲームる？ゲームる！", "だいさんじ甲子園", "にじさんじ甲子園", "にじワイテ人狼RPG", 
    "格付けマリカ", "にじさんじイカ祭り", "にじさんじスマブラ杯", "にじさんじマリカ杯", "マリカにじさんじ杯","にじスプラDREAMDEATHMATCH","にじスプラ大会",
    "ミリしらスト６チャレンジ", "にじさんじイヤホンガンガンゲーム", "おながましろの心霊対談",
    "ケイナガオの楽屋裏", "Nagao's Kitchen", "初心者講座", "たい変", "にじフェス", "視聴者参加型",
    "にじさんじのTOYBOX！", "にじさんじのハッピーアワー!!", "にじさんじのB級バラエティ(仮)", "桜魔大戦譚","にじさんじ大運動会",
    "にじさんじMIX UP!!", "にじさんじユニット歌謡祭2022", "にじさんじ歌謡祭2024", "にじマイクラ占領戦","全肯定長尾景",
    "にじクイ", "木10！ろふまお塾", "ヤシロ&ササキのレバガチャダイパン"
]

TAG_CONVERSION_MAP = {
    "マイクラ": "マインクラフト",
    ["マリカ","マリオカート8デラックス"]: "マリオカート8DX",   
    ["スプラ","スプラトゥーン"]: "Splatoon",
    ["スプラ2","スプラトゥーン2"]: "Splatoon2",
    ["スプラ3","スプラトゥーン3"]: "Splatoon3",
    "あつ森":"あつまれどうぶつの森",
    "サイスタ":"アイドルマスター SideM GROWING STARS",
    "大乱闘スマッシュブラザーズSP",:"大乱闘スマッシュブラザーズSPECIAL",
    "ツイステ":"ツイステッドワンダーランド",
    "デトロイト":"Detroit Become Human",
    "剣盾":"ポケットモンスター-ソード・シールド",
    "L4D2":"Left 4 Dead 2",
    "スト6":"ストリートファイター6",
    ["Apex","APEX","エペ"]:"Apex Legends",
    "ポケカ":"Pokémon Trading Card Game Pocket",
    "パワプロ":"パワプロ野球",
    "プロセカ":"プロジェクトセカイ カラフルステージ！ feat. 初音ミク",
    "ヒューマンフォールフラット":"Human: Fall Flat",
    "ながおげん":"園児組",
    "ましろ":"ましろ爻",
    "えある":"春崎エアル",
    "エアル":"春崎エアル",
    "歌枠":"歌配信",
    "歌ってみた":"歌動画",
    "踊ってみた":"踊り動画",
    "ダンス動画":"踊り動画",
    "ダンス配信":"踊り配信",
    "ベース練習":"楽器配信",
    "弾いて":"楽器配信",
    "弾ける":"楽器配信",
    "タメジャナインデス":"タメナンデス",
    "めにまに":"めにまにカンパニー",
    "めにまにかんぱにー":"めにまにカンパニー",
    "OW":"Overwatch",
    "OW2":"Overwatch2",
    "ウマ娘":"ウマ娘　プリティダービー",
    "ポケモン銀":"ポケットモンスター-金・銀",
    "ポケモン金":"ポケットモンスター-金・銀",
    "ポケモンユナイト":"ポケットモンスター-金・銀",
    "ポケモンSV":"ポケットモンスター-ユナイト",
    "ポケモンサファイア":"ポケットモンスター-ルビー・サファイア",
    "ポケモンFRLG":"ポケットモンスター-ファイアレッド・リーフグリーン",
    "ポケモンBDSP":"ポケットモンスター-ブリリアントダイヤモンド・シャイニングパール"
}
# ★ユニット・メンバー定義: "ユニット名": ["メンバーA", "メンバーB", ...]
UNIT_GROUP_MAP = {
    "VΔLZ": ["甲斐田晴", "弦月藤士郎"],
    "フ景罪": ["フミ"],
    "タメナンデス": ["オリバー・エバンス"],
    "エア景": ["春崎エアル"],
    "えなかき": ["える","綺沙良"],
    "園児組": ["弦月藤士郎"],
    "年長組": ["甲斐田晴"],
    "けいあい": ["相羽ういは"],
    "Klime": ["甲斐田晴", "弦月藤士郎"],
    "組体操": ["渋谷ハジメ", "夕陽リリ"],
    "クソザコトレーナーズ": ["春崎エアル","グウェル・オス・ガール","グウェル・オス・ガール","소나기（ソ・ナギ）"],
    "ケイトララ": ["渚トラウト"],
    "Klime": ["山神カルタ", "東堂コハク"],
    "情報差分組": ["赤城ウェン","星導ショウ","榊ネス"],
    "女子騎士祓魔師鑑定士": ["フレン・E・ルスタリオ","先斗寧","星導ショウ"],
    "スプラ四天王": ["笹木咲","春崎エアル","不破湊"],
    "ふつまひ": ["雪城眞尋"],
    "ながおちぐ": ["西園チグサ"],
    "にじさんじON砲": ["小野町春香"],
    "にじさんじダンス部": ["山神カルタ","東堂コハク","レイン・パターソン","セラフ・ダズルガーデン","倉持めると"],
    "長尾ーズ": ["三枝明那","黛灰","不破湊"],
    "てっぺん": ["本間ひまわり","鷹宮リオン","来栖夏芽"],
    "チームABC": ["える","雪城眞尋"],
    "『絶え間なく突撃』": ["奈羅花","渡会雲雀","榊ネス"],
    "にじさんじポケカ部": ["花畑チャイカ","舞元啓介","葉加瀬冬雪","加賀美ハヤト","倉持めると","赤城ウェン","栞葉るり","榊ネス"],
    "にじさんじラジオ体操部": ["月ノ美兎","勇気ちひろ","える","樋口楓","渋谷ハジメ", "伏見ガク", "ギルザレンIII世", "剣持刀也","叶","笹木咲",
                    "椎名唯華","ドーラ", "轟京子", "シスター・クレア", "花畑チャイカ", "社築","鈴木勝", "緑仙", "鷹宮リオン", "舞元啓介", "でびでび・でびる", "桜凛月",
                    "町田ちま", "ジョー・力一", "ベルモンド・バンデラス", "矢車りね", "黒井しば", "童田明治", "小野町春香", "戌亥とこ", "三枝明那",
                    "雪城眞尋", "レヴィ・エリファ", "葉加瀬冬雪", "加賀美ハヤト", "夜見れな", "黛灰", "アルス・アルマル", "相羽ういは", "天宮こころ",
                    "エリー・コニファー", "ラトナ・プティ", "早瀬走", "健屋花那", "フミ", "星川サラ", "えま★おうがすと", "ルイス・キャミー",
                    "不破湊", "白雪巴", "グウェル・オス・ガール", "ましろ爻", "奈羅花", "来栖夏芽", "フレン・E・ルスタリオ", "メリッサ・キンレンカ",
                    "イブラヒム","弦月藤士郎", "甲斐田晴", "北小路ヒスイ", "西園チグサ", "アクシア・クローネ", "ローレン・イロアス",
                    "レオス・ヴィンセント", "オリバー・エバンス", "レイン・パターソン", "海妹四葉", "壱百満天原サロメ", "風楽奏斗", "渡会雲雀",
                    "四季凪アキラ", "セラフ・ダズルガーデン", "Taka Radjiman", "Zea-Cornelia", "Riksa Dhirendra", "Nara Haramaung",
                    "Layla Alstroemeria", "Bonnivier Pranaja", "Derem Kado", "Xia-Ekavira", "Mika Melatika","소나기（ソ・ナギ）",
                    "양나리（ヤン・ナリ）","하윤（ハ・ユン）","오지유（オ・ジユ）","세피나（セフィナ）","나세라（ナ・セラ）",
                    "小清水透", "獅子堂あかり", "鏑木ろこ", "五十嵐梨花", "石神のぞみ",
                    "ソフィア・ヴァレンタイン", "倉持めると", "佐伯イッテツ", "赤城ウェン", "宇佐美リト","緋八マナ", "星導ショウ",
                    "叢雲カゲツ", "小柳ロウ", "伊波ライ", "Elira Pendora", "Pomu Rainpuff", "Petra Gurin", "Enna Alouette",
                    "Reimu Endou", "Millie Parfait", "Luca Kaneshiro", "Shu Yamino", "Yugo Asuma", "Sonny Brisko", "Uki Violeta",
                    "Aia Amare", "あばだんご"],
    "バベルの景": ["オリバー・エバンス","ベルモンド・バンデラス"],
    "めにまにカンパニー": ["桜凛月","Nara Haramaung","세피나（セフィナ）"],
    "忖度フィニッシャーズ": ["える","愛園愛美"],
    "にじGTA救急隊": ["樋口楓","森中花咲","桜凛月","成瀬鳴","小野町春香","三枝明那","健屋花那","グウェル・オス・ガール","弦月藤士郎",
                 "甲斐田晴","민수하（ミン・スゥーハ）", "오지유（オ・ジユ）", "세피나（セフィナ）", "宇佐美リト", "魁星", "Maria Marionette", "Vezalius Bandage"],
}

# --- 3. タグ判定関数 ---
def analyze_video_tags(title, fixed_tags):
    """タイトルからカテゴリとキーワードを自動判定する"""
    detected_category = "未分類"
    detected_keywords = []

    # 検索用にタイトルを小文字化
    title_lower = str(title).lower()
    
    # 1. カテゴリ判定
    for cat in CATEGORY_list:
        if cat in title:
            detected_category = cat
            break 
    
    # 2. キーワード判定 (タイトルに含まれるものを検出)
    for keyword in KEYWORD_list:
        if keyword.lower() in title_lower:
            if keyword not in detected_keywords:
                detected_keywords.append(keyword)

    # 3. チャンネル固有の固定タグを追加 (タイトルになくてもappend)
    if fixed_tags:
        for tag in fixed_tags:
            if tag not in detected_keywords:
                detected_keywords.append(tag)
            
    return detected_category, detected_keywords

# --- 3. タグ判定関数 ---
def analyze_video_tags(title, fixed_tags):
    """タイトルからカテゴリとキーワードを自動判定する"""
    detected_category = "未分類"
    detected_keywords = []

    # 検索用にタイトルを小文字化
    title_lower = str(title).lower()
    
    # 1. カテゴリ判定
    for cat in CATEGORY_list:
        if cat in title:
            detected_category = cat
            break 
    
    # 2. キーワード判定 (タイトルに含まれるものを検出)
    for keyword in KEYWORD_list:
        if keyword.lower() in title_lower:
            if keyword not in detected_keywords:
                detected_keywords.append(keyword)

    # ---------------------------------------------------------
    # 表記ゆれ・略称から正式タグを追加する処理
    # ---------------------------------------------------------
    for slang, formal_tag in TAG_CONVERSION_MAP.items():
        # タイトルに略称(マイクラ等)が含まれているか？
        if slang in title_lower:
            # 正式名称(マインクラフト等)がまだタグになければ追加
            if formal_tag not in detected_keywords:
                detected_keywords.append(formal_tag)
    # ---------------------------------------------------------

    # 3. チャンネル固有の固定タグを追加 (タイトルになくてもappend)
    if fixed_tags:
        for tag in fixed_tags:
            if tag not in detected_keywords:
                detected_keywords.append(tag)
            
    return detected_category, detected_keywords
def analyze_video_tags(title, fixed_tags):
    # ... (これまでの処理: カテゴリ判定、キーワード判定、表記ゆれ変換) ...
    
    # ---------------------------------------------------------
    # ★追加部分: ユニットとメンバーの相互補完
    # ---------------------------------------------------------
    for unit_name, members in UNIT_GROUP_MAP.items():
        
        # 【パターン1】ユニット名があるのに、メンバーが入っていない場合 → メンバーを追加
        if unit_name in detected_keywords:
            for member in members:
                if member not in detected_keywords:
                    detected_keywords.append(member)

        # 【パターン2】メンバーが全員揃っているのに、ユニット名がない場合 → ユニット名を追加
        #  (全員揃っているかチェック)
        has_all_members = all(member in detected_keywords for member in members)
        if has_all_members:
            if unit_name not in detected_keywords:
                detected_keywords.append(unit_name)
    # ---------------------------------------------------------

    # 3. チャンネル固有の固定タグを追加 (タイトルになくてもappend)
    if fixed_tags:
        for tag in fixed_tags:
            if tag not in detected_keywords:
                detected_keywords.append(tag)
            
    return detected_category, detected_keywords

# --- 4. YouTube APIから動画を取得（新方式：PlaylistItems使用） ---
# チャンネルIDから「アップロード済み動画リスト」のIDを取得する関数
def get_uploads_playlist_id(youtube, channel_id):
    try:
        resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
        return resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"❌ Error getting playlist ID for {channel_id}: {e}")
        return None

# 指定されたプレイリストから全動画を取得する関数
def fetch_videos_from_playlist(youtube, playlist_id, channel_name, fixed_tags):
    videos = []
    next_page_token = None
    page_count = 0
    
    # MAX_PAGES_TO_FETCH ページ分だけ繰り返し取得
    while page_count < MAX_PAGES_TO_FETCH:
        try:
            request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                break

            for item in items:
                snippet = item['snippet']
                # 公開日時 (例: 2020-01-01T00:00:00Z)
                published_at = snippet.get('publishedAt')
                if not published_at: continue
                
                # 日付のみ抽出
                dt = datetime.strptime(published_at[:10], '%Y-%m-%d')
                published_date = dt.strftime('%Y-%m-%d')
                
                video_id = item['contentDetails']['videoId']
                video_title = snippet['title']
                
                # 自動タグ判定
                category, keywords = analyze_video_tags(video_title, fixed_tags)
                
                videos.append({
                    "youtubeId": video_id,
                    "title": video_title,
                    "channel": channel_name,
                    "date": published_date,
                    "thumbnail": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                    "category": category,
                    "keywords": keywords,
                    "songs": []
                })

            next_page_token = response.get('nextPageToken')
            page_count += 1
            print(f"   Running... {channel_name}: {len(videos)} 件取得中 (Page {page_count}/{MAX_PAGES_TO_FETCH})")
            
            if not next_page_token:
                break
                
        except Exception as e:
            print(f"❌ Error fetching playlist items: {e}")
            break
            
    print(f"ℹ️ {channel_name}: 合計 {len(videos)} 件取得成功")
    return videos


# --- 5. GitHub更新処理 ---
def update_github_json(new_videos):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    contents_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{JSON_FILE_PATH}"
    
    # GET: 既存ファイルの取得
    response = requests.get(contents_url, headers=headers)

    if response.status_code == 200:
        content_info = response.json()
        existing_content = content_info['content']
        existing_sha = content_info['sha']
        try:
            decoded_content = base64.b64decode(existing_content).decode('utf-8')
            existing_videos = json.loads(decoded_content)
        except:
            existing_videos = []
    else:
        existing_videos = []
        existing_sha = None

    existing_ids = {v['youtubeId'] for v in existing_videos}
    merged_videos = existing_videos.copy()
    
    added_count = 0
    for new_video in new_videos:
        if new_video['youtubeId'] not in existing_ids:
            merged_videos.append(new_video)
            added_count += 1
            # 数が多いのでログ出力を抑制
            # print(f"🆕 追加: {new_video['title']}")
    
    if added_count == 0:
        print("✅ 新しい動画はありませんでした。")
        return

    print(f"📦 合計 {added_count} 件の新しい動画をマージしました。")

    # 日付順にソート
    merged_videos.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    # JSON生成とエンコード
    new_content_bytes = json.dumps(merged_videos, indent=2, ensure_ascii=False).encode('utf-8')
    new_content_base64 = base64.b64encode(new_content_bytes).decode('utf-8')

    # PUT: 更新コミット
    commit_data = {
        "message": f"ARCHIVE_BOT: {added_count} 件追加 (全件取得モード)",
        "content": new_content_base64
    }
    if existing_sha:
        commit_data["sha"] = existing_sha
    
    put_res = requests.put(contents_url, headers=headers, json=commit_data)
    
    if put_res.status_code in [200, 201]:
        print(f"🚀 GitHubコミット完了: {added_count}件追加しました！")
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
    all_new_videos = []

    for ch in CHANNELS:
        # 1. チャンネルIDからアップロードリストIDを取得
        playlist_id = get_uploads_playlist_id(youtube, ch['id'])
        if not playlist_id:
            continue
            
        # 2. プレイリストから全動画を取得
        fixed_tags = ch.get('fixed_tags', [])
        videos = fetch_videos_from_playlist(youtube, playlist_id, ch['name'], fixed_tags)
        all_new_videos.extend(videos)
    
    if all_new_videos:
        update_github_json(all_new_videos)
    else:
        print("⚠️ 動画が1件も取得できませんでした。APIキーなどを確認してください。")

if __name__ == "__main__":
    main()











