import os
import json
import base64
import re
import html
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

OWNER_NAME = "長尾景"
TARGET_X_USER = "midori_2434"
MANUAL_SONG_ARTIST_MAP = {
    "セレナーデ": "なとり",
    "分かっちゃいないね": "monet"
    # 他にも誤検知しやすい曲があればここに追加
}
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
        "id": "PLCuBbANKdfzu6ElbEC1S-mrOFyAGQRKw1",
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
    "カラオケ": "歌配信",
    "歌枠": "歌配信",
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
        # --- あ行 ---
        "愛園愛美", "相羽ういは", "赤城ウェン", "赤羽葉子", "明楽レイ", "アクシア・クローネ", "朝日南アカネ",
        "飛鳥ひな", "東堂コハク", "アミシア・ミチェラ", "雨森小夜", "アルス・アルマル", "アンジュ・カトリーナ",
        "安土桃", "家長むぎ", "五十嵐梨花", "伊波ライ", "イ・オン", "イ・シウ", "イ・ロハ",
        "壱百満天原サロメ", "イブラヒム", "出雲霞", "一橋綾人", "五木左京", "戌亥とこ", "宇佐美リト",
        "宇志海いちご", "卯月コウ", "海妹四葉", "エクス・アルビオ", "えま★おうがすと", "エトナ・クリムソン",
        "エリー・コニファー", "える", "遠北千南", "オ・ジユ", "御伽原江良", "小野町春香", "オリバー・エバンス",
        
        # --- か行 ---
        "甲斐田晴", "海夜叉神", "魁星", "加賀美ハヤト", "カエン", "蝸堂みかる", "ガオン", "風楽奏斗",
        "春崎エアル", "霞", "片眼鏡", "葛葉", "語部紡", "叶", "鏑木ろこ", "神田笑一", "北小路ヒスイ",
        "北見遊征", "ギルザレンIII世", "久遠千歳", "九里詠太", "黒井しば", "雲母たまこ", "倉持めると",
        "グウェル・オス・ガール", "郡道美玲", "剣持刀也", "弦月藤士郎", "小清水透", "梢桃音", "小柳ロウ",
        "コ・ヤミ",
        
        # --- さ行 ---
        "佐伯イッテツ", "早乙女ベリー", "榊ネス", "酒寄颯馬", "桜凛月", "笹木咲", "シスカ・レオンタイン",
        "椎名唯華", "シェリン・バーガンディ", "栞葉るり", "シスター・クレア", "四季凪アキラ", "司賀りこ",
        "獅子堂あかり", "静凛", "渋谷ハジメ", "嶋野", "篠宮ゆの", "城瀬いすみ", "ジョー・力一",
        "白砂あやね", "白雪巴", "シン・ギル", "シン・ユヤ", "周央サンゴ", "鈴木勝", "鈴鹿詩子",
        "鈴原るる", "鈴谷アキ", "瀬戸美夜子", "セフィナ", "セラフ・ダズルガーデン", "先斗寧",
        "ソ・ナギ", "ソフィア・ヴァレンタイン", "ソン・ミア", "十河ののは",
        
        # --- た行 ---
        "鷹宮リオン", "立伝都々", "千凛あゆむ", "珠乃井ナナ", "タカ・ラジマン", "月ノ美兎", "月見しずく",
        "塚原大地", "チェ・アラ", "童田明治", "ドーラ", "轟京子",
        
        # --- な行 ---
        "渚トラウト", "名伽尾アズマ", "七瀬すず菜", "奈羅花", "鳴門こがね", "ナ・セラ", "成瀬鳴",
        "ナギサ・アルシニア", "西園チグサ", "ニュイ・ソシエール", "猫屋敷美紅", "ヌン・ボラ",
        
        # --- は行 ---
        "長尾景", "長尾姉上", "ハクレン", "ハ・ユン", "博衣こより", "花籠つばさ", "花畑チャイカ",
        "早瀬走", "葉加瀬冬雪", "葉山舞鈴", "ハナ・マキア", "ハン・チホ", "バン・ハダ", "樋口楓",
        "日ノ隈らん", "緋八マナ", "伏見ガク", "フミ", "フレン・E・ルスタリオ", "不破湊", "文野環",
        "ボニフィエール・プラナジャ", "星川サラ", "星導ショウ", "本間ひまわり",
        
        # --- ま行 ---
        "舞元啓介", "魔界ノりりむ", "魔使マオ", "ましろ爻", "町田ちま", "水面まどか", "ミカ・メラティカ",
        "ミラン・ケストレル", "三枝明那", "ミン・スゥーハ", "ムン・ホジュン", "モアリン", "叢雲カゲツ",
        "物述有栖", "メリッサ・キンレンカ", "森中花咲",
        
        # --- や行 ---
        "矢車りね", "八朔ゆず", "山田龍一郎", "山神カルタ", "ヤン・ナリ", "勇気ちひろ", "夕陽リリ",
        "雪城眞尋", "雪汝", "ユ・ルリ", "夢月ロア", "夢追翔", "夜牛詩乃", "夜見れな",
        
        # --- ら・わ行 ---
        "ライ・ガリレイ", "ライラ・アルストロエメリア", "ラトナ・プティ", "リクサ・ディレンドラ", "リゼ・ヘルエスタ",
        "リュ・ハリ", "ルイス・キャミー", "ルンルン", "レイン・パターソン", "レヴィ・エリファ",
        "レオス・ヴィンセント", "レザ・アファンルナ", "レヨン", "ローレン・イロアス", "ローロー",
        "緑仙", "竜胆尊", "渡会雲雀",
        
        # --- 記号・特殊・アルファベット ---
        "男虎", "皇れお", "神永タイガ", "御子神琴音", "ぷりん・らら・もーど", "ぽめろ・ぱんち",
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
        "Pokémon LEGENDS アルセウス", "マインクラフト", "マリオシリーズ", "スーパーマリオブラザーズ", "深夜放送", "キーボードパズル","LIBRARIAN",
        "スーパーマリオメーカー2", "マリオカート8DX", "マリオカートワールド", "マリオパーティ", "漢字でGO!", "PC Building Simulator","Don't Drop The Cake",
        "その他マリオシリーズ", "みんなで空気読み。", "メイド イン ワリオ", "桃太郎電鉄", "モンスターストライク", "つぐのひ　忌み夜の喰霊品店",
        "モンスターハンター：ワールド", "星のカービィシリーズ", "リズム天国", "レイトン教授と不思議な町", "崩壊：スターレイル", "Knockout City",
        "一致するまで終われまテン!!", "任天堂", "パチスロ", "ホラーゲーム", "Chilla's Art", "PACIFY", "Twelve Minutes", "トロッコ問題",
        "Poppy Playtime", "Keep Talking and Nobody Explodes", "Protein for Muscle", "R.E.P.O.", "青鬼", "RTA", "例外配達",
        "その他ホラーゲーム", "カードゲーム", "その他ゲーム", "Five Nights at Freddy's", "Getting Over It", "V最協", "V祭協"
    ],
    "PROGRAMS": [
        "SYMPHONIA Day2", "LOCK ON FLEEK", "にじ鯖夏祭り", "VTuberエンジョイカジュアル交流戦","Uncharted Spheres",
        "ベース", "歳の差バラエティ(?)", "VΔLZ1st 一唱入魂", "VΔLZ2nd 三華の樂", "にじ漢歌祭り","にじベイブレード","ながおしゃべり",
        "にじメンメドレー", "VTuber最協決定戦", "V祭協", "VTuberのあそびば", "くろのわーるがなんかやる","にじ遊戯王祭2026",
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
    "Uncharted_Spheres":"Uncharted Spheres",
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
    "@ShirasunaAyane": "白砂あやね",
    "@MinamoMadoka": "水面まどか",
    "@Otora": "男虎",
    "@KuriEita": "九里詠太",
    "@SazanamiIruka": "小々波いるか",
    "@ChirinAyumu": "千凛あゆむ",
    "@TsukaharaDaichi": "塚原大地",
    "@MikogamiKotone": "御子神琴音",
    "@Rei7": "Rei7",
    "@Leyon": "レヨン",
    "@PurinLaLaMode": "ぷりん・らら・もーど",
    "@PomeloPunch": "ぽめろ・ぱんち",
    "@KaminagaTaiga": "神永タイガ",
    "@YamadaRyuichiro": "山田龍一郎",
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
# 絵文字 / 記号 → ライバー名 変換辞書
# 絵文字 / 記号 → ライバー名 変換辞書
LIVER_EMOJI_MAP = {
    # --- 4絵文字 ---
    "♥️♠️♦️♣️": "物述有栖",
    "♥♠♦♣": "物述有栖",

    # --- 3絵文字 ---
    "🥼🌱😺": "レオス・ヴィンセント",

    # --- 2絵文字（異字体セレクタ等のゆれ含む） ---
    "🎀💙": "勇気ちひろ",
    "🏰🌕️": "ギルザレンIII世",
    "🏰🌕": "ギルザレンIII世",
    "竜胆尊": "竜胆尊",
    "🍶⚜️": "竜胆尊",
    "🍶⚜": "竜胆尊",
    "🚪👿": "でびでび・でびる",
    "🎑💊": "月見しずく",
    "🐕🐾": "黒井しば",
    "🐺🍎": "童田明治",
    "📷💚": "瀬戸美夜子",
    "🏰🕛": "御伽原江良",
    "🌐💫": "雪城眞尋",
    "🍃🗻": "葉山舞鈴",
    "🎩🐤": "夜見れな",
    "💻💙": "黛灰",
    "🍮💎": "相羽ういは",
    "🐻💎": "ラトナ・プティ",
    "🏃‍♀️💨": "早瀬走",
    "💉💘": "健屋花那",
    "❤️🦋": "ルイス・キャミー",
    "❤🦋": "ルイス・キャミー",
    "💥衝突": "魔使マオ",
    "🥂✨": "不破湊",
    "👠⛓": "白雪巴",
    "👠⛓️": "白雪巴",
    "✖🍳": "奈羅花",
    "🐏🎵": "来栖夏芽",
    "🎻🛵": "弦月藤士郎",
    "🦖🎖": "朝日南アカネ",
    "🦖🎖️": "朝日南アカネ",
    "💞🦩": "周央サンゴ",
    "🐬🌱": "西園チグサ",
    "🗝💸": "ローレン・イロアス",
    "💯🦂": "壱百満天原サロメ",
    "🍝🍷": "風楽奏斗",
    "♦☕": "渡会雲雀",
    "♦️☕": "渡会雲雀",
    "🦉🎻": "セラフ・ダズルガーデン",
    "🦦✌️": "Miyu Ottavia",
    "🦦✌": "Miyu Ottavia",
    "😈💥": "Riksa Dhirendra",
    "🕰🌺": "Layla Alstroemeria",
    "🌋🍔": "Etna Crimson",
    "🔦🦁": "Siska Leontyne",
    "🐥🍭": "Nagisa Arcinia",
    "🌒☁": "Reza Avanluna",
    "🌒☁️": "Reza Avanluna",
    "🐾🏵": "Hyona Elatiora",
    "🐾🏵️": "Hyona Elatiora",
    "⚗️🎼": "Xia Ekavira",
    "⚗🎼": "Xia Ekavira",
    "👻📌": "Mika Melatika",
    "🎀🧸": "ユ・ルリ",
    "🌛🌱": "シン・ユヤ",
    "🦴🔔": "カエン",
    "🌑🦋": "ハン・チホ",
    "☁️🌫️": "ハクレン",
    "☁🌫": "ハクレン",
    "🌹💛": "チェ・アラ",
    "❄💜": "ヌン・ボラ",
    "❄️💜": "ヌン・ボラ",
    "💗🌕️": "セフィナ",
    "💗🌕": "セフィナ",
    "🐈‍⬛🔪": "コ・ヤミ",
    "🐈‍⬛🔪️": "コ・ヤミ",
    "🎮️🦭": "ハ・ユン",
    "🎮🦭": "ハ・ユン",
    "🌸🌙": "ナ・セラ",
    "🐱💫": "獅子堂あかり",
    "🍕🎢": "鏑木ろこ",
    "⚾🧡": "五十嵐梨花",
    "🐰🗞": "ソフィア・ヴァレンタイン",
    "🧸🌙": "倉持めると",
    "🍱🦖": "赤城ウェン",
    "🌩🦒": "宇佐美リト",
    "🌩️🦒": "宇佐美リト",
    "🐝🤣": "緋八マナ",
    "🐙🌟": "星導ショウ",
    "🥷🔫": "叢雲カゲツ",
    "👻🔪": "小柳ロウ",
    "🪓🎀": "立伝都々",
    "🚓🐾": "栞葉るり",
    "🦋⏳": "ミラン・ケストレル",
    "📿🍔": "北見遊征",
    "🔑🐍": "魁星",
    "🫖🌿": "榊ネス",
    "🍰🧁": "早乙女ベリー",
    "🐣📛": "雲母たまこ",
    "🐟🍴": "渚トラウト",
    "📚🗣": "一橋綾人",
    "📚🗣️": "一橋綾人",
    "💼📊": "五木左京",
    "♫🐌": "蝸堂みかる",
    "♫💮": "夜牛詩乃",
    "♫🦎": "十河ののは",
    "♫💐": "猫屋敷美紅",
    "👑🌸": "皇れお",
    "💍📘": "篠宮ゆの",
    "🏰🍬": "城瀬いすみ",
    "🧢🪽": "花籠つばさ",
    "🏖️🫶": "白砂あやね",
    "🏖🫶": "白砂あやね",
    "🪟🫶": "水面まどか",
    "👊🐯": "男虎",
    "🧰✂️": "九里詠太",
    "🧰✂": "九里詠太",
    "🫧🐬": "小々波いるか",
    "💜🗯️": "千凛あゆむ",
    "💜🗯": "千凛あゆむ",
    "🗡🐼": "塚原大地",
    "🦈✦": "Rei7",
    "🎮️🥇": "レヨン",
    "🎮🥇": "レヨン",
    "🍮💌": "ぷりん・らら・もーど",
    "🌠👊": "ぽめろ・ぱんち",
    "🐅🎻": "神永タイガ",
    "⛰️🎹": "山田龍一郎",
    "⛰🎹": "山田龍一郎",

    # --- 1絵文字 / 単一記号 ---
    "🐰": "月ノ美兎",
    "🗼": "える",
    "🍁": "樋口楓",
    "🥦": "静凛",
    "💜": "静凛",
    "🌱": "渋谷ハジメ",
    "🐈": "鈴谷アキ",
    "🎶": "鈴鹿詩子",
    "🍓": "宇志海いちご",
    "🌷": "家長むぎ",
    "🌇": "夕陽リリ",
    "🐟": "文野環",
    "✌️": "伏見ガク",
    "✌": "伏見ガク",
    "🦊": "伏見ガク",
    "⚔️": "剣持刀也",
    "⚔": "剣持刀也",
    "🌼": "森中花咲",
    "🐻": "森中花咲",
    "🔫": "叶",
    "💀": "赤羽葉子",
    "🎋": "笹木咲",
    "🍜": "闇夜乃モルル",
    "🌻": "本間ひまわり",
    "🍼": "魔界ノりりむ",
    "❄️": "雪汝",
    "❄": "雪汝",
    "👻": "椎名唯華",
    "🔥": "ドーラ",
    "⛩️": "海夜叉神",
    "⛩": "海夜叉神",
    "☀️": "名伽尾アズマ",
    "🦑": "出雲霞",
    "🐐": "轟京子",
    "🔔": "シスター・クレア",
    "🌵": "花畑チャイカ",
    "🖥️": "社築",
    "🖥": "社築",
    "🍑": "安土桃",
    "☪️": "鈴木勝",
    "☪": "鈴木勝",
    "🐼": "緑仙",
    "🌙": "卯月コウ",
    "🍊": "八朔ゆず",
    "🔪": "神田笑一",
    "🍅": "神田笑一",
    "🐤": "飛鳥ひな",
    "🍭": "春崎エアル",
    "☂️": "雨森小夜",
    "☔️": "雨森小夜",
    "☂": "雨森小夜",
    "☔": "雨森小夜",
    "🦅": "鷹宮リオン",
    "👨‍🌾": "舞元啓介",
    "🌸": "桜凛月",
    "🐹": "町田ちま",
    "🤡": "ジョー・力一",
    "🎈": "ジョー・力一",
    "🍬": "遠北千南",
    "🎙️": "成瀬鳴",
    "🎙": "成瀬鳴",
    "🥃": "ベルモンド・バンデラス",
    "🌽": "矢車りね",
    "🎤": "夢追翔",
    "🧠": "久遠千歳",
    "🐽": "郡道美玲",
    "🌖": "夢月ロア",
    "♨️": "小野町春香",
    "♨": "小野町春香",
    "🧂": "語部紡",
    "📘": "語部紡",
    "🍹": "戌亥とこ",
    "⚖️": "アンジュ・カトリーナ",
    "⚖": "アンジュ・カトリーナ",
    "👑": "リゼ・ヘルエスタ",
    "🌶️": "三枝明那",
    "🌶": "三枝明那",
    "💕": "愛園愛美",
    "🎨": "鈴原るる",
    "🛡️": "エクス・アルビオ",
    "🛡": "エクス・アルビオ",
    "🔲": "レヴィ・エリファ",
    "🎃": "ニュイ・ソシエール",
    "⚗️": "葉加瀬冬雪",
    "⚗": "葉加瀬冬雪",
    "🏢": "加賀美ハヤト",
    "📕": "アルス・アルマル",
    "🎐": "天宮こころ",
    "🌲": "エリー・コニファー",
    "🚴‍♀️": "早瀬走",
    "🧐": "シェリン・バーガンディ",
    "🔖": "フミ",
    "🌟": "星川サラ",
    "🎴": "山神カルタ",
    "★": "えま★おうがすと",
    "😎": "グウェル・オス・ガール",
    "🧷": "ましろ爻",
    "🎠": "フレン・E・ルスタリオ",
    "🐝": "メリッサ・キンレンカ",
    "💧": "イブラヒム",
    "☯️": "長尾景",
    "☯": "長尾景",
    "🌞": "甲斐田晴",
    "🌌": "空星きらめ",
    "🍯": "東堂コハク",
    "❇️": "北小路ヒスイ",
    "❇": "北小路ヒスイ",
    "🐈‍⬛": "アクシア・クローネ",
    "🍵": "オリバー・エバンス",
    "❤️‍🔥": "レイン・パターソン",
    "❤‍🔥": "レイン・パターソン",
    "💭": "天ヶ瀬むゆ",
    "🫐": "先斗寧",
    "🍀": "海妹四葉",
    "📄": "四季凪アキラ",
    "🥩": "Taka Radjiman",
    "🔶": "ZEA Cornelia",
    "☕": "Hana Macchia",
    "🚨": "Rai Galilei",
    "🐧": "Amicia Michella",
    "👽": "Azura Cecillia",
    "🐯": "Nara Haramaung",
    "🎣": "Bonnivier Pranaja",
    "🎁": "Derem Kado",
    "📶": "ウィフィ",
    "🌊": "ミン・スゥーハ",
    "👔": "ガオン",
    "🎵": "ローロー",
    "🌧": "ソ・ナギ",
    "🌧️": "ソ・ナギ",
    "🐾": "イ・シウ",
    "😸": "明楽レイ",
    "🚀": "イ・ロハ",
    "📌": "ヤン・ナリ",
    "👁‍🗨": "リュ・ハリ",
    "🌫️": "シン・ギル",
    "🌫": "シン・ギル",
    "⚜️": "オ・ジユ",
    "⚜": "オ・ジユ",
    "🍡": "ソン・ミア",
    "🏴‍☠️": "バン・ハダ",
    "🏴‍☠": "バン・ハダ",
    "🍰": "イ・オン",
    "🫧": "小清水透",
    "❤️‍🩹": "石神のぞみ",
    "❤‍🩹": "石神のぞみ",
    "🤝": "佐伯イッテツ",
    "💡": "伊波ライ",
    "📒": "司賀りこ",
    "🛼": "珠乃井ナナ",
    "🪞": "綺沙良",
    "🪷": "梢桃音",
    "🥨": "ルンルン",
    "🥗": "七瀬すず菜",
    "🍇": "酒寄颯馬",
    "🥢": "御子神琴音",

    # --- 予約語・全体歌唱 ---
    "全員": "全員"
}
# セトリパース時の除外単語
EXCLUDE_SETLIST_KEYWORDS = [
    "開始", "セトリ", "SETLIST", "本編", "待機", "挨拶",
    "MC", "トーク", "自己紹介", "感想", "告知", "お披露目",
    "OP", "ED", "スパチャ", "振り返り"
]
GLOBAL_ARTIST_DB: Dict[str, str] = {}
HANDLE_MAP_LOWER = {k.lower(): v for k, v in HANDLE_TO_NAME_MAP.items()}

# ==============================================================================
# 2. タグ & 楽曲解析ロジック
# ==============================================================================

def analyze_video_tags(title, description, fixed_tags, channel_name="", is_short=False):
    detected_categories = set()
    detected_keywords = set()
    
    title_lower = str(title).lower()
    description_lower = str(description).lower() if description else ""

    for cat in CATEGORY_LIST:
        if cat in title:
            detected_categories.add(cat)

    for group_name, keyword_list in KEYWORD_GROUPS.items():
        for keyword in keyword_list:
            if keyword.lower() in title_lower:
                detected_keywords.add(keyword)

    for phrase, forced_cat in FORCE_CATEGORY_MAP.items():
        if phrase in title:
            detected_categories.add(forced_cat)

    for slang, formal_tag in TAG_CONVERSION_MAP.items():
        if slang.lower() in title_lower:
            detected_keywords.add(formal_tag)

    if re.search(r'【[^】]*える[^】]*】', title):
        detected_keywords.add("える")
    if re.search(r'【[^】]*叶[^】]*】', title):
        detected_keywords.add("叶")


    found_handles = re.findall(r'(@[\w\.\-]+)', description_lower)
    for handle in found_handles:
        h_lower = handle.lower()
        if h_lower in HANDLE_MAP_LOWER:
            detected_keywords.add(HANDLE_MAP_LOWER[h_lower])

    for unit_name, members in UNIT_GROUP_MAP.items():
        if unit_name in detected_keywords:
            for member in members:
                detected_keywords.add(member)
        if set(members).issubset(detected_keywords):
            detected_keywords.add(unit_name)

    if fixed_tags:
        for tag in fixed_tags:
            detected_keywords.add(tag)
            if tag in CATEGORY_LIST:
                detected_categories.add(tag)

    if not detected_categories:
        detected_categories.add("未分類")

    return sorted(list(detected_categories)), sorted(list(detected_keywords))

def get_duration_seconds(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match: return 0
    h, m, s = [int(match.group(i) or 0) for i in range(1, 4)]
    return h * 3600 + m * 60 + s

def extract_music_metadata(desc):
    if not desc:
        return []
    clean_lines = [
        line.strip() for line in desc.split("\n")
        if not any(bad in line.lower() for bad in ["http", "channel", "/@", "music.apple", "spotify"])
    ]
    clean_desc = "\n".join(clean_lines)

    auto_songs = []
    song_m = re.search(r"(?:Song|曲|楽曲)\s*[:：\-]?\s*(.+)", clean_desc, re.IGNORECASE)
    artist_m = re.search(r"(?:Artist|アーティスト)\s*[:：\-]?\s*(.+)", clean_desc, re.IGNORECASE)

    if song_m:
        s_title = song_m.group(1).strip("  ")
        s_artist = artist_m.group(1).strip("  ") if artist_m else "Unknown Artist"
        s_artist = re.split(r'\(on behalf of', s_artist)[0].strip("  ")
        if not any(bad in s_title.lower() or bad in s_artist.lower() for bad in ["http", "channel", "@"]):
            auto_songs.append({"title": s_title, "artist": s_artist, "start": 0})

    return auto_songs

def normalize_title(title: str) -> str:
    t = unicodedata.normalize('NFKC', str(title)).lower()
    t = re.sub(r'[\(（\[【][^\)）\]】]*[\)）\]】]', '', t)
    t = re.sub(r'[\s\-_・/／:：~～!?！？♪· ]', '', t)
    return t.strip()

def load_artist_db():
    global GLOBAL_ARTIST_DB
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    source_files = [
        "archives/custom_known_songs.json",
        "songs/videos.json",
        "archives/archive_videos.json",
        "archives/external_videos.json"
    ]
    db = {}
    for rel_path in source_files:
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{rel_path}"
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                raw_bytes = base64.b64decode(r.json()['content'])
                text = raw_bytes.decode('utf-8-sig').strip()
                if not text: continue
                data = json.loads(text)
                for item in data:
                    for s in item.get("songs", []):
                        raw_title = s.get("title", "").strip()
                        raw_artist = s.get("artist", "").strip()
                        if not raw_title or not raw_artist or raw_artist in ["Unknown Artist", ""]:
                            continue
                        pure_title = re.sub(r'\s+with\s+.*$', '', raw_title).strip("  ")
                        norm_key = normalize_title(pure_title)
                        if norm_key and norm_key not in db:
                            db[norm_key] = raw_artist
        except Exception:
            continue
    GLOBAL_ARTIST_DB = db
    print(f"📚 アーティストDB初期化完了: {len(GLOBAL_ARTIST_DB)} 曲をキャッシュ")

def fetch_artist_from_itunes(title: str) -> str:
    clean_title = re.sub(r'[\(（\[【].*?[\)）\]】]', '', title).strip("  ")
    if not clean_title: return ""
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean_title)}&entity=song&country=JP&limit=5"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            for item in res.json().get("results", []):
                if normalize_title(item.get("trackName", "")) == normalize_title(clean_title):
                    return item.get("artistName", "").strip()
    except Exception:
        pass
    return ""

def fetch_artist_from_vocadb(title: str) -> str:
    clean_title = re.sub(r'[\(（\[【][^\)）\]】]*[\)）\]】]', '', title).strip("  ")
    if not clean_title: return ""
    url = "https://vocadb.net/api/songs"
    params = {"query": clean_title, "preferAccurateMatches": "true", "maxResults": 3, "lang": "Japanese"}
    try:
        res = requests.get(url, params=params, headers={"User-Agent": "VTuberArchiveBot/1.0"}, timeout=4)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                if normalize_title(item.get("name", "")) == normalize_title(clean_title):
                    return re.split(r'\s+(?:feat\.|ft\.|/)\s*', item.get("artistString", ""), 1)[0].strip()
    except Exception:
        pass
    return ""

def resolve_artist_name(raw_title: str) -> str:
    if not raw_title:
        return ""
    pure_t = re.sub(r'\s+with\s+.*$', '', raw_title).strip("  ")
    norm_key = normalize_title(pure_t)

    # 1. 手動確定辞書（最優先）
    if pure_t in MANUAL_SONG_ARTIST_MAP:
        return MANUAL_SONG_ARTIST_MAP[pure_t]
    norm_manual = {normalize_title(k): v for k, v in MANUAL_SONG_ARTIST_MAP.items()}
    if norm_key in norm_manual:
        return norm_manual[norm_key]

    # 2. 内部DB（過去データ・手動確定ファイル）
    if norm_key in GLOBAL_ARTIST_DB:
        return GLOBAL_ARTIST_DB[norm_key]

    # 3. iTunes API（J-POP・メジャー曲を優先判定）
    artist = fetch_artist_from_itunes(pure_t)

    # 4. VocaDB（ボカロ曲フォールバック）
    if not artist:
        artist = fetch_artist_from_vocadb(pure_t)

    if artist:
        GLOBAL_ARTIST_DB[norm_key] = artist

    return artist

def parse_setlist_from_text(text, channel_owner=OWNER_NAME, fallback_members=None):
    if not text:
        return []
    text = html.unescape(text)
    ts_regex = r'(?:(?<=\s)|^|\b)(\d{1,2}:\d{1,2}:\d{2}|\d{1,2}:\d{2})(?!\d)'
    matches = list(re.finditer(ts_regex, text))
    if len(matches) < 3:
        return []

    raw_entries = []
    for i in range(len(matches)):
        ts_str = matches[i].group(1)
        start_idx = matches[i].end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start_idx:end_idx].strip()
        raw_entries.append((ts_str, content))

    songs = []
    for ts_str, raw_text in raw_entries:
        clean_text = raw_text.split('\n')[0].strip()
        if not clean_text or any(x in clean_text.upper() for x in EXCLUDE_SETLIST_KEYWORDS):
            continue

        clean_text = re.sub(r'^[:\s♪・\-\.\]】）)／/|｜￤~～]+', '', clean_text).strip("  ")
        clean_text = re.sub(r'\s*[\(（]?http.*$', '', clean_text).strip("  ")
        if not clean_text: continue

        t = clean_text
        a = ""
        for sep in [' / ', '／', ' - ', ' － ', '：', ' : ', '￤']:
            if sep in clean_text:
                parts = clean_text.split(sep, 1)
                t, a = parts[0].strip("  "), parts[1].strip("  ")
                break

        if not a:
            a = resolve_artist_name(t)

        parts = list(map(int, ts_str.split(':')))
        sec = parts[0] * 3600 + parts[1] * 60 + parts[2] if len(parts) == 3 else parts[0] * 60 + parts[1] if len(parts) == 2 else 0

        songs.append({"title": t, "artist": a, "start": sec})

    songs.sort(key=lambda x: x["start"])
    unique_songs = []
    seen = set()
    for s in songs:
        if (s["start"], s["title"]) not in seen:
            seen.add((s["start"], s["title"]))
            unique_songs.append(s)
    return unique_songs

# ★ コメント欄からセトリを取得する関数
def fetch_setlist_from_comments(youtube, video_id, fallback_members=None):
    """概要欄にセトリがない場合、コメント欄から取得"""
    best_songs = []
    try:
        # 1. 関連度順（上位30件）
        res = youtube.commentThreads().list(
            part="snippet", videoId=video_id, order="relevance",
            maxResults=30, textFormat="plainText"
        ).execute()

        for item in res.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            if re.search(r'\d{1,2}:\d{2}', text):
                songs = parse_setlist_from_text(text, fallback_members=fallback_members)
                if len(songs) > len(best_songs):
                    best_songs = songs

        if len(best_songs) >= 3:
            return best_songs

        # 2. キーワード検索（セトリ、セットリスト、タイムスタンプ）
        for term in ["セットリスト", "セトリ", "タイムスタンプ"]:
            try:
                search_res = youtube.commentThreads().list(
                    part="snippet", videoId=video_id, searchTerms=term,
                    maxResults=5, textFormat="plainText"
                ).execute()
                for item in search_res.get("items", []):
                    text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    if re.search(r'\d{1,2}:\d{2}', text):
                        songs = parse_setlist_from_text(text, fallback_members=fallback_members)
                        if len(songs) > len(best_songs):
                            best_songs = songs
                if len(best_songs) >= 3:
                    break
            except Exception:
                continue

        return best_songs
    except Exception as e:
        print(f"⚠️ [{video_id}] コメント取得エラー: {e}")
        return best_songs

# ★ YouTube Shorts のHTMLから公式音源クレジットを抽出する関数
def コメント(video_id: str) -> Optional[dict]:
    try:
        url = f"https://www.youtube.com/shorts/{video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return None

        html_text = res.text
        # 「曲名 · アーティスト名」の中黒区切りパターン
        m_credit = re.search(r'"content"\s*:\s*"([^"]+?)\s*[·・]\s*([^"]+?)"', html_text)
        if m_credit:
            title = m_credit.group(1).strip("  ")
            artist = m_credit.group(2).strip("  ")
            return {"title": title, "artist": artist, "start": 0}

        # 中黒区切りがない場合のフォールバック（曲名のみ）
        m_label = re.search(r'"label"\s*:\s*"([^"]+?)"', html_text)
        if m_label:
            return {"title": m_label.group(1).strip("  "), "artist": "", "start": 0}

    except Exception as e:
        print(f"⚠️ [{video_id}] 音源抽出エラー: {e}")

    return None

def parse_cover_or_shorts(title, desc, is_short=False, video_id=None):
    """Shorts音源および歌ってみたの単曲メタデータ抽出"""
    if not desc: desc = ""
    clean_lines = [l.strip() for l in desc.split("\n") if not any(b in l.lower() for b in ["http", "channel", "@", "spotify"])]

    # 1. 概要欄キーワード（本家 / Original / Music / 音源）
    for line in clean_lines:
        if re.search(r"^(?:本家様?|Original|Music|音源|楽曲)[:：\s]+(.*)", line, re.I):
            val = re.sub(r"^(?:本家様?|Original|Music|音源|楽曲)[:：\s]+", "", line).strip("  ")
            if " / " in val or "／" in val:
                parts = re.split(r"[/／]", val, 1)
                return [{"title": parts[0].strip("  "), "artist": parts[1].strip("  "), "start": 0}]

    # 2. タイトル形式 (曲名 / アーティスト)
    clean_title = re.sub(r"[\(（\[【][^\)）\]】]*(?:covered|cover|歌ってみた|歌|mv|オリジナル)[^\)）\]】]*[\)）\]】]", "", title, flags=re.I)
    clean_title = re.sub(r"(?:歌ってみた|COVER|Cover|MV)", "", clean_title, flags=re.I).strip("   /／-－_・")

    pattern = r"^(.*?)(?:\s*[/／\-－]\s*)(.*?)$"
    m = re.search(pattern, clean_title, flags=re.I)
    if m:
        t, a = m.group(1).strip("  "), m.group(2).strip("  ")
        if not a: a = resolve_artist_name(t)
        return [{"title": t, "artist": a, "start": 0}]

    # 3. 単曲歌動画でタイトルから取得
    if clean_title and not is_short:
        clean_title = clean_title.strip("  ")
        return [{"title": clean_title, "artist": resolve_artist_name(clean_title), "start": 0}]

    # 4. ★ Shorts かつ概要欄に情報がない場合にWebから公式音源取得
    if is_short and video_id:
        credit = コメント(video_id)
        if credit and credit.get("title") and credit["title"] not in ["1.0", "1.0x", "登録", "再生"]:
            if not credit.get("artist"):
                credit["artist"] = resolve_artist_name(credit["title"])
            return [credit]

    return []

# ==============================================================================
# 3. X (Twitter) 連携処理
# ==============================================================================

def extract_youtube_ids_from_text(text: str) -> List[str]:
    if not text: return []
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
    ]
    yt_ids = []
    for p in patterns:
        yt_ids.extend(re.findall(p, text))
    return list(dict.fromkeys(yt_ids))

def expand_url(short_url: str) -> str:
    try:
        res = requests.head(short_url, allow_redirects=True, timeout=5)
        return res.url
    except Exception:
        return short_url

def fetch_quoted_tweet_text(tweet_url: str) -> str:
    m = re.search(r'(?:twitter\.com|x\.com)\/[^/]+\/status\/(\d+)', tweet_url)
    if not m: return ""
    status_id = m.group(1)
    oembed_url = f"https://publish.twitter.com/oembed?url=https://twitter.com/i/status/{status_id}&omit_script=true"
    try:
        res = requests.get(oembed_url, timeout=5)
        if res.status_code == 200:
            return html.unescape(res.json().get("html", ""))
    except Exception:
        pass
    return ""

def fetch_youtube_ids_from_midori_x() -> List[str]:
    endpoints = [
        f"https://rsshub.app/twitter/user/{TARGET_X_USER}",
        f"https://nitter.net/{TARGET_X_USER}/rss",
        f"https://nitter.cz/{TARGET_X_USER}/rss"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    found_video_ids = set()

    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200: continue

            root = ET.fromstring(res.content)
            items = root.findall('./channel/item')
            if not items: continue

            for item in items:
                desc = item.find('description')
                text = desc.text if desc is not None else ""

                found_video_ids.update(extract_youtube_ids_from_text(text))

                for tco in re.findall(r'https?:\/\/t\.co\/[a-zA-Z0-9]+', text):
                    expanded = expand_url(tco)
                    found_video_ids.update(extract_youtube_ids_from_text(expanded))

                    if re.search(r'(?:twitter\.com|x\.com)\/[^/]+\/status\/\d+', expanded):
                        quoted_text = fetch_quoted_tweet_text(expanded)
                        if quoted_text:
                            found_video_ids.update(extract_youtube_ids_from_text(quoted_text))
                            for q_tco in re.findall(r'https?:\/\/t\.co\/[a-zA-Z0-9]+', quoted_text):
                                found_video_ids.update(extract_youtube_ids_from_text(expand_url(q_tco)))

            if found_video_ids: break
        except Exception:
            continue

    print(f"🐦 @{TARGET_X_USER} のポスト（引用含む）から {len(found_video_ids)} 件のYouTube動画IDを検知")
    return list(found_video_ids)

def fetch_videos_by_ids(youtube, video_ids: List[str], fixed_tags=None, source_label="X告知"):
    if not video_ids: return []
    videos = []
    unique_ids = list(dict.fromkeys(video_ids))

    for i in range(0, len(unique_ids), 50):
        chunk = unique_ids[i:i + 50]
        try:
            res = youtube.videos().list(part='snippet,contentDetails', id=','.join(chunk)).execute()
        except Exception as e:
            print(f"⚠️ YouTube APIエラー: {e}")
            continue

        for v_data in res.get('items', []):
            v_id = v_data['id']
            snip = v_data['snippet']
            desc = snip.get('description', '')
            sec = get_duration_seconds(v_data['contentDetails']['duration'])
            uploader_name = snip.get('channelTitle', '')
            title = snip['title']
            is_short = (0 < sec <= 60)

            cat, kw = analyze_video_tags(title, desc, fixed_tags or [], channel_name=uploader_name, is_short=is_short)

            combined = (title + desc + uploader_name).lower()
            if OWNER_NAME.lower() not in combined and not any(m.lower() in combined for m in kw):
                continue

            auto_songs = []
            cat_set = set(cat)
            if "歌配信" in cat_set or cat_set.intersection({"歌動画", "踊り動画"}):
                auto_songs = parse_setlist_from_text(desc, fallback_members=kw)
                # ★ コメント欄探索
                if not auto_songs and sec > 300:
                    auto_songs = fetch_setlist_from_comments(youtube, v_id, fallback_members=kw)
                if not auto_songs and not is_short:
                    auto_songs = extract_music_metadata(desc) or parse_cover_or_shorts(title, desc, is_short=False, video_id=v_id)
            elif is_short:
                # ★ Shorts音源探索
                auto_songs = parse_cover_or_shorts(title, desc, is_short=True, video_id=v_id)

            videos.append({
                "youtubeId": v_id,
                "title": title,
                "channel": uploader_name,
                "date": snip['publishedAt'][:10],
                "thumbnail": f"https://i.ytimg.com/vi/{v_id}/mqdefault.jpg",
                "category": cat,
                "keywords": kw,
                "tags": [source_label],
                "songs": auto_songs
            })

    return videos

# ==============================================================================
# 4. YouTube プレイリスト取得 & GitHub JSON 更新
# ==============================================================================

def get_uploads_playlist_id(youtube, channel_id):
    try:
        resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
        return resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception:
        return None

def fetch_videos_from_playlist(youtube, playlist_id, channel_name, fixed_tags, auto_tags=None):
    videos = []
    next_page_token = None
    page_count = 0
    print(f"🔍 {channel_name} のプレイリストを取得中... (ID: {playlist_id})")

    while page_count < MAX_PAGES_TO_FETCH:
        try:
            res = youtube.playlistItems().list(
                part='snippet,contentDetails', playlistId=playlist_id,
                maxResults=50, pageToken=next_page_token
            ).execute()
            items = res.get('items', [])
            if not items: break

            v_ids = [it['contentDetails']['videoId'] for it in items]
            v_res = youtube.videos().list(part='contentDetails,snippet', id=','.join(v_ids)).execute()
            details = {v['id']: v for v in v_res.get('items', [])}

            for v_id in v_ids:
                if v_id not in details: continue
                v_data = details[v_id]
                snip = v_data['snippet']
                desc = snip.get('description', '')
                sec = get_duration_seconds(v_data['contentDetails']['duration'])
                uploader_name = snip.get('channelTitle', channel_name)
                is_short = (0 < sec <= 60)

                cat, kw = analyze_video_tags(snip['title'], desc, fixed_tags, channel_name=uploader_name, is_short=is_short)

                # ★ 楽曲解析 & セトリ探索 & Shorts音源探索を確実に配線
                auto_songs = []
                cat_set = set(cat)
                if "歌配信" in cat_set or cat_set.intersection({"歌動画", "踊り動画"}):
                    auto_songs = parse_setlist_from_text(desc, fallback_members=kw)
                    # 概要欄になく、5分以上の長尺ならコメント欄を探索
                    if not auto_songs and sec > 300:
                        print(f"💬 [{v_id}] 概要欄にセトリなし。コメント欄を探索中...")
                        auto_songs = fetch_setlist_from_comments(youtube, v_id, fallback_members=kw)
                    # 単曲歌動画の解析
                    if not auto_songs and not is_short:
                        auto_songs = extract_music_metadata(desc) or parse_cover_or_shorts(snip['title'], desc, is_short=False, video_id=v_id)
                elif is_short:
                    # Shorts 音源の抽出 (video_id を確実に渡す)
                    auto_songs = parse_cover_or_shorts(snip['title'], desc, is_short=True, video_id=v_id)

                videos.append({
                    "youtubeId": v_id,
                    "title": snip['title'],
                    "channel": uploader_name,
                    "date": snip['publishedAt'][:10],
                    "thumbnail": f"https://i.ytimg.com/vi/{v_id}/mqdefault.jpg",
                    "category": cat,
                    "keywords": kw,
                    "tags": auto_tags or [],
                    "songs": auto_songs
                })

            next_page_token = res.get('nextPageToken')
            if not next_page_token: break
            page_count += 1
        except Exception as e:
            print(f"⚠️ {channel_name} (ID: {playlist_id}) 取得エラー: {e}")
            break

    return videos

def update_github_json(new_videos, target_file_path=JSON_FILE_PATH, commit_msg="BOT: Update archive"):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{target_file_path}"
    
    res = requests.get(url, headers=headers)
    existing_videos, existing_sha = [], None
    
    if res.status_code == 200:
        info = res.json()
        existing_sha = info['sha']
        try:
            decoded = base64.b64decode(info['content']).decode('utf-8-sig').strip()
            existing_videos = json.loads(decoded) if decoded else []
        except Exception:
            existing_videos = []

    video_map = {}
    for v in existing_videos:
        vid = v.get("youtubeId")
        if not vid: continue
        cleaned_songs = []
        for s in v.get("songs", []):
            t = s.get("title", "")
            a = s.get("artist", "")
            if not any(bad in t.lower() or bad in a.lower() for bad in ["http", "channel", "@", "%e7%b7%91%e4%bb%99"]):
                if t not in ["1.0", "1.0x"]:
                    cleaned_songs.append(s)
        v["songs"] = cleaned_songs
        video_map[vid] = v

    for nv in new_videos:
        vid = nv.get("youtubeId")
        if not vid: continue
        if vid in video_map:
            if video_map[vid].get("songs") and not nv.get("songs"):
                nv["songs"] = video_map[vid]["songs"]
            if video_map[vid].get("tags") and not nv.get("tags"):
                nv["tags"] = video_map[vid]["tags"]
            video_map[vid].update(nv)
        else:
            video_map[vid] = nv

    all_videos = list(video_map.values())
    if not all_videos: return

    # アーティスト名の再補完（手動辞書・全体DB）
    for video in all_videos:
        for s in video.get("songs", []):
            current_artist = s.get("artist", "").strip()
            if not current_artist or current_artist in ["Unknown Artist", "sora"]:
                raw_title = s.get("title", "").strip()
                s["artist"] = resolve_artist_name(raw_title)

    final = sorted(all_videos, key=lambda x: x.get('date', ''), reverse=True)
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(json.dumps(final, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8'),
        "sha": existing_sha
    }
    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        print(f"🚀 {target_file_path} の更新が完了しました。")
    else:
        print(f"❌ {target_file_path} 更新失敗: {put_res.status_code}")

# ==============================================================================
# 5. エントリーポイント
# ==============================================================================
def main():
    if not YOUTUBE_API_KEY or not GITHUB_TOKEN:
        print("❌ APIキーまたはGITHUB_TOKENが設定されていません。")
        return

    print("📚 アーティスト辞書を構築中...")
    load_artist_db()

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    fetched_official_videos = []

    # 1. 公式チャンネル通常アップロード
    for ch in CHANNELS:
        pid = get_uploads_playlist_id(youtube, ch['id'])
        if pid:
            fetched_official_videos.extend(fetch_videos_from_playlist(youtube, pid, ch['name'], ch.get('fixed_tags', [])))

    # 2. 特殊プレイリスト
    for pl in EXTRA_PLAYLISTS:
        try:
            pl_name = pl.get('name', OWNER_NAME)
            fetched_official_videos.extend(fetch_videos_from_playlist(
                youtube, pl['id'], pl_name, pl.get('fixed_tags', []), auto_tags=pl.get('auto_tags')
            ))
        except Exception as e:
            print(f"⚠️ プレイリストスキップ: {e}")

    # 3. @midori_2434 のポスト & 引用ポストから動画を自動取得
    print(f"\n🐦 @{TARGET_X_USER} のXポストから告知・引用動画を探索中...")
    x_video_ids = fetch_youtube_ids_from_midori_x()
    fetched_external_videos = []
    if x_video_ids:
        print(f"🔍 検出された {len(x_video_ids)} 件の動画をYouTubeから取得・解析中...")
        fetched_external_videos = fetch_videos_by_ids(
            youtube, x_video_ids, fixed_tags=["外部動画", "告知"], source_label="Twitter告知"
        )

    # 4. それぞれ適切なJSONファイルへ保存
    if fetched_official_videos:
        print("\n💾 公式アーカイブ (archive_videos.json) を更新中...")
        update_github_json(
            fetched_official_videos,
            target_file_path=JSON_FILE_PATH,
            commit_msg="BOT: Update official archive"
        )

    if fetched_external_videos:
        print(f"\n💾 外部連携動画 ({FINAL_JSON_PATH}) を更新中...")
        update_github_json(
            fetched_external_videos,
            target_file_path=FINAL_JSON_PATH,
            commit_msg=f"BOT: Update external videos from @{TARGET_X_USER}"
        )

    print("\n✅ 全処理が完了しました。")

if __name__ == "__main__":
    main()
      
