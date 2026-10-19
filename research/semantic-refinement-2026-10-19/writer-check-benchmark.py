"""Bounded warm writer-check timings; choose a checkout through PYTHONPATH."""

import json, statistics, time
from pathlib import Path
import aussiefy
from aussiefy import Translator, harness

tr = Translator(lookup_embedder=None)
text = "The worker carried the boxes to the station. A friend said that the weather was pleasant. " * 35
for _ in range(2):
    harness.lint(text, original=text, translator=tr, suggest=False, english="none")
samples = []
for _ in range(5):
    start = time.perf_counter()
    harness.lint(text, original=text, translator=tr, suggest=False, english="none")
    samples.append(time.perf_counter() - start)
print(
    json.dumps(
        {
            "module": str(Path(aussiefy.__file__).resolve()),
            "median_seconds": statistics.median(samples),
            "samples": samples,
            "words": len(text.split()),
        }
    )
)
