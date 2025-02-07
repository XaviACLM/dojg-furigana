"""
export relevant libraries from anki, as .apkg, with all extra information, to this folder.
"""

from typing import Optional, List
import regex as re
from furigana.furigana import split_furigana, item_html
from itertools import islice, chain
from util import deterministic_hash
import os
from datetime import datetime
from random import randint

from deck_wrangling import ApkgAsAnki
from tts import TTSManager, VoicevoxManager
from special_punctuation_handling import handle_nakaguro, handle_brackets


kana_matcher = re.compile(r"([\p{IsHira}\p{IsKatakana}ー–—]+)", re.UNICODE)
kanji_matcher = re.compile(r"([\p{IsHan}]+)", re.UNICODE)
notkanji_matcher = re.compile(r"([^\p{IsHan}]+)", re.UNICODE)
japanese_chars = r"[\p{IsHira}\p{IsKatakana}\p{IsHan}・、。ー「」『』【】〈〉《》〔〕［］｢｣〖〗【】〘〙〚〛〝〞〟〰〽〿–—‘’“”…‥･〳〴〵〶〷〼〽〾〿]"
jap_matcher = re.compile(r"(" + japanese_chars + "+)", re.UNICODE)
jap_maybe_cloze_matcher_str = (
    r"(" + japanese_chars + r'+)|<span class="cloze">(' + japanese_chars + r"+)</span>"
)  # old, before the cloze symbol matcher
# jap_maybe_cloze_matcher_str = r'(' + japanese_chars + r'+)|<span class="cloze">(' + japanese_chars + r'+|○○)</span>' #should not be necessary anymore
jap_maybe_cloze_matcher = re.compile(jap_maybe_cloze_matcher_str, re.UNICODE)
jap_cloze_matcher = re.compile(r"(?:" + jap_maybe_cloze_matcher_str + ")+", re.UNICODE)
cloze_limits_matcher = re.compile('<span class="cloze">|</span>')
cloze_inner_matcher = re.compile('<span class="cloze">.*?</span>')
zwsp = "\u200b"  # zero width space


substitutions = {
    "逹": "達",  # miswritten character
    "晚": "晩",  # miswritten character
    "友逢": "友達",  # mistyped. 友逢 is correct but in usage it is clear that 友達 is intended
    "意昧": "意味",  # mistype, 意昧 is not a word
    "鷗": "鴎",  # not wrong, but mecab has trouble with it, presumably due to being kyujitai. we select the shinjitai form. this is the 'kamome' in 'kamomedai', meaning 'seagull'
    "傾": "斜め",  # outdated kanji
    "頸": "頚",  # again we keep it shinjitai
    "ヶ月": "箇月",  # ヶ is an abbreviation of 箇 (looks like the top bit) but it's awkward to put furigana on it
    "悲しみした": "悲しみました",  # mistype
}

forbidden_words = [
    "芥川龍之介『夢』",  # intensely archaic language, several kanji within give mecab trouble. not worth the effort
]

# w-okada it still gets some stuff wrong, like
# クラス(の中)で
# reads naka as chou
# 一番頭がいい。
# instead of ichiban atama ga ii, reads ichi bangashira ga ii (????)
# 明後日(asatte) is also wrong... mecab fails to read it from the dict
# i don't know, mecab just has its limits


def add_furigana_with_splits(sentence_split: List[str], furigana_size=0.8) -> str:
    sentence_text = "".join(sentence_split)

    # replace spaces with zero width space to avoid mecab deleting them
    sentence_text = sentence_text.replace(" ", zwsp)

    mecab_full = split_furigana(sentence_text)

    l = 0
    i = -1
    final_html_splits = []
    final_html_piece = []
    mecab_iter = iter(mecab_full)
    for sentence_part in sentence_split:
        l += len(sentence_part)
        while l > 0:
            i += 1
            # returns a tuple w/ writing and, if different, reading
            mecab_part = next(mecab_iter)
            mecab_len = len(mecab_part[0])
            l -= mecab_len
            if l >= 0:
                final_html_piece.append(
                    item_html(mecab_part, furigana_size=furigana_size)
                )
        if l == 0:
            final_html_splits.append("".join(final_html_piece))
            final_html_piece = []
        elif l < 0:  # else
            overshoot = -l
            match mecab_part:
                case (kanji, hiragana):
                    pre_cloze_kanji, post_cloze_kanji = (
                        kanji[:-overshoot],
                        kanji[-overshoot:],
                    )
                    f = len(pre_cloze_kanji) / len(kanji)

                    # careful! shitty approximation! not real!
                    cutoff = int(f * len(hiragana))
                    pre_cloze_furigana, post_cloze_furigana = (
                        hiragana[:cutoff],
                        hiragana[cutoff:],
                    )
                    pre_cloze = item_html(
                        (pre_cloze_kanji, pre_cloze_furigana),
                        furigana_size=furigana_size,
                    )
                    post_cloze = item_html(
                        (post_cloze_kanji, post_cloze_furigana),
                        furigana_size=furigana_size,
                    )
                case (hiragana,):
                    pre_cloze, post_cloze = hiragana[:-overshoot], hiragana[-overshoot:]
            final_html_piece.append(pre_cloze)
            final_html_splits.append("".join(final_html_piece))
            final_html_piece = []
            final_html_piece.append(post_cloze)

    return final_html_splits


def empty_clozes(sentence_html: str) -> str:
    blank_cloze = '<span class="cloze">○○</span>'
    return re.sub(cloze_inner_matcher, blank_cloze, sentence_html)


class MultipleAnnotator:
    def __init__(self):
        self.items = []

    def process(self, item):
        if item in self.items:
            i = 1
            item = f"{item} ({i})"
            while item in self.items:
                i += 1
                item = f"{item} ({i})"
        self.items.append(item)
        return item


class FieldProcessor:
    def __init__(
        self, tts_manager: TTSManager, n_cards=None, add_furigana=True, add_audio=True
    ):
        self.tts_manager = tts_manager
        self.start_time = datetime.now()

        self.counter = 0
        self.counter_generated = 0
        self.n_cards = n_cards

        self.add_furigana = add_furigana
        self.add_audio = add_audio

        self.multiple_annotator = MultipleAnnotator()

    def fix_html_snafus(self, field: str):
        # some fields are all wrapped in a green for some reason (so the first green is double nested)
        # i assume this is an error, so we just remove it
        if field.startswith('<span class="green"><span class="green">'):
            field = field[20:-7]
        # same for this. random open color spans (never closed)
        field = field.replace('<span style="color:#0055FF; ">', "")
        # and again
        if field.endswith("<span style=\"font-family:'ＭＳ 明朝',serif; \">。</span>"):
            field = field[:-50] + "。"
        return field

    def add_furigana_and_audio_to_field(self, field: str, skip_furigana=False):
        # we switch out em spaces for two normal spaces, as em spaces give mecab trouble
        field = field.replace("\u2003", "  ")

        # there's a weird divisor - \u3000 - in there. we just ignore it with . for simplicity
        match = re.match(r'(?:<span class="green">\((.*)\)\..</span>)?(.*)', field)
        tag = match.group(1)
        # tag will be added later. if tag is None then the green span is not there at all (error?)
        sentence_html = match.group(2)

        cloze_split = re.split(cloze_limits_matcher, sentence_html)

        if skip_furigana:
            furiganized_html = sentence_html
        else:
            cloze_delimiters = re.findall(cloze_limits_matcher, sentence_html)

            furiganized_cloze_split = add_furigana_with_splits(cloze_split)
            furiganized_html = "".join(
                chain(
                    *zip(furiganized_cloze_split, cloze_delimiters),
                    [furiganized_cloze_split[-1]],
                )
            )

        # generate sentence audio
        sentence_text = "".join(cloze_split)

        # in places where it gives different options, always pick the first for audio
        sentence_readable_text = handle_brackets(sentence_text)
        sentence_readable_text = handle_nakaguro(sentence_readable_text)

        sentence_id = deterministic_hash(sentence_readable_text)[:32]
        sentence_filename = f"dojg_audio.{sentence_id}.mp3"
        sentence_audio_path = f"dojg_sentence_audio\\{sentence_filename}"

        # this fails sometimes, though the program keeps running
        # an issue w tts. not a problem, we just do a few extra passes
        # (audio is never regenerated and there appear to be no corrupted files)
        self.counter += 1
        if self.add_audio and not os.path.exists(sentence_audio_path):
            self.counter_generated += 1
            if self.gender is not None:
                speaker = randint(0, 2) + 3 * (self.gender == "female")
            else:
                speaker = None

            self.tts_manager.create_audio(
                sentence_readable_text,
                speed=0.8,
                file_dir="dojg_sentence_audio",
                file_name=sentence_filename,
                voice_idx=speaker,
            )
            if self.n_cards is not None:
                time_now = datetime.now()
                avg_gen_time = (time_now - self.start_time) / self.counter_generated
                cards_left = self.n_cards - self.counter
                approx_time = avg_gen_time * cards_left
                approx_ending_time = time_now + approx_time
                print(
                    f"{self.counter} / {self.n_cards} - ETA {approx_ending_time.strftime('%H:%M')}"
                )

        audio_html = f"[sound:{sentence_audio_path}]"

        # add tag back + audio
        final_html = (
            ((audio_html + " ") if self.add_audio else "")
            + ("" if tag is None else f'<span class="green">({tag}).</span>  ')
            + furiganized_html
        )

        return final_html

    def furiganize_fields(self, note):
        # this doesn't entirely fit with the name of the function but does agree with the spirit of it
        # necessary preprocessing that either fixes mistakes in the text or at least doesn't change the meaning
        # necessary for the morphological parser to be able to handle the text

        fields = note.fields

        # replace personal note
        fields[0] = fields[0].replace('e-stem','エの形')

        for original, substitute in substitutions.items():
            for i, field in enumerate(fields):
                fields[i] = field.replace(original, substitute)

        if "male" in fields[1] and "suffix" not in fields[1]:
            self.gender = "female" if "female" in fields[1] else "male"
        else:
            self.gender = None

        fields[0] = self.multiple_annotator.process(
            fields[0]
        )  # add (i) tag to name if repeated

        # select the example sentence fields
        # translation is immediately after, cloze is immediately before the first sentence
        for idx_field, field in islice(enumerate(fields), 9, 41, 2):
            if not field:
                break
            has_forbidden_words = any((word in field for word in forbidden_words))
            field = self.fix_html_snafus(field)
            field = self.add_furigana_and_audio_to_field(
                field, skip_furigana=has_forbidden_words or not self.add_furigana
            )
            fields[idx_field] = field

        # add furigana to empty cloze field
        fields[8] = empty_clozes(fields[9])


"""
from MeCab import Tagger
tagger = Tagger()
items= ['やるせない','遣る瀬無い','遣る瀬ない','やる瀬ない']
for item in items:
    print(tagger.parse(item))
print(jjsj)
#hiragana gets parsed correctly (hell yeah)
"""

"""
with ApkgAsAnki(
    "Dictionary of Japanese Grammar Blueprint", proceed_if_unzipped=True
) as dojg_deck:

    def inspect(note):
        print(note.fields[0])
        print("\n".join(note.fields[8:13]))
        print("\n"*1)

    dojg_deck.apply_to_notes(inspect)
"""

tts_manager = VoicevoxManager()
with ApkgAsAnki(
    "Dictionary of Japanese Grammar Blueprint", proceed_if_unzipped=True
) as dojg_deck:
    processor = FieldProcessor(
        tts_manager, n_cards=5383, add_furigana=True, add_audio=True
    )

    """
    # doesn't work
    # whatever, we can include it by exporting
    audio_dir = 'dojg_sentence_audio' 
    for audio_file in os.listdir(audio_dir)[:50]:
        path = os.path.join(audio_dir, audio_file)
        maybe_renamed = dojg_deck.col.media.add_file(path)
        assert maybe_renamed == audio_file
    """
  
    dojg_deck.apply_to_notes(processor.furiganize_fields)
    print(processor.counter)

    dojg_deck.commit_and_save(with_name="Dictionary of Japanese Grammar +F +A")


with ApkgAsAnki(
    "Dictionary of Japanese Grammar Blueprint", proceed_if_unzipped=True
) as dojg_deck:
    processor = FieldProcessor(
        tts_manager, n_cards=5383, add_furigana=True, add_audio=False
    )
    dojg_deck.apply_to_notes(processor.furiganize_fields)
    dojg_deck.commit_and_save(with_name="Dictionary of Japanese Grammar +F")


with ApkgAsAnki(
    "Dictionary of Japanese Grammar Blueprint", proceed_if_unzipped=True
) as dojg_deck:
    processor = FieldProcessor(
        tts_manager, n_cards=5383, add_furigana=False, add_audio=True
    )
    dojg_deck.apply_to_notes(processor.furiganize_fields)
    dojg_deck.commit_and_save(with_name="Dictionary of Japanese Grammar +A")


with ApkgAsAnki(
    "Dictionary of Japanese Grammar Blueprint", proceed_if_unzipped=True
) as dojg_deck:
    processor = FieldProcessor(
        tts_manager, n_cards=5383, add_furigana=False, add_audio=False
    )
    dojg_deck.apply_to_notes(processor.furiganize_fields)
    dojg_deck.commit_and_save(with_name="Dictionary of Japanese Grammar")
