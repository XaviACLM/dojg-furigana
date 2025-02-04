import subprocess
import asyncio
import os
import atexit
from random import randint
import requests
import time

from voicevox import Client as VoicevoxClient

from metaclasses import TransientSingleton
from timed_resource_manager import TimedResourceManager


VOICEVOX_EXE_PATH = os.path.join(
    "C:",
    os.sep,
    "Program Files",
    "voicevox-windows-directml-0.22.3",
    "VOICEVOX",
    "vv-engine",
    "run.exe",
)
VOICEVOX_VOICES = [0, 13, 14, 30, 81]

W_OKADA_TTS_DIR = os.path.join("C:", os.sep, "Program Files", "w-okada", "main")
W_OKADA_TTS_EXE = os.path.join(W_OKADA_TTS_DIR, "main.exe")

VOICEPEAK_VOICES = [  # default speaking params for some extra character (very mild)
    ("Japanese Male 1", {"happy": 50}),
    ("Japanese Male 2", dict()),
    ("Japanese Male 3", {"angry": 50}),
    ("Japanese Female 1", {"happy": 50}),
    ("Japanese Female 2", dict()),
    ("Japanese Female 3", {"angry": 50}),
]
"""
                    "Asumi Shuo",
                    "Asumi Ririse",
                    "Frimomen",
                    "Tohoku Zunko",
                    "Zundamon",
                    "Jashinchan",
                    "Japanese Male Child",
                    "Japanese Female Child",
                    "Japanese Male4", # not a typo
                    "Japanese Female4", # not a typo
                    "小春六花",
                    "東北きりたん"
                    ]
"""

VOICEPEAK_DIR = os.path.join("C:", os.sep, "Program Files", "Voicepeak")
VOICEPEAK_EXE = os.path.join(CRACKED_VOICEPEAK_DIR, "voicepeak.exe")


class VoicevoxInterface(TimedResourceManager, metaclass=TransientSingleton):
    def _start_resource(self):
        self._process = subprocess.Popen([VOICEVOX_EXE_PATH])

    def _stop_resource(self):
        self._process.terminate()
        self._process.wait()
        self._process = None

    def _process_request(self, sentence, speaker_id):
        return asyncio.run(self._process_request_async(sentence, speaker_id))

    async def _process_request_async(self, sentence, speaker_id):
        async with VoicevoxClient() as client:
            audio_query = await client.create_audio_query(sentence, speaker=speaker_id)
            return await audio_query.synthesis(speaker=speaker_id)


class WOkadaInterface(TimedResourceManager, metaclass=TransientSingleton):
    startup_time = 15
    port = 19000
    base_url = f"http://localhost:{port}"

    def _start_resource(self):
        self._process = subprocess.Popen(
            W_OKADA_TTS_EXE + " cui --https false --no_cui true", cwd=W_OKADA_TTS_DIR
        )
        timeout = 60
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise Exception(
                    "WOkada TTS api has spent over a minute trying to set up. Very likely the process has failed."
                )

            try:
                response = requests.get(f"{self.base_url}/api/hello")
                if response.status_code == 200:
                    # running!
                    break
                else:
                    continue  # so idiomatic
            except requests.RequestException as e:
                continue

            time.sleep(1)

    def _stop_resource(self):
        self._process.terminate()
        self._process.wait()
        self._process = None

    def _process_request(self, request_payload):
        url = f"{self.base_url}/api/tts-manager/operation/generateVoice"
        return requests.post(url, json=request_payload).content


class TTSManager:
    def __init__(self):
        self.voice_use_counts = [0] * self.amt_voices

    @property
    def amt_voices(self):
        raise NotImplementedError()

    def _select_voice_idx(self):
        # randomly selects voice from 0-self.amt_voices, but making sure to keep it fairly balanced
        max_diff = 5
        if max(self.voice_use_counts) - min(self.voice_use_counts) >= max_diff:
            voice_idx = min(
                range(self.amt_voices), key=self.voice_use_counts.__getitem__
            )
        else:
            voice_idx = randint(0, self.amt_voices - 1)
        self.voice_use_counts[voice_idx] += 1
        return voice_idx

    def _get_voice_by_idx(self, voice_idx):
        raise NotImplementedError()

    def _create_audio(self, sentence, voice, speed, output_path):
        raise NotImplementedError()

    def create_audio(
        self, sentence, voice_idx=None, speed=1, file_dir=".", file_name=None
    ):
        voice_idx = voice_idx if voice_idx is not None else self._select_voice_idx()
        voice = self._get_voice_by_idx(voice_idx)
        file_name = file_name or str(int(1000 * time.time()))
        if not file_name.endswith(".wav"):
            file_name += ".wav"
        file_path = os.path.join(file_dir, file_name)

        self._create_audio(sentence, voice, speed, file_path)

        return file_name[:-4]  # file id


class WOkadaManager(TTSManager, metaclass=TransientSingleton):
    def __init__(self, timeout=30):
        super().__init__()
        self.interface = WOkadaInterface(timeout=timeout)
        atexit.register(self.interface.shutdown)

    @property
    def amt_voices(self):
        return 4

    def _get_voice_by_idx(self, voice_idx):
        return voice_idx

    def _create_audio(self, sentence, voice, speed, output_path):
        request_payload = {
            "voice_character_slot_index": voice,
            "reference_voice_slot_index": 98,  # we keep our samples in the 98th slot
            "text": sentence,
            "language": "all_ja",
            "speed": speed,
            "cutMethod": "Slice by every punct",
        }

        data = self.interface.handle_request(request_payload)

        with open(output_path, "wb") as f:
            f.write(data)


class VoicevoxManager(TTSManager, metaclass=TransientSingleton):
    def __init__(self, timeout=30):
        super().__init__()
        self.interface = VoicevoxInterface(timeout=timeout)
        atexit.register(self.interface.shutdown)

    @property
    def amt_voices(self):
        return len(VOICEVOX_VOICES)

    def _get_voice_by_idx(self, voice_idx):
        return VOICEVOX_VOICES[voice_idx]

    def _create_audio(self, sentence, voice, speed, output_path):
        if speed != 1:
            raise ValueError(
                "Can't handle speeds other than 1 in voicevox (might be possible, just didn't check)"
            )

        data = self.interface.handle_request(sentence, voice)

        with open(output_path, "wb") as f:
            f.write(data)


class VoicepeakManager(TTSManager, metaclass=TransientSingleton):
    @property
    def amt_voices(self):
        return len(VOICEPEAK_VOICES)

    def _get_voice_by_idx(self, voice_idx):
        return VOICEPEAK_VOICES[voice_idx]

    def _create_audio(self, sentence, voice, speed, output_path):
        speed = int(speed * 100)
        if not 50 <= speed <= 200:
            raise ValueError(
                "Voicepeak only supports speed values ranging from 0.5 to 2."
            )
        if len(sentence) > 140:
            raise Exception(
                "Voicepeak cannot process sentences longer than 140 characters."
            )

        narrator, emotion = voice

        emotion_arg = (
            "-e " + ",".join((f"{key}={value}" for key, value in emotion.items()))
            if emotion
            else ""
        )

        command = f'{VOICEPEAK_EXE} --speed {speed} --narrator "{narrator}" {emotion_arg} --say "{sentence}" --out "{output_path}"'

        result = subprocess.run(command, encoding="utf-16")


if __name__ == "__main__":
    lines = """散々な思い出は悲しみを穿つほど
やるせない恨みはアイツのために
置いてきたのさ
あんたらわかっちゃないだろ
本当に傷む孤独を
今だけ箍外してきて
怒りよ今 悪党ぶっ飛ばして
そりゃあ愛ある罰だ
もう眠くはないや ないやないや
もう悲しくないさ ないさ
そう 怒りよ今 悪党蹴り飛ばして
そりゃあ愛への罰だ
もう眠くはないな ないなないな
もう寂しくないさ ないさ""".split("\n")
    manager = VoicepeakManager()
    for voice in range(manager.amt_voices):
        for i, line in enumerate(lines[:2]):
            manager.create_audio(
                line, voice_idx=voice, file_name=str(100 * voice + i + 1)
            )
