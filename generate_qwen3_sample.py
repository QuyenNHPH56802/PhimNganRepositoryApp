"""Generate a Qwen3-TTS voice sample."""

import os
import torch
from qwen_tts import Qwen3TTSModel
import soundfile as sf


os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
torch.set_num_threads(os.cpu_count() or 4)

TEXT = "Hello, I am your intelligent translation assistant."
OUTPUT_FILE = "sample_qwen3_en_female.wav"
CHECKPOINT = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER = "Vivian"


def main():
    tts = Qwen3TTSModel.from_pretrained(
        CHECKPOINT,
        device_map="cpu",
        dtype=torch.float32,
    )

    print("Supported speakers:", tts.get_supported_speakers())
    print("Supported languages:", tts.get_supported_languages())

    print(f"Generating with speaker={SPEAKER}, language=English...")
    wavs, sr = tts.generate_custom_voice(
        text=TEXT,
        speaker=SPEAKER,
        language="English",
        max_new_tokens=512,
    )
    sf.write(OUTPUT_FILE, wavs[0], sr)
    print(f"Saved: {OUTPUT_FILE} (sr={sr}, duration={len(wavs[0])/sr:.2f}s)")


if __name__ == "__main__":
    main()