# Pipeline Quality

Phase 7 turns the MVP pipeline into a production-quality pipeline. This
document describes the moving pieces, the tuning knobs, and the metric
thresholds each stage is held to.

## Pipeline at a glance

```
        ┌─────────────┐
        │  asset.wav  │
        └──────┬──────┘
               │
               ▼
   ┌───────────────────────┐
   │ asr_transcribe_diarize │  WhisperX + pyannote + wav2vec2 alignment
   └──────────┬────────────┘
              │ TranscriptSegment[]  (word-level, speaker_id)
              ▼
   ┌───────────────────────┐
   │       translate       │  OpenAI / Gemini / Claude / Local
   └──────────┬────────────┘
              │ TranslatedSegment[] (vi, speaker_id, start_ms, end_ms)
              ▼
   ┌───────────────────────┐
   │ subtitle alignment    │  SequenceMatcher + dp aligner → cues
   └──────────┬────────────┘
              │ SubtitleCue[]
              ▼
   ┌───────────────────────┐
   │       qa_per_speaker  │  per-speaker WER + missing-speaker detection
   └──────────┬────────────┘
              │
   ┌──────────┴──────────────────────────┐
   ▼                                     ▼
┌──────────────────┐            ┌────────────────────────┐
│ voice_clone_*    │            │ mix_dub                │
│ VieNeu / CosyV3  │            │ sidechain + loudnorm   │
└──────────────────┘            └────────────────────────┘
```

## Quality modes

| Mode | ASR | Diarize | Alignment | Voice clone | Mixer | Subtitle CPS |
|------|-----|---------|-----------|-------------|-------|--------------|
| FAST | faster-whisper | no | no | no | no | 18 |
| BALANCED | whisperx | yes | yes | no | yes | 16 |
| HIGH | whisperx | yes | yes | yes | yes | 14 |

Switch via `PUT /projects/{id}/quality-mode { "mode": "high" }`.

## Subtitle alignment

`subtitle/aligner.py:align_subtitles_to_asr` uses `difflib.SequenceMatcher`
to map ASR tokens onto the target Vietnamese text. The match cost matrix
penalizes substitution; matched words carry the ASR start/end timing.

Cues are CPS-clamped against the policy target. `alignment_mse(cues, gold)`
returns ms² — golden threshold: ≤ 250 ms².

## Voice cloning

Reference audio → `voice_extract_embedding` (resemblyzer / 3D-Speaker) →
`voice_clone_synthesize(text, embedding_key)`. The provider reads
`ctx.voice_consent`; if it's not `"granted"`, it raises `ConsentMissing`.
The activity refuses to run unless `voice_profile.consent_status == "granted"`
in the DB.

The activity writes an `audit_logs` row for every extraction and synthesis.

## Multi-speaker QA

`qa_per_speaker` returns:

- `missing_speakers` — speakers in reference absent from output.
- `per_speaker_wer` — dict of per-speaker WER.
- `per_speaker_wer_mean` — average.
- `turn_overlap_count` — overlapping `[mm:ss.ms]` markers.

Missing speakers ≥ 1 fails the gate.

## Dubbing mixer

`mixer/ffmpeg_mixer.py:mix_dub` builds a `filter_complex` chain:

```
[bgm]volume=1.0[bgm];
[speaker][bgm]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=200[compr];
[compr]loudnorm=I=-16:LRA=11:TP=-1.0[out]
```

`loudnorm` is part of ffmpeg's GPL components; if the bundled binary is
LGPL, the loudnorm filter may be missing. CI checks for
`ffmpeg -filters | grep loudnorm`.

After mixing, `loudness_delta` (target −16 LUFS) must stay ≤ 1.5 LU.

## Tuning knobs

| Knob | Where | Effect |
|------|-------|--------|
| `QualityMode` | API | Switches the entire policy |
| `target_cps` | QualityPolicy | Subtitle cue duration floor |
| `loudnorm I/LRA/TP` | Mixer | EBU R128 target |
| `sidechain threshold/ratio` | Mixer | BGM ducking aggressiveness |
| `model_id` (WhisperX) | Provider | Transcription accuracy |

## Metric thresholds

See `scripts/baseline_thresholds.yaml`:

| Provider | Metric | Threshold |
|----------|--------|-----------|
| alignment | alignment_mse | ≤ 250 ms² |
| qa_multispeaker | per_speaker_wer_mean | ≤ 0.15 |
| qa_multispeaker | missing_speaker_count | 0 |
| mixer | loudness_delta | ≤ 1.5 LU |
| mixer | loudness_lufs | -17.5 .. -14.5 |

## Limitations

- ASR/diarize/voice-clone providers are stubs; metrics use synthetic data.
- Loudness measurement requires ffmpeg with `loudnorm` filter enabled.
- Per-speaker QA WER requires `jiwer`.