import os
import json
import base64
import re
from datetime import datetime
from googleapiclient.discovery import build
import requests
import sys

# --- 1. 設定値 ---
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

EXTRA_PLAYLISTS = [
    {
        "id": "PLBp6ycTto5GroVAk6Kudsq5kNTfG7KS7v", 
        "name": "長尾景",
        "fixed_tags": ["歌動画"],
        "auto_tags": ["カバー(ソロ)", "歌"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GoI2_p5mt4VTGxVo742O39L", 
        "name": "長尾景",
        "fixed_tags": ["歌動画"],
        "auto_tags": ["カバー(ユニット)", "歌"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GpzqP1210T592tJNBGIbr9s", 
        "name": "長尾景",
        "fixed_tags": ["踊り動画"],
        "auto_tags": ["カバー(ソロ)", "踊"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GqXxtXMZysbZsZKWF15a7vm", 
        "name": "長尾景",
        "fixed_tags": ["踊り動画"],
        "auto_tags": ["カバー(ユニット)", "踊"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5Gr_8_WWkrkFi4VIn3MBM16e", 
        "name": "長尾景",
        "fixed_tags": ["歌動画"],
        "auto_tags": ["オリジナル（ソロ）", "歌"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GpSNOHZ2F-YG4zuOt2yQuTj", 
        "name": "長尾景",
        "fixed_tags": ["歌動画"],
        "auto_tags": ["オリジナル(ユニット)", "歌"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5Go5-ydU7-dkjGQQL4aRBhr9", 
        "name": "長尾景",
        "fixed_tags": ["踊り動画"],
        "auto_tags": ["オリジナル（ソロ）", "踊"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GpJ_zxs62-ytfQHS6GLDhaV", 
        "name": "長尾景",
        "fixed_tags": ["踊り動画"],
        "auto_tags": ["オリジナル(ユニット)", "踊"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GpDE572kCo-irPWjNgP6IG_", 
        "name": "長尾景",
        "fixed_tags": ["楽器配信・動画"],
        "auto_tags": ["オリジナル（ソロ）", "弾"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GozfE8ryy4knBGP3rOTsIhJ", 
        "name": "長尾景",
        "fixed_tags": ["楽器配信・動画"],
        "auto_tags": ["オリジナル(ユニット)", "弾"]  # archive_videos.jsonの tags に入る値
    },
    {
        "id": "PLBp6ycTto5GqM3GtJP5uMwoCVmcvK0WiX",
        "name": "長尾景",
        "fixed_tags": ["ぷちさんじ"]
    },
    {
        "id": "PLBp6ycTto5GqBQLRFl4eikLuVCPLjdhFJ",
        "name": "長尾景",
        "fixed_tags": ["雑談"]
    },
    {
        "id": "PLBp6ycTto5GozlebGn5bM3xwAO73H9E03",
        "name": "長尾景",
        "fixed_tags": ["歌配信"]
    },
    {
        "id": "PLBp6ycTto5GpfRvDNSYGGl5YRrGBRY0wA",
        "name": "長尾景",
        "fixed_tags": ["企画"]
    },
    {
        "id": "PLBp6ycTto5GoNTkdug6HJm8z5dI9QnbIB",
        "name": "長尾景",
        "fixed_tags": ["楽器配信・動画"]
    },
    {
        "id": "PLBp6ycTto5GrRHriPoiX239ff9UgVGCWe",
        "name": "長尾景",
        "fixed_tags": ["お披露目配信"]
    },
    {
        "id": "PLBp6ycTto5Gql76h6O3snsP4JQQWa6IA_",
        "name": "長尾景",
        "fixed_tags": ["プロモーション"]
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

# 【追加】タイトルに含まれていたら強制的にカテゴリに追加するマッピング
FORCE_CATEGORY_MAP = {
    "踊ってみた": "踊り動画",
    "歌ってみた": "歌動画",
    "楽曲": "歌動画",
    "3D": "3D",
    "XFDムービー":"プロモーション",
    "特典":"プロモーション",
    "Cover": "歌動画",
    "踊ってみた": "踊り動画",
    "踊って": "踊り動画",
    "感想配信": "記念配信",
    "告知": "プロモーション",
    "ティーザー": "プロモーション",
    "ダンス動画": "踊り動画",
    "ダンス配信": "踊り配信",
    "ベース練習": "楽器配信・動画",
    "弾いて": "楽器配信・動画",
    "弾ける": "楽器配信・動画",
    "歌枠": "歌配信",
    "歌って": "歌動画",
    "歌ってみた": "歌動画",
    "COVER": "歌動画",
    "LIVE": "ライブイベント",
    "ライブ": "ライブイベント",
    "殺陣": "殺陣",
    "お披露目": "お披露目配信"
}

KEYWORD_GROUPS = {
    "MEMBERS": [
        "愛園愛美", "相羽ういは", "赤城ウェン", "赤羽葉子", "アクシア・クローネ", "朝日南アカネ", "飛鳥ひな", "遠北千南", "長尾姉上",
        "安土桃", "天ヶ瀬むゆ", "天宮こころ", "雨森小夜", "アルス・アルマル", "アンジュ・カトリーナ", "家長むぎ", "五十嵐梨花",
        "石神のぞみ", "出雲霞", "五木左京", "伊波ライ", "戌亥とこ", "イブラヒム", "宇佐美リト", "宇志海いちご", "卯月コウ",
        "海妹四葉", "エクス・アルビオ", "えま★おうがすと", "エリー・コニファー", "御伽原江良", "小野町春香", "オリバー・エバンス",
        "魁星", "甲斐田晴", "加賀美ハヤト", "蝸堂みかる", "綺沙良", "鏑木ろこ", "神田笑一", "北小路ヒスイ", "北見遊征", "雲母たまこ",
        "ギルザレンⅢ世", "グウェル・オス・ガール", "葛葉", "倉持めると", "黒井しば", "来栖夏芽", "郡道美玲", "弦月藤士郎", "剣持刀也",
        "梢桃音", "小清水透", "小柳ロウ", "佐伯イッテツ", "早乙女ベリー", "榊ネス", "酒寄颯馬", "桜凛月", "笹木咲", "椎名唯華", "シェリン・バーガンディ",
        "栞葉るり", "司賀りこ", "四季凪アキラ", "獅子堂あかり", "静凛", "シスター・クレア", "渋谷ハジメ", "篠宮ゆの", "城瀬いすみ", "ジョー・力一","鈴原るる",
        "白雪巴", "周央サンゴ", "健屋花那", "鈴鹿詩子", "皇れお", "鈴木勝", "鈴原るる", "鈴谷アキ", "瀬戸美夜子", "セラフ・ダズルガーデン",
        "ソフィア・ヴァレンタイン", "空星きらめ", "鷹宮リオン", "立伝都々", "珠乃井ナナ", "月ノ美兎", "でびでび・でびる", "東堂コハク",
        "十河ののは", "ドーラ", "轟京子", "名伽尾アズマ", "渚トラウト", "七瀬すず菜", "奈羅花", "成瀬鳴", "西園チグサ", "ニュイ・ソシエール",
        "猫屋敷美紅", "葉加瀬冬雪", "花畑チャイカ", "早瀬走", "葉山舞鈴", "春崎エアル", "花籠つばさ", "樋口楓", "一橋綾人", "緋八マナ",
        "壱百満天原サロメ", "風楽奏斗", "伏見ガク", "フミ", "文野環", "フレン・E・ルスタリオ", "不破湊", "ベルモンド・バンデラス",
        "星川サラ", "星導ショウ", "先斗寧", "本間ひまわり", "舞元啓介", "魔界ノりりむ", "ましろ爻", "町田ちま", "魔使マオ", "黛灰",
        "ミラン・ケストレル", "叢雲カゲツ", "メリッサ・キンレンカ", "森中花咲", "矢車りね", "夜牛詩乃", "社築", "山神カルタ", "勇気ちひろ",
        "夕陽リリ", "雪城眞尋", "夢月ロア", "夢追翔", "夜見れな", "ラトナ・プティ", "リゼ・ヘルエスタ", "緑仙", "竜胆尊", "ルイス・キャミー",
        "ルンルン", "レイン・パターソン", "レヴィ・エリファ", "レオス・ヴィンセント", "ローレン・イロアス", "渡会雲雀", "童田明治",
        # EN / ID / KR
        "Amicia Michella", "Xia-Ekavira", "Zea-Cornelia", "Taka Radjiman", "Derem Kado", "Nara Haramaung", "Hana Macchia",
        "Mika Melatika", "Miyu Ottavia", "Layla Astroemeria", "Riksa Dhirendra", "Reza Avanluna", "아키라 레이（明楽 レイ）",
        "이로하（イ・ロハ）", "오지유（オ・ジユ）", "가온（ガオン）", "신유야（シン・ユヤ）", "세피나（セフィナ）", "소나기（ソ・ナギ）",
        "나세라（ナ・セラ）", "하윤（ハ・ユン）", "반하다（バン・ハダ）", "민수하（ミン・スゥーハ）", "양나리（ヤン・ナリ）", "Ike Eveland",
        "Aia Amare", "Yugo Asuma", "Vezalius Bandage", "Uki Violeta", "Enna Alouette", "Elira Pendora", "Endou Reimu", "Fulgur Ovid",
        "Kyoran Meloco", "Kaelix Debonair", "Sonny Brisko", "Selen Tatsuki", "Torahime Kotoka", "Petra Gurin", "Pomu Rainpuff",
        "Maria Marionette", "Millie Parfait", "Shu Yamino", "Luca Kaneshiro", "Ren Zotto", "星弥", "Noor","ChroNoiR",
        # 外部・声優・その他
        "字ぴろぱる", "歌衣メイカ", "渋谷ハル", "熊谷タクマ", "かなえ先生", "天開司", "浅沼晋太郎", "伊東健人", "デンジャーD","こばやん",
        "てんぐ・横山ミル", "ヤースー", "藤川Q", "寺島惇太", "百花繚乱", "ぽんぽこ", "ピーナッツくん", "ばあちゃる", "英リサ",
        "兎麹まり", "一ノ瀬うるは", "神威きゅぴ", "橘ひなの", "八雲ぺに", "ゴモリー", "多井隆晴", "松本吉弘", "前野智昭", "土田玲央",
        "平川大輔", "龍惺ろたん"
    ],
    "UNITS": [
        "VΔLZ", "エア景", "おりひめばるつ", "園児組", "年長組", "クソザコトレーナーズ", "Klime", "けいあい",
        "Southern,xxxx", "情報差分組", "女子騎士祓魔師鑑定士", "タメナンデス", "チームヘラクレス",
        "ながおちぐ", "にじさんじダンス部", "にじさんじ放課後ゲーム部", "にじさんじベイブレード部",
        "にじさんじポケカ部", "にじさんじロケット団", "にじさんじGTA救急隊", "にじ飯調査隊",
        "SitR名古屋", "フ景罪", "ふつまひ", "めにまにかんぱにー", "えなかき"
    ],
    "GAMES": [
        "アイドルマスター SideM", "あつまれどうぶつの森", "Apex Legends", "A Little to the Left", "BUCK SHOT ROULETTE", "ARK",
        "ARK:Survival Ascended", "ARK:Survival Evolved", "ARK-アイランドマップ", "ARK-ラグナロクマップ", "ときめきメモリアル", "AmongUs",
        "ARK-エクスティンクションマップ", "ARK-クリスタルアイルズマップ", "ASTRONEER", "Blazing Sails", "ドラえもんのどら焼き屋さん物語","ダレカレ",
        "Cooking Simulator", "Dead by Daylight", "eFootball ウイニングイレブン", "ウマ娘　プリティダービー","UMIGARI | ウミガリ","Ring Fit Adventure",
        "おえかきの森", "Fall Guys", "Getting Over It", "Gartic Phones", "Get To Work", "Golf It!", "Inverted Angel",
        "Fast Food Simulator", "Human: Fall Flat", "Left 4 Dead 2", "maimai", "Nintendo Switch Sports", "PADDLE PADDLE PADDLE",
        "Operation: Tango", "Overcooked!2", "Overwatch", "Overwatch2", "Papers, Please", "PEAK", "Portal2","一致するまで終われまテン!!",
        "PowerWash Simulator", "PUBG", "slither.io/wormax.io", "Stray", "BLEACH", "ラブラブスクールデイズ", "Unpacking",
        "断罪室", "Ultimate Chicken Horse", "UNDERTALE", "Unrailed!", "GeoGuessr", "ito(イト)", "エアホッケー","TRPG",
        "オバケイドロ!", "くそいサイト", "コードネーム", "にじさんじ共通テスト", "恋愛相談", "Raft", "遊戯王", "閉店事件",
        "グランド・セフト・オートV", "クロノ・トリガー", "原神", "幻塔", "ゴッドフィールド", "7days to die",
        "逆凸", "ゆびをふる", "シャドウバース", "雀魂", "白猫GOLF", "スイカゲーム", "ストリートファイター6",
        "スーパーモンキーボール バナナランブル", "やわらかあたま塾", "ゴブリン・ノーム・ホーン", "カービィのエアライダー",
        "マイクラ肝試し", "ゲームモーション研究会", "同時視聴", "凸待ち", "Splatoon", "Splatoon2", "Splatoon3", "ワンス・アポン・ア・塊魂",
        "おにぎり屋さんシミュレーター", "全国一般人常識チェック", "世界のアソビ大全51", "VALORANT", "Untitled Goose Game",
        "ゼルダの伝説 ブレス オブ ザ ワイルド", "太鼓の達人", "ツイステッドワンダーランド", "逆水寒", "夜間警備", "PotionPermit",
        "開店コンビニ日記", "牧場物語", "大乱闘スマッシュブラザーズSPECIAL", "テトリス99", "ダンガンロンパ", "Amanda the Adventurer",
        "刀剣乱舞", "Detroit Become Human", "大乱闘スマッシュブラザーズ", "ツイステッドワンダーランド", "塊塊アンコール",
        "ドキドキ文芸部", "ネコトモ", "バイオハザード ヴィレッジ", "パワフルプロ野球", "ロックマンエグゼ", "Q REMASTERED",
        "パワプロ", "プロセカ", "プロジェクトセカイ カラフルステージ！ feat. 初音ミク", "ポーカーチェイス", "Gang Beasts","CONTENT WARNING",
        "ポケットモンスター", "ポケットモンスター-金・銀", "ポケットモンスター-ユナイト", "GTA", "There Is No Game", "FOOD DELIVERY SERVICE",
        "Pokémon Trading Card Game Pocket", "ポケットモンスター-ファイアレッド・リーフグリーン", "大乱闘スマッシュブラザーズ",
        "ポケットモンスター-ルビー・サファイア", "ポケットモンスター-ブリリアントダイヤモンド・シャイニングパール", "BIOHAZARD VILLAGE","何かが潜んでいる",
        "ポケットモンスター-スカーレットバイオレット", "ポケットモンスター-ソード・シールド", "ポケットモンスター-ぽこ あ ポケモン","アリーナ・オブ・ヴァラー", "BATTLEFIELD V",
        "Pokémon LEGENDS アルセウス", "マインクラフト", "マリオシリーズ", "スーパーマリオブラザーズ", "深夜放送", "キーボードパズル",
        "スーパーマリオメーカー2", "マリオカート8DX", "マリオカートワールド", "マリオパーティ", "漢字でGO!", "PC Building Simulator",
        "その他マリオシリーズ", "みんなで空気読み。", "メイド イン ワリオ", "桃太郎電鉄", "モンスターストライク", "つぐのひ　忌み夜の喰霊品店",
        "モンスターハンター：ワールド", "星のカービィシリーズ", "リズム天国", "レイトン教授と不思議な町", "崩壊：スターレイル", "Knockout City",
        "一致するまで終われまテン!!", "任天堂", "パチスロ", "ホラーゲーム", "Chilla's Art", "PACIFY", "Twelve Minutes", "トロッコ問題",
        "Poppy Playtime", "Keep Talking and Nobody Explodes", "Protein for Muscle", "R.E.P.O.", "青鬼", "RTA", "例外配達",
        "その他ホラーゲーム", "カードゲーム", "その他ゲーム", "Five Nights at Freddy's", "Getting Over It", "V最協", "V祭協"
    ],
    "PROGRAMS": [
        "SYMPHONIA Day2", "LOCK ON FLEEK", "にじ鯖夏祭り", "VTuberエンジョイカジュアル交流戦",
        "ベース", "歳の差バラエティ(?)", "VΔLZ1st 一唱入魂", "VΔLZ2nd 三華の樂", "にじ漢歌祭り","にじベイブレード",
        "にじメンメドレー", "VTuber最協決定戦", "V祭協", "VTuberのあそびば", "くろのわーるがなんかやる",
        "Talking in English Collab", "ゲームる？ゲームる！", "だいさんじ甲子園", "にじさんじ甲子園",
        "にじワイテ人狼RPG", "格付けマリカ", "にじさんじイカ祭り", "にじさんじスマブラ杯", "神域甲子園", "ながおちぐ甲子園",
        "マリカにじさんじ杯", "にじスプラDREAMDEATHMATCH", "にじスプラ大会", "ミリしらスト６チャレンジ", "FIFA",
        "にじさんじイヤホンガンガンゲーム", "おながましろの心霊対談", "ケイナガオの楽屋裏", "NIJIMelodyTime",
        "Nagao's Kitchen", "初心者講座", "たい変", "にじフェス", "視聴者参加型", "にじさんじ麻雀杯",
        "にじさんじのTOYBOX！", "にじさんじのハッピーアワー!!", "にじさんじのB級バラエティ(仮)",
        "桜魔大戦譚", "にじさんじ大運動会", "にじさんじMIX UP!!", "にじさんじユニット歌謡祭2022", "目隠しポケモン","にじポケ1on1","にじエペさい",
        "にじさんじ歌謡祭2024", "にじマイクラ占領戦", "全肯定長尾景", "にじクイ", "木10！ろふまお塾", "KZHCUP", "にじさんじVALORANTカスタム",
        "ヤシロ&ササキのレバガチャダイパン", "レバガチャダイパン杯", "にじプロセカ大会", "カラフェス", "にじエペ祭", "神域リーグ", "にじさんじ遊戯王マスターデュエル"
    ]
}

TAG_CONVERSION_MAP = {
    "何かが潜んでいる":"TRPG",
    "マイクラ": "マインクラフト",
    "マリカ": "マリオカート8DX",
    "マリオカート8デラックス": "マリオカート8DX",
    "にじばろカスタム": "にじさんじVALORANTカスタム",
    "スプラ": "Splatoon",
    "Golf it": "Golf It!",
    "モンハンワイルズ": "モンスターハンターワイルズ",
    "スプラトゥーン": "Splatoon",
    "Pokemon LEGENDS アルセウス": "Pokémon LEGENDS アルセウス",
    "バイオハザードヴィレッジ": "BIOHAZARD VILLAGE",
    "スプラ2": "Splatoon2",
    "フードデリバリーサービス": "FOOD DELIVERY SERVICE",
    "VAROLANT": "VALORANT",
    "アリヴァラ": "アリーナ・オブ・ヴァラー",
    "スプラトゥーン2": "Splatoon2",
    "桃鉄": "桃太郎電鉄",
    "空気読み": "みんなで空気読み。",
    "アモアス": "AmongUs",
    "スプラ3": "Splatoon3",
    "スプラトゥーン3": "Splatoon3",
    "テトリス": "テトリス99",
    "切り抜き": "公式切り抜き",
    "リングフィットアドベンチャー": "Ring Fit Adventure",
    "お絵描きの森": "おえかきの森",
    "ライブ": "ライブ・イベント",
    "姉": "長尾姉上",
    "KZH CUP": "KZZCUP",
    "SONG": "歌動画",
    "とうらぶ": "刀剣乱舞",
    "にじGTA": "にじさんじGTA",
    "楽曲": "歌動画",
    "Speaking English Practice": "Talking in English Collab",
    "にじスプラDREAM DEATHMATCH": "にじスプラDREAMDEATHMATCH",
    "V最協": "VTuber最協決定戦",
    "レバガチャ運動会": "レバガチャダイパン杯",
    "にじマイクラ占領戦": "にじマイクラ聖地占領戦",
    "あつ森": "あつまれどうぶつの森",
    "どうぶつの森": "あつまれどうぶつの森",
    "サイスタ": "アイドルマスター SideM GROWING STARS",
    "大乱闘スマッシュブラザーズSP": "大乱闘スマッシュブラザーズSPECIAL",
    "スマブラ": "大乱闘スマッシュブラザーズ",
    "ツイステ": "ツイステッドワンダーランド",
    "デトロイト": "Detroit Become Human",
    "剣盾": "ポケットモンスター-ソード・シールド",
    "ぽこ あ ポケモン":"ポケットモンスター-ぽこ あ ポケモン",
    "L4D2": "Left 4 Dead 2",
    "スト6": "ストリートファイター6",
    "ザンギ": "ストリートファイター6",
    "Power Wash Simulator": "PowerWash Simulator",
    "Apex": "Apex Legends",
    "APEX": "Apex Legends",
    "エペ": "Apex Legends",
    "ポケポケ": "Pokémon Trading Card Game Pocket",
    "にじイカ祭り": "にじさんじイカ祭り",
    "歌枠": "歌配信",
    "歌って": "歌動画",
    "歌ってみた": "歌動画",
    "COVER": "歌動画",
    "談義": "対談",
    "XFDムービー":"プロモーション",
    "特典":"プロモーション",
    "Cover": "歌動画",
    "踊ってみた": "踊り動画",
    "踊って": "踊り動画",
    "感想配信": "記念配信",
    "告知": "プロモーション",
    "ティーザー": "プロモーション",
    "ダンス動画": "踊り動画",
    "ダンス配信": "踊り配信",
    "ベース練習": "楽器配信・動画",
    "弾いて": "楽器配信・動画",
    "弾ける": "楽器配信・動画",
    "ポケカ": "Pokémon Trading Card Game Pocket",
    "パワプロ": "パワフルプロ野球",
    "にじさんじマリカ杯": "マリカにじさんじ杯",
    "プロセカ": "プロジェクトセカイ カラフルステージ！ feat. 初音ミク",
    "ヒューマンフォールフラット": "Human: Fall Flat",
    "ながおげん": "園児組",
    "社畜王子": "春崎エアル",
    "モンハンライズ": "モンスターハンターライズ",
    "ましろ": "ましろ爻",
    "えある": "春崎エアル",
    "エアル": "春崎エアル",
    "スプラトゥーン３": "Splatoon3",
    "スプラトゥーン２": "Splatoon2",
    "めにまに": "めにまにカンパニー",
    "めにまにかんぱにー": "めにまにカンパニー",
    "タメジャナインデス": "タメナンデス",
    "OW": "Overwatch",
    "闇ノシュウ": "Shu Yamino",
    "弦月": "弦月藤士郎",
    "甲斐田": "甲斐田晴",
    "一唱入魂":"VΔLZ1st 一唱入魂",
    "三華の樂":"VΔLZ2nd 三華の樂",
    "ウマ娘": "ウマ娘　プリティダービー",
    "ポケモン銀": "ポケットモンスター-金・銀",
    "ポケモン金": "ポケットモンスター-金・銀",
    "ポケモンユナイト": "ポケットモンスター-ユナイト",
    "ポケモンSV": "ポケットモンスター-スカーレットバイオレット",
    "ポケモンサファイア": "ポケットモンスター-ルビー・サファイア",
    "ポケモンFRLG": "ポケットモンスター-ファイアレッド・リーフグリーン",
    "ポケモンBDSP": "ポケットモンスター-ブリリアントダイヤモンド・シャイニングパール"
}

HANDLE_TO_NAME_MAP = {
    "@KaidaHaru": "甲斐田晴", "@GenzukiTojiro": "弦月藤士郎", "@valz_ch": "VΔLZ", "@Fumi": "フミ",
    "@HoshikawaSara": "星川サラ", "@YamagamiKaruta": "山神カルタ", "@TodoKohaku": "東堂コハク", "@OliverEvans": "オリバー・エバンス",
    "@HarusakiAir": "春崎エアル", "@NishizonoChigusa": "西園チグサ", "@LainPaterson": "レイン・パターソン",
    "@SeraphDazzlegarden": "セラフ・ダズルガーデン", "@ShibuyaHajime": "渋谷ハジメ", "@YuhiRiri": "夕陽リリ", "@Elu": "える",
    "@SukoyaKana": "健屋花那", "@GweluOsGar": "グウェル・オス・ガール", "@AkagiWen": "赤城ウェン", "@HoshirubeSho": "星導ショウ",
    "@SakakiNess": "榊ネス", "@FrenELustario": "フレン・E・ルスタリオ", "@PontoNei": "先斗寧", "@SasakiSaku": "笹木咲","@LuluSuzuhara":"鈴原るる",
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
UNIT_GROUP_MAP = {
    "ChroNoiR":["叶", "葛葉"],
    "VΔLZ": ["甲斐田晴", "弦月藤士郎"],
    "フ景罪": ["フミ"],
    "タメナンデス": ["オリバー・エバンス"],
    "エア景": ["春崎エアル"],
    "えなかき": ["える", "綺沙良"],
    "園児組": ["弦月藤士郎"],
    "年長組": ["甲斐田晴"],
    "けいあい": ["相羽ういは"],
    "Klime": ["山神カルタ", "東堂コハク"],
    "組体操": ["渋谷ハジメ", "夕陽リリ"],
    "クソザコトレーナーズ": ["春崎エアル", "グウェル・オス・ガール", "소나기（ソ・ナギ）"],
    "ケイトララ": ["渚トラウト"],
    "情報差分組": ["赤城ウェン", "星導ショウ", "榊ネス"],
    "女子騎士祓魔師鑑定士": ["フレン・E・ルスタリオ", "先斗寧", "星導ショウ"],
    "スプラ四天王": ["笹木咲", "春崎エアル", "不破湊"],
    "ふつまひ": ["雪城眞尋"],
    "ながおちぐ": ["西園チグサ"],
    "にじさんじON砲": ["小野町春香"],
    "にじさんじダンス部": ["山神カルタ", "東堂コハク", "レイン・パターソン", "セラフ・ダズルガーデン", "倉持めると"],
    "長尾ーズ": ["三枝明那", "黛灰", "不破湊"],
    "てっぺん": ["本間ひまわり", "鷹宮リオン", "来栖夏芽"],
    "チームABC": ["える", "雪城眞尋"],
    "『絶え間なく突撃』": ["奈羅花", "渡会雲雀", "榊ネス"],
    "SitR名古屋": ["緑仙", "葉加瀬冬雪", "渡会雲雀", "先斗寧", "小清水透"],
    "にじさんじポケカ部": ["花畑チャイカ", "舞元啓介", "葉加瀬冬雪", "加賀美ハヤト", "倉持めると", "赤城ウェン", "栞葉るり", "榊ネス"],
    "にじさんじラジオ体操部": [
        "月ノ美兎", "勇気ちひろ", "える", "樋口楓", "渋谷ハジメ", "伏見ガク", "ギルザレンIII世", "剣持刀也", "叶", "笹木咲", "椎名唯華", "ドーラ", "轟京子", "シスター・クレア", "花畑チャイカ", "社築", "鈴木勝", "緑仙", "鷹宮リオン", "舞元啓介", "でびでび・でびる", "桜凛月", "町田ちま", "ジョー・力一", "ベルモンド・バンデラス", "矢車りね", "黒井しば", "童田明治", "小野町春香", "戌亥とこ", "三枝明那", "雪城眞尋", "レヴィ・エリファ", "葉加瀬冬雪", "加賀美ハヤト", "夜見れな", "黛灰", "アルス・アルマル", "相羽ういは", "天宮こころ", "エリー・コニファー", "ラトナ・プティ", "早瀬走", "健屋花那", "フミ", "星川サラ", "えま★おうがすと", "ルイス・キャミー", "不破湊", "白雪巴", "グウェル・オス・ガール", "ましろ爻", "奈羅花", "来栖夏芽", "フレン・E・ルスタリオ", "メリッサ・キンレンカ", "イブラヒム", "弦月藤士郎", "甲斐田晴", "北小路ヒスイ", "西園チグサ", "アクシア・クローネ", "ローレン・イロアス", "レオス・ヴィンセント", "オリバー・エバンス", "レイン・パターソン", "海妹四葉", "壱百満天原サロメ", "風楽奏斗", "渡会雲雀", "四季凪アキラ", "セラフ・ダズルガーデン", "Taka Radjiman", "Zea-Cornelia", "Riksa Dhirendra", "Nara Haramaung", "Layla Alstroemeria", "Bonnivier Pranaja", "Derem Kado", "Xia-Ekavira", "Mika Melatika", "소나기（ソ・ナギ）", "양나리（ヤン・ナリ）", "하윤（ハ・ユン）", "오지유（オ・ジユ）", "세피나（セフィナ）", "나세라（ナ・セラ）", "小清水透", "獅子堂あかり", "鏑木ろこ", "五十嵐梨花", "石神のぞみ", "ソフィア・ヴァレンタイン", "倉持めると", "佐伯イッテツ", "赤城ウェン", "宇佐美リト", "緋八マナ", "星導ショウ", "叢雲カゲツ", "小柳ロウ", "伊波ライ", "Elira Pendora", "Pomu Rainpuff", "Petra Gurin", "Enna Alouette", "Reimu Endou", "Millie Parfait", "Luca Kaneshiro", "Shu Yamino", "Yugo Asuma", "Sonny Brisko", "Uki Violeta", "Aia Amare", "あばだんご"
    ],
    "バベルの景": ["オリバー・エバンス", "ベルモンド・バンデラス"],
    "めにまにカンパニー": ["桜凛月", "Nara Haramaung", "세피나（セフィナ）"],
    "にじGTA救急隊": ["樋口楓", "森中花咲", "桜凛月", "成瀬鳴", "小野町春香", "三枝明那", "健屋花那", "グウェル・オス・ガール", "弦月藤士郎", "甲斐田晴", "민수하（ミン・スゥーハ）", "오지유（オ・ジユ）", "세피나（セフィナ）", "宇佐美リト", "魁星", "Maria Marionette", "Vezalius Bandage"],
    "忖度フィニッシャーズ": ["える", "愛園愛美"],
    "にじメン歌リレー": ["三枝明那", "弦月藤士郎", "神田笑一", "ジョー・力一", "加賀美ハヤト", "不破湊", "夢追翔"],
    "にじ漢歌祭り": ["北見遊征", "セラフ・ダズルガーデン", "酒寄颯馬", "榊ネス", "伊波ライ", "ミラン・ケストレル", "風楽奏斗", "ジョー・力一", "甲斐田晴", "宇佐美リト", "緋八マナ", "渚トラウト"],
    "だいさんじ甲子園": ["緑仙", "グウェル・オス・ガール", "榊ネス"]
}
# --- 3. タグ判定関数 (リスト形式へ変更) ---
# パフォーマンス最適化: ループ外で小文字化マップを作成
HANDLE_MAP_LOWER = {k.lower(): v for k, v in HANDLE_TO_NAME_MAP.items()}



def analyze_video_tags(title, description, fixed_tags, channel_name="", is_short=False):
    detected_categories = set()
    detected_keywords = set()
    
    title_lower = str(title).lower()
    description_lower = str(description).lower() if description else ""

    # 1. タイトルからカテゴリを直接判定 (CATEGORY_LISTにある言葉)
    for cat in CATEGORY_LIST:
        if cat in title:
            detected_categories.add(cat)

    # 2. キーワード判定 (MEMBERS, UNITS, GAMES, PROGRAMS)
    for group_name, keyword_list in KEYWORD_GROUPS.items():
        for keyword in keyword_list:
            if keyword.lower() in title_lower:
                detected_keywords.add(keyword)

    # 3. 強制カテゴリ追加 (タイトルに特定のフレーズがあればカテゴリへ)
    for phrase, forced_cat in FORCE_CATEGORY_MAP.items():
        if phrase in title:
            detected_categories.add(forced_cat)

    # 4. 表記ゆれ・略称の変換 (マリカ → マリオカート8DX など)
    for slang, formal_tag in TAG_CONVERSION_MAP.items():
        if slang.lower() in title_lower:
            detected_keywords.add(formal_tag)

    # 5. 特殊判定 (【える】のような形式)
    if re.search(r'【[^】]*える[^】]*】', title):
        detected_keywords.add("える")
    if re.search(r'【[^】]*叶[^】]*】', title):
        detected_keywords.add("叶")

    # 6. 説明欄のハンドルネーム(@xxxx)からメンバー特定
    found_handles = re.findall(r'(@[\w\.\-]+)', description_lower)
    for handle in found_handles:
        h_lower = handle.lower()
        if h_lower in HANDLE_MAP_LOWER:
            detected_keywords.add(HANDLE_MAP_LOWER[h_lower])

    # 7. ユニットとメンバーの相互補完 (VΔLZがあれば甲斐田・弦月を追加)
    for unit_name, members in UNIT_GROUP_MAP.items():
        if unit_name in detected_keywords:
            for member in members:
                detected_keywords.add(member)
        # メンバーが全員揃っていたらユニット名も追加
        if set(members).issubset(detected_keywords):
            detected_keywords.add(unit_name)

    # 8. 固定タグ（チャンネル設定やプレイリスト設定）の反映
    if fixed_tags:
        for tag in fixed_tags:
            detected_keywords.add(tag)
            # もし固定タグがカテゴリリストにある言葉ならカテゴリにも入れる
            if tag in CATEGORY_LIST:
                detected_categories.add(tag)

    # 9. キーワードからカテゴリを推論
    # ゲーム名が含まれていれば「ゲーム実況」を追加
    games_set = set(KEYWORD_GROUPS["GAMES"])
    if not detected_keywords.isdisjoint(games_set):
        detected_categories.add("ゲーム実況")
        
    # 番組名が含まれていれば「公式企画・番組」を追加
    programs_set = set(KEYWORD_GROUPS["PROGRAMS"])
    if not detected_keywords.isdisjoint(programs_set):
        detected_categories.add("公式企画・番組")
        detected_categories.add("企画")

    # 10. 公式切り抜き判定 (ショート動画用)
    if is_short and ("長尾景" in channel_name or "長尾景" in title):
        exclude_cats = {"踊り動画", "歌動画", "楽器配信・動画", "歌配信", "踊り配信"}
        if not detected_categories.intersection(exclude_cats):
            detected_categories.add("公式切り抜き")

    # 11. 最終チェック
    if not detected_categories:
        detected_categories.add("未分類")

    return sorted(list(detected_categories)), sorted(list(detected_keywords))
# --- 4. YouTube API ---
def get_uploads_playlist_id(youtube, channel_id):
    try:
        resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
        return resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except: return None
def timestamp_to_seconds(ts_str):
    parts = ts_str.split(':')
    if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0
def extract_music_metadata(desc):
    auto_songs = []
    # 日本語・英語両方のパターンに対応
    song_m = re.search(r"(?:Song|曲|楽曲)\s*[:：\-]?\s*(.+)", desc, re.IGNORECASE)
    artist_m = re.search(r"(?:Artist|アーティスト)\s*[:：\-]?\s*(.+)", desc, re.IGNORECASE)
    
    if song_m:
        s_title = song_m.group(1).strip()
        s_artist = artist_m.group(1).strip() if artist_m else "Unknown Artist"
        # 配信元情報のノイズ除去
        s_artist = re.split(r'\(on behalf of', s_artist)[0].strip()
        auto_songs.append({"title": s_title, "artist": s_artist, "start": 0})
    return auto_songs
    
def parse_setlist_from_text(text):
    
    if not text: return []
    text = html.unescape(text)

    # タイムスタンプ(ts)と、次のタイムスタンプが来るまでのテキスト(raw)をペアで抽出
    pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)(.*?)(?=\d{1,2}:\d{2}(?::\d{2})?|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if len(matches) < 4: return []

    songs = []
    # 除外したい単語リスト
    exclude_keywords = ["開始", "セトリ", "SETLIST", "本編", "待機", "挨拶", "MC", "トーク"]

    for ts_str, raw_text in matches:
        # 1. HTMLタグ除去とクリーニング
        clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
        
        # 2. 曲名の前後にある不要な記号（♪、・、数字、カッコ、~ など）を徹底除去
        clean_text = re.sub(r'^[:\s♪・\-\d\.\]】）)／/|｜￤]+', '', clean_text).strip()
        # 末尾の「~」や「～」を削除
        clean_text = re.sub(r'\s*[~～]+$', '', clean_text).strip()
        # 行末のURLやカッコ内を掃除
        clean_text = re.sub(r'\s*[\(（]?http.*$', '', clean_text).strip()

        # 3. 除外ワード判定（大文字に変換してからチェック）
        if not clean_text:
            continue
            
        clean_text_upper = clean_text.upper()
        if any(x in clean_text_upper for x in exclude_keywords):
            continue

        # 4. アーティスト名の分割
        t, a = clean_text, ""
        separators = [' / ', '／', ' - ', ' － ', '：', ' : ', '/','￤']
        for sep in separators:
            if sep in clean_text:
                parts = clean_text.split(sep, 1)
                t, a = parts[0].strip(), parts[1].strip()
                break
        
        songs.append({
            "title": t,
            "artist": a,
            "start": timestamp_to_seconds(ts_str)
        })
            
    return songs
    
def get_duration_seconds(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match: return 0
    h, m, s = [int(match.group(i) or 0) for i in range(1, 4)]
    return h * 3600 + m * 60 + s

def fetch_videos_from_playlist(youtube, playlist_id, channel_name, fixed_tags, auto_tags=None):
    videos = []
    next_page_token = None
    page_count = 0
    while page_count < MAX_PAGES_TO_FETCH:
        try:
            res = youtube.playlistItems().list(part='snippet,contentDetails', playlistId=playlist_id, maxResults=50, pageToken=next_page_token).execute()
            items = res.get('items', [])
            if not items: break
            
            v_ids = [it['contentDetails']['videoId'] for it in items]
            v_res = youtube.videos().list(part='contentDetails,snippet', id=','.join(v_ids)).execute()
            details = {v['id']: v for v in v_res.get('items', [])}

            for item in items:
                v_id = item['contentDetails']['videoId']
                if v_id not in details: continue
                
                v_data = details[v_id]
                snip = v_data['snippet']
                desc = snip.get('description', '')
                sec = get_duration_seconds(v_data['contentDetails']['duration'])
                
                # 1. タグ判定
                cat, kw = analyze_video_tags(snip['title'], desc, fixed_tags, channel_name, (0 < sec <= 60))
                
                # 2. カテゴリに応じた楽曲情報の自動補完
                auto_songs = []
                cat_set = set(cat)
                
                # A. 歌配信の場合：説明欄のセトリ（タイムスタンプ）を取りに行く
                if "歌配信" in cat_set:
                    auto_songs = parse_setlist_from_text(desc)
                
                # B. 歌動画・踊り動画の場合：YouTube公式の「ライセンス情報」を取りに行く
                elif cat_set.intersection({"歌動画", "踊り動画"}):
                    # まず説明欄から抽出を試み、なければライセンス情報を探す
                    # (歌動画でも短いセトリを書く人がいるための予備処理)
                    auto_songs = parse_setlist_from_text(desc) or extract_music_metadata(desc)
                    # 公式情報が載っていない場合のみ、予備として説明欄のテキスト解析(自作セトリ)を試みる
                    if not auto_songs:
                        auto_songs = parse_setlist_from_text(desc)

                # 3. データの登録
                videos.append({
                    "youtubeId": v_id,
                    "title": snip['title'],
                    "channel": channel_name,
                    "date": snip['publishedAt'][:10],
                    "thumbnail": f"https://i.ytimg.com/vi/{v_id}/mqdefault.jpg",
                    "category": cat,
                    "keywords": kw,
                    "tags": auto_tags or [],
                    "songs": auto_songs
                })
    
    
def update_github_json(new_videos):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    contents_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{JSON_FILE_PATH}"

    # 既存データの読み込み
    res = requests.get(contents_url, headers=headers)
    existing_videos, existing_sha = [], None
    if res.status_code == 200:
        existing_sha = res.json().get('sha')
        decoded = base64.b64decode(res.json()['content']).decode('utf-8-sig')
        existing_videos = json.loads(decoded)

    # 既存データをマップ化 (管理対象チャンネルのみ)
    managed_map = {v['youtubeId']: v for v in existing_videos if v.get('channel') in MANAGED_CHANNEL_NAMES}
    preserved_videos = [v for v in existing_videos if v.get('channel') not in MANAGED_CHANNEL_NAMES]

    updated_count, added_count = 0, 0

    for nv in new_videos:
        v_id = nv['youtubeId']
        if v_id in managed_map:
            ev = managed_map[v_id]
            is_changed = False
            
            # ★重要★ 手動入力された songs や tags が既存にあれば優先して保持
            if ev.get('songs') and not nv.get('songs'):
                nv['songs'] = ev['songs']
                is_changed = True
            if ev.get('tags') and not nv.get('tags'):
                nv['tags'] = ev['tags']
                is_changed = True
                
            # カテゴリとキーワードの統合
            merged_cat = sorted(list(set(nv['category']) | set(ev.get('category', []))))
            if "未分類" in merged_cat and len(merged_cat) > 1: merged_cat.remove("未分類")
            
            if sorted(ev.get('category', [])) != merged_cat or sorted(ev.get('keywords', [])) != sorted(nv['keywords']):
                nv['category'] = merged_cat
                is_changed = True
            
            if is_changed: updated_count += 1
            managed_map[v_id] = nv
        else:
            managed_map[v_id] = nv
            added_count += 1

    final_list = sorted(preserved_videos + list(managed_map.values()), key=lambda x: x.get('date', ''), reverse=True)

    # 保存処理
    new_content = json.dumps(final_list, indent=2, ensure_ascii=False).encode('utf-8')
    commit_data = {"message": f"BOT: Update archive (Add {added_count}, Update {updated_count})", "content": base64.b64encode(new_content).decode('utf-8'), "sha": existing_sha}
    requests.put(contents_url, headers=headers, json=commit_data)
    print(f"🚀 GitHub更新完了！ (総数: {len(final_list)}件)")

def main():
    if not YOUTUBE_API_KEY or not GITHUB_TOKEN: return
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    fetched_videos = []
    
    # 1. チャンネルの通常アップロード
    for ch in CHANNELS:
        pid = get_uploads_playlist_id(youtube, ch['id'])
        if pid: fetched_videos.extend(fetch_videos_from_playlist(youtube, pid, ch['name'], ch.get('fixed_tags', [])))

    # 2. 特殊プレイリスト (自動タグ付与あり)
    for pl in EXTRA_PLAYLISTS:
        fetched_videos.extend(fetch_videos_from_playlist(youtube, pl['id'], pl['name'], pl.get('fixed_tags', []), auto_tags=pl.get('auto_tags')))

    if fetched_videos:
        update_github_json(fetched_videos)

if __name__ == "__main__":
    main()


