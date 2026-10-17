"""Measure Basic and Smart translation explicitly, using the established changes benchmark's corpus and dials."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys

import aussiefy
from aussiefy.translation import run

# The maintainer benchmark is outside the installed package; keep its checkout behind the selected package.
sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts import benchmark_changes as benchmark


def measure(repeats):
    tr = aussiefy.Translator(lookup_embedder=None)
    rows = []
    for mode, embedder in [("basic", None), ("smart", "bundled")]:
        expected = "ngram" if mode == "basic" else "bundled"
        for setting, base in benchmark.SETTINGS.items():
            options = base | {"embedder": embedder}
            resolved = tr.policy(**options).embedder
            if resolved != expected:
                raise RuntimeError(f"{mode}/{setting}: unexpected resolved embedder {resolved}")
            for name, text in benchmark.texts():
                plain = run(text, translator=tr, **options)
                built = run(text, translator=tr, _changes=True, **options)
                if plain.text != built.text:
                    raise RuntimeError(f"{mode}/{setting}/{name}: observer changed translation")
                plain_seconds = benchmark.median_seconds(
                    lambda: run(text, translator=tr, **options), repeats)
                changes_seconds = benchmark.median_seconds(
                    lambda: run(text, translator=tr, _changes=True, **options), repeats)
                rows.append({"mode": mode, "translation_embedder": embedder, "resolved_embedder": resolved,
                    "setting": setting, "text": name,
                    "characters": len(text), "input_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "output_sha256": hashlib.sha256(plain.text.encode()).hexdigest(), "text_parity": True,
                    "translate_ms": round(plain_seconds * 1000, 3), "changes_ms": round(changes_seconds * 1000, 3),
                    "ratio": changes_seconds / plain_seconds,
                    "renderings": sum(len(c["alternatives"]) + len(c["locked"]) for c in built.changes)})
        # Observe the requested translation scorer, rather than inferring its mode from lookup configuration.
        if not callable(tr._scorers.get(expected)):
            raise RuntimeError(f"{mode}: translation fallback scorer did not match the requested mode")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    rows = measure(args.repeats)
    summaries = {mode: {setting: {"median_ratio": statistics.median(
        r["ratio"] for r in rows if r["mode"] == mode and r["setting"] == setting),
        "max_ratio": max(r["ratio"] for r in rows if r["mode"] == mode and r["setting"] == setting)}
        for setting in benchmark.SETTINGS} for mode in ["basic", "smart"]}
    indexed = {(r["mode"], r["setting"], r["text"]): r for r in rows}
    matching = {}
    for setting in benchmark.SETTINGS:
        matching[setting] = {}
        for operation in ["translate_ms", "changes_ms"]:
            ratios = [indexed["smart", setting, name][operation] / indexed["basic", setting, name][operation]
                      for name, _ in benchmark.texts()]
            matching[setting][operation] = {"median_smart_over_basic": statistics.median(ratios),
                                           "max_smart_over_basic": max(ratios)}
    package = Path(aussiefy.__file__).resolve().parent
    report = {"python": platform.python_version(), "platform": platform.platform(), "repeats": args.repeats,
        "measurement_seam": "aussiefy.translation.run; _changes=False/True, explicit translation embedder",
        "translation_modes": {"basic": None, "smart": "bundled"}, "lookup_backend": None,
        "resolved_translation_embedders": {"basic": "ngram", "smart": "bundled"},
        "scorer_activation_verified": True, "settings": benchmark.SETTINGS,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "benchmark_script_sha256": hashlib.sha256(Path(benchmark.__file__).read_bytes()).hexdigest(),
        "package_path": str(package),
        "runtime_files_sha256": {str(p.relative_to(package)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(package.rglob("*")) if p.is_file() and "__pycache__" not in p.parts},
        "criterion": "Existing median changes/translate ratio <=1.5 within each mode/setting; individual cases may exceed it.",
        "summary": summaries, "smart_over_basic": matching, "rows": rows}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))
