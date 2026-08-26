# Benchmark

Phase 5 wires a benchmark harness around the golden dataset so every
provider swap (ASR / Translation / Subtitle / TTS / OCR / Text-Removal) is
measurable and regression-detectable.

## How it works

```bash
# Run all providers against the golden dataset.
python scripts/benchmark.py --provider all \
    --golden datasets/golden \
    --out reports/$(date +%Y%m%d)

# Run a single provider.
python scripts/benchmark.py --provider asr \
    --golden datasets/golden \
    --out reports/asr

# CI smoke (reference = hypothesis, expect perfect scores).
python scripts/benchmark.py --provider all \
    --out reports/ci/ \
    --stub-only
```

Outputs:

- `reports/<run>/benchmark_<ts>.json` — per-fixture records.
- `reports/<run>/summary.json` — aggregated metrics per provider.

## Metrics

| Provider | Metric | Library | Direction |
|----------|--------|---------|-----------|
| asr | WER, CER | `jiwer` | lower better |
| translate | BLEU, chrF2 | `sacrebleu` | higher better |
| subtitle | CPS, overlap | custom | within range |
| tts | MOS proxy | heuristic | higher better |
| ocr | F1@IoU0.5 | custom | higher better |
| text-removal | PSNR (numpy) | custom | higher better |

## Thresholds

Defined in `scripts/baseline_thresholds.yaml`. CI gate fails if any metric
falls outside `[min, max]` or regresses beyond `regression`.

```yaml
asr:
  wer: { max: 0.20, regression: 0.03 }
translate:
  bleu: { min: 25.0, regression: -2.0 }
```

## Snapshotting baseline

After a benchmark run you accept as the new reference:

```bash
python scripts/baseline_snapshot.py \
    --reports reports/20240101T000000Z/benchmark.json \
    --out reports/baseline.json
```

`baseline.json` is committed; subsequent PR runs compare against it.

## CI gate

`.github/workflows/benchmark.yml` runs on every PR touching `apps/`,
`scripts/`, or `datasets/golden/`. It uploads `reports/ci/` as artifact
and fails the build on regression.

## Adding a new provider

1. Add `ProviderRunner` to `scripts/benchmark.py`.
2. Add fixtures in `scripts/fixtures/<provider>_fixture.json`.
3. Add thresholds in `baseline_thresholds.yaml`.
4. Update `metrics.py` if the metric is novel.

## Limitations

- `--stub-only` returns reference as hypothesis; useful for verifying the
  metric formulas but not for measuring real provider quality.
- PSNR/SSIM for text-removal requires `numpy`. Without numpy the runner
  returns a byte-equality proxy.
- BLEU/chrF require `sacrebleu`. Install via
  `pip install -r scripts/requirements-bench.txt`.