"""Compare Smart fallback with its exhaustive reference; writes timings and hashes, never corpus text.

Run from the repository root:
    python research/document-refinement-2026-10-15/benchmark_smart.py --repo . --output smart-performance.json
"""

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_hashes(repo):
    files = sorted((repo / "aussiefy").glob("*.py"))
    files += sorted(p for p in (repo / "aussiefy/data").rglob("*") if p.is_file())
    return {str(p.relative_to(repo)): sha256(p.read_bytes()) for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.repetitions < 3:
        parser.error("at least three warm repetitions are required")
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo))
    before = source_hashes(repo)
    started = datetime.now(timezone.utc).isoformat()
    import yaml
    from aussiefy import Translator
    from aussiefy.embed import similarity_scorer
    from aussiefy.static import bundled

    assert Path(sys.modules["aussiefy"].__file__).resolve().parent == repo / "aussiefy"
    optimised = Translator(lookup_embedder=None)
    reference = Translator(optimised.dictionary, lookup_embedder=None)
    basic = Translator(optimised.dictionary, lookup_embedder=None)
    emb = bundled()

    class ExhaustiveEmbedder:
        def similarity(self, query, pattern):
            return sum(x * y for x, y in zip(emb.encode(query), emb.encode(pattern)))

    patterns = optimised.dictionary.fallback_patterns
    reference._scorers["bundled"] = similarity_scorer(ExhaustiveEmbedder(), [p.text for p in patterns])
    modes = {"exhaustive_original_dot": (reference, "bundled"),
             "shape_first_map_dot": (optimised, "bundled"), "ngram": (basic, "ngram")}
    corpus_paths = {"story": "tests/corpus/classics/drovers_wife.txt",
                    "technical": "tests/corpus/everyday/workplace/mdn_http_cookies.md"}
    samples = {"short_known": "I'm very tired. Let's go to the pub for a beer after work. You're crazy!",
               "short_fallback": "He was exhaustedd. She is lethargic today. I am discombobulated and apprehensive."}
    samples.update({name: (repo / path).read_text(encoding="utf-8") for name, path in corpus_paths.items()})
    options = dict(level=4, seed=42, vulgarity=1, embellishment=1)
    results = []
    for name, text in samples.items():
        outputs = {mode: tr.translate(text, embedder=backend, **options).to_dict()
                   for mode, (tr, backend) in modes.items()}
        assert outputs["exhaustive_original_dot"] == outputs["shape_first_map_dot"], name
        times = {mode: [] for mode in modes}
        order = list(modes)
        for repeat in range(args.repetitions):
            offset = repeat % len(order)
            for mode in order[offset:] + order[:offset]:
                tr, backend = modes[mode]
                start = time.perf_counter()
                result = tr.translate(text, embedder=backend, **options)
                times[mode].append(time.perf_counter() - start)
                assert result.to_dict() == outputs[mode], (name, mode, repeat)
        row = {"input": name, "path": corpus_paths.get(name), "source": "file" if name in corpus_paths else "script literal",
               "sha256": sha256(text.encode()), "words": len(text.split()), "characters": len(text),
               "exact_full_result_parity": True, "modes": {}}
        for mode, elapsed in times.items():
            row["modes"][mode] = {"seconds": elapsed, "median_seconds": statistics.median(elapsed),
                                  "min_seconds": min(elapsed), "max_seconds": max(elapsed),
                                  "output_sha256": sha256(outputs[mode]["text"].encode())}
        results.append(row)
        print(json.dumps({"input": name, "median_seconds": {
            mode: values["median_seconds"] for mode, values in row["modes"].items()}}), flush=True)
    golden_path = repo / "tests/corpus/golden.yaml"
    golden_bytes = golden_path.read_bytes()
    parity_inputs = [case["input"] for case in yaml.safe_load(golden_bytes)]
    parity_inputs += [samples["story"], samples["technical"]]
    parity_options = [(2, 0), (5, 42)]
    for text in parity_inputs:
        for level, seed in parity_options:
            opts = dict(level=level, seed=seed, vulgarity=1, embellishment=1, embedder="bundled")
            assert reference.translate(text, **opts).to_dict() == optimised.translate(text, **opts).to_dict()
    assert source_hashes(repo) == before, "source changed during benchmark; rerun against a stable tree"
    assert golden_path.read_bytes() == golden_bytes, "golden corpus changed during benchmark"
    report = {"started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
              "script_sha256": sha256(Path(__file__).read_bytes()), "source_hashes": before,
              "method": {"warmup_runs_per_mode_per_input": 1, "warm_repetitions": args.repetitions,
                         "measurement": "perf_counter translation only; serial modes rotate each repetition",
                         "shared": "same current dictionary, grammar, embedding weights and vector caches",
                         "comparison": "exhaustive candidate scores with original generator dot vs current scorer and dot",
                         "scope": "core backend only; excludes construction, network and website overhead",
                         "options": options},
              "model": {"name": emb.name, "dimensions": emb.dims, "fallback_patterns": len(patterns)},
              "benchmarks": results,
              "parity": {"source": "tests/corpus/golden.yaml", "source_sha256": sha256(golden_bytes),
                         "input_hashes": [sha256(t.encode()) for t in parity_inputs],
                         "inputs": len(parity_inputs), "source_words": sum(len(t.split()) for t in parity_inputs),
                         "level_seed_pairs": parity_options, "comparisons": len(parity_inputs) * len(parity_options),
                         "exact_full_result_parity": True}, "sources_unchanged_during_run": True}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "parity_comparisons": report["parity"]["comparisons"]}), flush=True)


if __name__ == "__main__":
    main()
