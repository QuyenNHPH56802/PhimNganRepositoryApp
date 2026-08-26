"""Build a golden dataset directory from raw source transcripts + reference translations.

Usage:
    python scripts/build_golden.py \
        --source transcripts/zh.txt \
        --reference transcripts/vi.txt \
        --out datasets/golden/zh-vi/ \
        --domain vlog --speaker-gender x --tags synthetic,seed

The builder does not synthesize audio. If you want audio fixtures, supply
`--audio-dir` and ensure filenames match `<line>.wav`. The CLI never downloads
or fetches external audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from datasets.golden import (
    Domain,
    GoldenSentence,
    License,
    Provenance,
    SpeakerGender,
)


def _slug(text: str, limit: int = 16) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"line_{digest}"


def _split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def build(
    *,
    source_path: Path,
    reference_path: Path,
    output_dir: Path,
    domain: Domain,
    speaker_gender: SpeakerGender,
    tags: list[str],
    license_kind: License,
    audio_dir: Path | None,
    multi_speaker: bool = False,
) -> int:
    zh_lines = _split_lines(source_path.read_text(encoding="utf-8"))
    vi_lines = _split_lines(reference_path.read_text(encoding="utf-8"))
    if len(zh_lines) != len(vi_lines):
        print(
            f"[build_golden] line mismatch: zh={len(zh_lines)} vi={len(vi_lines)}",
            file=sys.stderr,
        )
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audio").mkdir(exist_ok=True)
    (output_dir / "transcripts").mkdir(exist_ok=True)
    (output_dir / "reference").mkdir(exist_ok=True)
    (output_dir / "subtitles").mkdir(exist_ok=True)

    sentences_path = output_dir / "sentences.jsonl"
    with sentences_path.open("w", encoding="utf-8") as sentences_file:
        for index, (zh, vi) in enumerate(zip(zh_lines, vi_lines), start=1):
            slug = _slug(zh)
            audio_key = f"audio/{slug}.wav" if audio_dir and (audio_dir / f"{slug}.wav").exists() else None
            sentence = GoldenSentence(
                id=f"{slug}_{index:04d}",
                zh=zh,
                vi=vi,
                audio_key=audio_key,
                domain=domain,
                speaker_gender=speaker_gender,
                tags=tags,
                license=license_kind,
                provenance=Provenance(contributor="build_golden", source="synthetic"),
            )
            sentences_file.write(sentence.model_dump_json() + "\n")

            (output_dir / "transcripts" / f"{slug}.txt").write_text(zh, encoding="utf-8")
            (output_dir / "reference" / f"{slug}.vi.txt").write_text(vi, encoding="utf-8")

            cps_target = 16.0
            duration_s = max(1.5, len(vi) / cps_target)
            start_ms = (index - 1) * int(duration_s * 1000)
            end_ms = start_ms + int(duration_s * 1000)
            with (output_dir / "subtitles" / f"{slug}.srt").open("w", encoding="utf-8") as subtitle_file:
                subtitle_file.write(
                    f"{index}\n00:00:{(start_ms // 1000) // 60:02d},{(start_ms // 1000) % 60:02d}.{(start_ms % 1000):03d} "
                    f"--> 00:00:{(end_ms // 1000) // 60:02d},{(end_ms // 1000) % 60:02d}.{(end_ms % 1000):03d}\n{vi}\n\n"
                )

    print(f"[build_golden] wrote {len(zh_lines)} sentences -> {sentences_path}")
    if multi_speaker:
        _write_multi_speaker_stub(output_dir, domain=domain, license_kind=license_kind)
    return 0


def _write_multi_speaker_stub(output_dir: Path, *, domain: Domain, license_kind: License) -> None:
    multi_dir = output_dir / "multi-speaker"
    multi_dir.mkdir(exist_ok=True)
    stub = {
        "id": "auto_dialogue",
        "domain": domain.value,
        "license": license_kind.value,
        "provenance": {"contributor": "build_golden", "source": "synthetic"},
        "speakers": ["spk_A", "spk_B"],
        "turns": [
            {"speaker": "spk_A", "start_ms": 0, "end_ms": 1500, "zh": "你好。", "vi": "Xin chào."},
            {"speaker": "spk_B", "start_ms": 1600, "end_ms": 3000, "zh": "你好。", "vi": "Chào bạn."},
        ],
    }
    (multi_dir / "auto_dialogue.json").write_text(
        json.dumps(stub, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build golden dataset directory")
    parser.add_argument("--source", type=Path, required=True, help="Source transcript path (zh)")
    parser.add_argument("--reference", type=Path, required=True, help="Reference translation path (vi)")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument("--audio-dir", type=Path, default=None, help="Optional audio directory")
    parser.add_argument("--domain", choices=[d.value for d in Domain], default="vlog")
    parser.add_argument("--speaker-gender", choices=[g.value for g in SpeakerGender], default="x")
    parser.add_argument("--tags", default="synthetic,seed", help="Comma-separated tags")
    parser.add_argument("--license", choices=[l.value for l in License], default=License.CC_BY_SA_4.value)
    parser.add_argument("--multi-speaker", action="store_true", help="Emit a multi-speaker dialogue stub")
    args = parser.parse_args()

    return build(
        source_path=args.source,
        reference_path=args.reference,
        output_dir=args.out,
        domain=Domain(args.domain),
        speaker_gender=SpeakerGender(args.speaker_gender),
        tags=[t.strip() for t in args.tags.split(",") if t.strip()],
        license_kind=License(args.license),
        audio_dir=args.audio_dir,
        multi_speaker=args.multi_speaker,
    )


if __name__ == "__main__":
    raise SystemExit(main())