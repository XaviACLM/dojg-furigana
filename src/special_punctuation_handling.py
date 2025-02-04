# this whole file has some very terrible code
#  of note okurigana handling and hiragana_casual_formal_pairs should clearly be unified
#   and the first attempted to follow some kind of structure but the second was completely hacked together
#   which is a shame because the second is the more general one (albeit also less optimized)
#  moreover it is coincidence that the exceptions list contains only sentences whose nakaguro are all exceptions
# both of these problems are relatively easy fixes but i do not believe the result would be very general either
# ultimately this serves only to handle those nakaguro in the dojg
# and will require tweaking if any new corpus of significant size is thrown at it
# a proper solution likely requires more expert handling of a morphological parser

from collections import defaultdict

import numpy as np
import regex as re

kanji_matcher = re.compile(r"([\p{IsHan}]+)", re.UNICODE)
katakana_matcher = re.compile(r"([\p{IsKatakana}ー–—]+)", re.UNICODE)

kana_chart = np.array(
    [
        ["あ", "い", "う", "え", "お"],
        ["か", "き", "く", "け", "こ"],
        ["が", "ぎ", "ぐ", "げ", "ご"],
        ["さ", "し", "す", "せ", "そ"],
        ["ざ", "じ", "ず", "ぜ", "ぞ"],
        ["た", "ち", "つ", "て", "と"],
        ["だ", "ぢ", "づ", "で", "ど"],
        ["な", "に", "ぬ", "ね", "の"],
        ["は", "ひ", "ふ", "へ", "ほ"],
        ["ば", "び", "ぶ", "べ", "ぼ"],
        ["ぱ", "ぴ", "ぷ", "ぺ", "ぽ"],
        ["ま", "み", "む", "め", "も"],
        ["や", "", "ゆ", "", "よ"],
        ["ら", "り", "る", "れ", "ろ"],
    ]
).T
# わ, を, ん plus minikana

okurigana_casual_to_formal = defaultdict(list)

# copula
okurigana_casual_to_formal["だ"].append("です")

# adjectives
for i_kana in kana_chart[1]:
    if not i_kana:
        continue
    casual, formal = i_kana, i_kana + "です"
    okurigana_casual_to_formal[casual].append(formal)
    casual = i_kana + "だ"
    okurigana_casual_to_formal[casual].append(formal)
# -shii adjectives
okurigana_casual_to_formal["しい"].append("しいです")
okurigana_casual_to_formal["しいだ"].append("しいです")
# some with longer okurigana
okurigana_casual_to_formal["きい"].append("きいです")
okurigana_casual_to_formal["かい"].append("かいです")

# other copula stuff

# suru
okurigana_casual_to_formal["する"].append("します")
okurigana_casual_to_formal["しんだ"].append("しみました")

# godan nonpast
for casual, formal in zip(kana_chart[2], kana_chart[1]):
    if not (casual and formal):
        continue
    formal += "ます"
    okurigana_casual_to_formal[casual].append(formal)
okurigana_casual_to_formal["まる"].append("まります")
okurigana_casual_to_formal["かる"].append("かります")
okurigana_casual_to_formal["わる"].append("わります")
okurigana_casual_to_formal["こえる"].append("こえます")

# ichidan nonpast
okurigana_casual_to_formal["る"].append("ます")
for i_kana in kana_chart[1]:
    if not i_kana:
        continue
    casual, formal = i_kana + "る", i_kana + "ます"
    okurigana_casual_to_formal[casual].append(formal)
for e_kana in kana_chart[3]:
    if not e_kana:
        continue
    casual, formal = e_kana + "る", e_kana + "ます"
    okurigana_casual_to_formal[casual].append(formal)
okurigana_casual_to_formal["かける"].append("かけます")

# ku ta-form
okurigana_casual_to_formal["いた"].append("きました")
# u-(tsu)-ru ta-form
okurigana_casual_to_formal["った"].append("いました")
okurigana_casual_to_formal["った"].append("りました")
# (nu)-(bu)-mu ta-form
okurigana_casual_to_formal["んだ"].append("みました")
# iku ta-form. this is irregular but i don't think it can even be triggered other than iku?
okurigana_casual_to_formal["った"].append("きました")

# ichidan ta-form
okurigana_casual_to_formal["た"].append("ました")
for i_kana in kana_chart[1]:
    if not i_kana:
        continue
    casual, formal = i_kana + "た", i_kana + "ました"
    okurigana_casual_to_formal[casual].append(formal)
for e_kana in kana_chart[3]:
    if not e_kana:
        continue
    casual, formal = e_kana + "た", e_kana + "ました"
    okurigana_casual_to_formal[casual].append(formal)
# owaru
okurigana_casual_to_formal["わった"].append("わりました")
# longer okurigana, passives, causatives, etc
for pre in ["まれ", "らせ", "され", "られ", "べられ", "まし", "かせ", "わせ"]:
    casual, formal = pre + "た", pre + "ました"
    okurigana_casual_to_formal[casual].append(formal)

# various negative ta-forms
okurigana_casual_to_formal["なかった"].append("ませんでした")
okurigana_casual_to_formal["べなかった"].append("べませんでした")
okurigana_casual_to_formal["らなかった"].append("りませんでした")

# negative form
okurigana_casual_to_formal["わない"].append("いません")
for a_kana, i_kana in zip(kana_chart[0], kana_chart[1]):
    if not (a_kana and i_kana):
        continue
    casual, formal = a_kana + "ない", i_kana + "ません"
    okurigana_casual_to_formal[casual].append(formal)
okurigana_casual_to_formal["からない"].append("かりません")
# negative potential
for e_kana in kana_chart[3]:
    if not e_kana:
        continue
    casual, formal = e_kana + "ない", e_kana + "ません"
    okurigana_casual_to_formal[casual].append(formal)
# ichidan potential
okurigana_casual_to_formal["えられない"].append("えられません")
# chigainai / chigaimasen
okurigana_casual_to_formal["いない"].append("いません")
# nai / nai desu
okurigana_casual_to_formal["ない"].append("ないです")
# nai / arimasen
for pre in ["しく", "じゃ", "い", "く"]:
    casual, formal = pre + "ない", pre + "ありません"
    okurigana_casual_to_formal[casual].append(formal)
# negative kuru
okurigana_casual_to_formal["ない"].append("ません")

# don't really get this one
# ［田中さんが食べた］ステーキは高かった・高かったです。
okurigana_casual_to_formal["かった"].append("かったです")

hiragana_casual_formal_pairs = [
    ("だ", "です"),
    ("", "です"),
    (
        "です",
        "だ",
    ),  # appears reversed sometimes. assuming intentional, we keep the first
    ("る", "ます"),
    # ('いる','います'),
    ("る", "ります"),
    ("く", "きます"),
    # ('ある','あります'),
    ("た", "ました"),
    # ('した','しました'),
    # ('あげた','あげました'),
    ("なった", "なりました"),
    ("らった", "もらいました"),
    ("ない", "ありません"),
    ("よう", "あげましょう"),
    ("なる", "なります"),
    ("しまった", "しまいました"),
    ("ない", "ません"),
    # ('かもしれない','かもしれません),
    ("する", "します"),
    ("らない", "りません"),
    ("じゃ", "では"),
    ("った", "りました"),
    ("おいた", "おきました"),  # oku is irregular apptly
    ("んだ", "みました"),
    ("なかった", "ませんでした"),
]
for i, (elem_1, elem_2) in enumerate(hiragana_casual_formal_pairs):
    hiragana_casual_formal_pairs[i] = (
        elem_1,
        elem_2,
        re.compile(f"(.*){elem_1}・\\1{elem_2}"),
        re.compile(f".*{elem_2}"),
    )

other_pairs = [
    ("へ", "に"),
    ("ん", "の"),  # kind of
    ("を", "が"),  # for tabetai mostly
    ("を", "に"),
    ("にだけ", "だけに"),
    ("でだけ", "だけで"),
    ("だった", "でした"),
    ("だろう", "でしょう"),
    ("でしょう", "だろう"),  # flipped sometimes
    ("なの", "である"),
    ("すれば", "すると"),
    ("いつも", "必ずしも"),
    ("こと", "の"),
]

nakaguro_exceptions = [
    "本日、川上弘美『椰子・椰子』を読了。なるほど面白い本だ。",
    "「思うに、快楽に耽る人生ほど快楽から遠いものはない。」ージョン・D・ロックフェラー2世",
    "不正軽油の製造・販売・使用は、極めて悪質な脱税行為である。のみならず、ディーゼル車の排気ガスは大気中の有害物質を増加させるなど、環境汚染の原因にもなっている。",
    "ご相談・ご意見・ご質問などがありましたら、下記へお知らせ願います。",
    "こんな機能があるといい、こんな情報が欲しいといったご意見・ご要望がありましたら、下記のアドレスに電子メールでお知らせ下さい。",
    "このプロジェクト管理ソフトの新バージョンでは、これまで日単位で行われていた計画と管理を時間・分単位で行えるようになった。",
    "技術者は単に技術の進歩の推進者であるのみならず、人類・社会に及ぼす技術の影響についても強い責任感を持つ自律的な行動者であるべきである。",
    "懲戒処分基準によると、教職員が酒酔い運転で死亡・重傷事故を起こした場合は免職になる。",
    "日本語教育のめざましい進歩の裏には、日本語教育者・研究者の並々ならぬ努力があったことは、想像にかたくありません。",
    "ジャッキー・チェンは、アクションにかけては右に出る者がいない俳優である。",
    "いかなる団体・個人についても、その意図や理由のいかんに関わらず、ここにある画像の転載・再配布等は許可しません。",
    "大学の図書館は、その大学の学生・教職員であるなしに関わらず閲覧できるのが普通だ。",
    "このオンラインゲームは、性別・年齢に関わらず誰でも楽しむことができます。",
    "情報リスクマネジメントという視点で、ビジネスの根幹をなす情報システムを評価・管理することが必須だ。",
    "阪神・淡路大震災では、住宅倒壊により何千人もの命が一瞬のうちに奪われた。",
    "大学教育の目的は、一つには幅広い教養と専門的な知識・能力を授けること、一つには社会に貢献する指導者を育成することだ。",
    "賞味期限のある食品類は開封・未開封の如何に関わらず返品対象外となります。",
    "半身・淡路大震災の時は見るからに新聞記者らしい人たちが大勢写真を撮っていた。",
    "このショールームでは住宅向けのタイル・健在を展示しております。",
]


def handle_nakaguro(sentence_text):
    if sentence_text in nakaguro_exceptions:
        return sentence_text  # we can do this b/c none of the exceptions contain other troublesome nakaguro

    nakaguro_split = sentence_text.split("・")
    for piece_index in range(len(nakaguro_split) - 1):
        preceding_text, following_text = nakaguro_split[piece_index : piece_index + 2]

        if re.fullmatch(katakana_matcher, preceding_text[-1]) and re.fullmatch(
            katakana_matcher, following_text[0]
        ):
            # place the flag so we remember to not delete this nakaguro
            nakaguro_split[piece_index + 1] = "・" + following_text
            continue

        following_kanji_match = re.match(kanji_matcher, following_text)

        if following_kanji_match:
            following_kanji = following_kanji_match.group(0)

            back_idx = preceding_text.rfind(following_kanji)

            if back_idx != -1:
                preceding_okurigana = preceding_text[back_idx + len(following_kanji) :]
                following_tail = following_text[len(following_kanji) :]

                valid_following_okurigana = okurigana_casual_to_formal[
                    preceding_okurigana
                ]
                for following_okurigana in valid_following_okurigana:
                    if following_tail.startswith(following_okurigana):
                        break
                else:
                    following_okurigana = None
                if following_okurigana is not None:
                    nakaguro_split[piece_index + 1] = re.sub(
                        f".*{following_okurigana}", "", following_text, count=1
                    )
                    continue

        sentence_part = preceding_text + "・" + following_text
        for casual, formal, matcher, tail_matcher in hiragana_casual_formal_pairs:
            if re.search(matcher, sentence_part):
                break
        else:
            tail_matcher = None
        if tail_matcher is not None:
            nakaguro_split[piece_index + 1] = re.sub(
                tail_matcher, "", following_text, count=1
            )
            continue

        for p1, p2 in other_pairs:
            if preceding_text.endswith(p1) and following_text.startswith(p2):
                break
        else:
            p2 = None
        if p2 is not None:
            nakaguro_split[piece_index + 1] = re.sub(p2, "", following_text, count=1)
            continue

    sentence_text = "".join(nakaguro_split)
    return sentence_text


bracket_matcher = re.compile(r"\{(.*?)[/・].*?\}")


def handle_brackets(sentence_text):
    return re.sub(bracket_matcher, lambda m: m.group(1), sentence_text)
