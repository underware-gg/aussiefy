"""Train, evaluate and release the bundled Aussie embedder (aussiefy/data/model), from training/recipe.yaml.

    python scripts/train_embedder.py release --version X.Y.Z    # everything: evaluation run, release run, export,
                                                                # reference checks, training/reports/X.Y.Z.json
    python scripts/train_embedder.py check                      # the reference set against the shipped model (no torch)

The steps `release` runs, for experiments (each takes --out DIR and --holdout):

    train       fine-tune the base model on the dictionary's pairs
    distil      Model2Vec distillation (of the base and the fine-tuned model), then tune the static vectors
    eval        Recall@3 on the held-back entries, the reference set, sizes, for every setup
    calibrate   cosine scores of related vs unrelated pairs, to choose cut-offs (--model PATH|ngram|bundled)
    export      write the tuned static model into the package (or --dest), with meta.json

Training needs the pinned toolchain in training/requirements.txt (torch, sentence-transformers, model2vec);
the package never does. Work goes to $AUSSIEFY_HOME/train/<version> (default ~/.aussiefy) and is never
committed. The approach, versioning and lessons learned are in training/README.md.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aussiefy.embed import NgramEmbedder  # noqa: E402
from aussiefy.gaps import concept_labels  # noqa: E402
from aussiefy.loader import load_dictionary  # noqa: E402
from aussiefy.lookup import meaning_texts  # noqa: E402
from aussiefy.models import home  # noqa: E402
from aussiefy.matcher import compile_pattern  # noqa: E402
from aussiefy.static import dictionary_fingerprint  # noqa: E402
from aussiefy.terms import strip_markup  # noqa: E402

RECIPE_PATH = ROOT / "training" / "recipe.yaml"
REPORTS = ROOT / "training" / "reports"
TOOLCHAIN = ("torch", "sentence-transformers", "transformers", "model2vec", "tokenizers", "safetensors", "datasets", "nltk",
             "accelerate", "scikit-learn", "numpy", "huggingface_hub")
METRICS = ("gloss->form", "gloss->concept's forms", "form->concept")
LOWER = ("opposites offered",)   # lower is better: share of queries where lookup would offer an opposite

R: dict = {}              # the recipe: loaded once by main() (--recipe PATH, or training/recipe.yaml)


def load_recipe(path: Path = RECIPE_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def best_by(scored) -> dict:
    """The best score for each key, from (key, score) pairs: an entry's best text, a concept's best entry."""
    best: dict = {}
    for key, score in scored:
        score = float(score)
        if key not in best or score > best[key]:
            best[key] = score
    return best


# --- data -------------------------------------------------------------------------------------------------

def clean(text: str) -> str:
    """Bind recipe pronouns, then remove grammar annotations through the shared language boundary."""
    slots = R["pairs"]["placeholders"]
    text = re.sub(r"\{(\w+)\}", lambda m: slots.get(m.group(1), ""), text)
    return strip_markup(text)


def entries(d):
    return sorted((e for e in d.idioms + d.garnish if e.status != "omit" and e.concept), key=lambda e: e.id)


def split(d, holdout: float) -> tuple[list, list]:
    """(training entries, held-back entries): a holdout share of the entries, drawn with the recipe's seed."""
    es = entries(d)
    rng = random.Random(R["seed"])
    held = set(rng.sample([e.id for e in es], round(len(es) * holdout)))
    return [e for e in es if e.id not in held], [e for e in es if e.id in held]


def triggers(d, cid: str) -> list[str]:
    c = d.concepts.get(cid)
    return [clean(p) for ps in (c.triggers.values() if c else ()) for p in ps]


def extra_pairs() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Pairs from the recipe's extra sources: YAML lists of {anchor, positive} or {anchor, negative}."""
    pos, neg = [], []
    for p in R["sources"].get("extra_pairs") or ():
        for row in yaml.safe_load((ROOT / p).read_text(encoding="utf-8")) or ():
            (pos if "positive" in row else neg).append((row["anchor"], row.get("positive") or row["negative"]))
    return pos, neg


WN_POS = {"predicate_adj": "as", "adj": "as", "np": "n", "vp": "v", "adv": "r"}


def wordnet_synonyms(word: str, pos: str, senses: int) -> list[str]:
    """Synonyms from a word's most common sense(s) in WordNet: the sense's own lemmas, and for adjectives the
    'similar to' cluster ("angry" -> wrathful, irascible), where WordNet keeps most adjective synonyms."""
    from nltk.corpus import wordnet as wn

    out = []
    for p in pos:
        for syn in wn.synsets(word.replace(" ", "_"), pos=p)[:senses]:
            out += [l.name() for l in syn.lemmas()]
            if p in "as":
                # NLTK's relation pointers are sets. Stabilise neighbours before per_trigger truncation,
                # retaining the source's sense-frequency and lemma order.
                out += [l.name() for s in sorted(syn.similar_tos(), key=lambda item: item.name()) for l in s.lemmas()]
    seen, keep = {word.lower()}, []
    for w in out:
        w = w.replace("_", " ").lower()
        if w not in seen and w.replace(" ", "").replace("-", "").isalpha():
            seen.add(w)
            keep.append(w)
    return keep


def benchmark_words() -> set[str]:
    path = R.get("gap_benchmark")
    if not path:
        return set()
    b = yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) or {}
    return {w.lower() for w in (b.get("fill") or {})} | {w.lower() for w in b.get("no_fill") or ()}


def wordnet_pairs(d, train) -> list[tuple[str, str]]:
    """Plain-English coverage: each trigger's WordNet synonyms paired with the concept's description and a few of
    its forms, so "affluent" lands near RICH. A synonym that is another concept's trigger is skipped (it belongs
    there), and benchmark words never enter training."""
    cfg = R["sources"].get("wordnet") or {}
    if not cfg.get("enabled"):
        return []
    trig_owner = {}
    for cid in d.concepts:
        for t in triggers(d, cid):
            trig_owner.setdefault(t.lower(), set()).add(cid)
    banned = benchmark_words()
    forms = {}
    for e in train:
        for cid in e.concept:
            forms.setdefault(cid, []).append(clean(e.form))
    out = []
    for cid, c in d.concepts.items():
        if not forms.get(cid):
            continue
        targets = [c.description] + forms[cid][:cfg.get("forms_per_concept", 2)]
        for frame, ps in c.triggers.items():
            pos = WN_POS.get(frame)
            if not pos:
                continue
            for p in ps:
                t = clean(p)
                if not t or "|" in t or "?" in t or len(t.split()) > 2:
                    continue
                syns = [w for w in wordnet_synonyms(t, pos, cfg.get("senses", 1))
                        if w not in banned and not (trig_owner.get(w, set()) - {cid})][:cfg.get("per_trigger", 6)]
                out += [(w, x) for w in syns for x in targets]
    return out


def pairs(d, train) -> list[tuple[str, str]]:
    """Trigger and replaces -> form, gloss -> form and variants, form -> riff; WordNet synonyms -> description and
    forms; then the recipe's extra pairs."""
    out = []
    # "first": a trigger pairs only with forms whose first concept is its own, so a multi-concept entry (stuffed:
    # TIRED, BROKEN, FULL) doesn't chain TIRED's triggers to FULL's and DRUNK's (1.3.0)
    first_only = R["pairs"].get("trigger_concepts", "all") == "first"
    for e in train:
        form = clean(e.form)
        for cid in e.concept[:1] if first_only else e.concept:
            out += [(t, form) for t in triggers(d, cid)]
        out += [(clean(r), form) for r in e.replaces]
        if e.gloss:
            out.append((e.gloss, form))
            out += [(e.gloss, clean(v)) for v in e.variants]
        out += [(form, r.text) for r in e.riffs]
    out += wordnet_pairs(d, train)
    out += extra_pairs()[0]
    seen, uniq = set(), []
    for a, b in out:
        if a and b and a.lower() != b.lower() and (a, b) not in seen:
            seen.add((a, b))
            uniq.append((a, b))
    return uniq


def sense_negatives(d, train) -> list[tuple[str, str]]:
    """The dictionary's own wrong senses: a trigger's !exclusions ("great !war|deal|...") paired with that
    concept's forms (and, per the recipe, its glosses and description: lookup compares with those), so "great
    war" learns to stay away from "beaut"; then the recipe's extra negatives."""
    targets = R["pairs"].get("sense_targets", ["forms"])
    n = R["pairs"]["sense_forms_per_concept"]
    forms = {}
    for e in train:
        for cid in e.concept:
            forms.setdefault(cid, [])
            if "forms" in targets:
                forms[cid].append(clean(e.form))
    for cid in list(forms):
        forms[cid] = forms[cid][:n]
        if "glosses" in targets:
            forms[cid] += [e.gloss for e in train if cid in e.concept and e.gloss][:n]
        if "description" in targets and cid in d.concepts:
            forms[cid].append(d.concepts[cid].description)
    out = []
    for cid, c in d.concepts.items():
        if not forms.get(cid):
            continue
        positive_triggers = {t.casefold() for t in triggers(d, cid)}
        for frame, patterns in c.triggers.items():
            for raw in patterns:
                if '!' not in raw:
                    continue
                compiled = compile_pattern(raw, frame, (cid,), 3)
                base = clean(raw)
                for i, element in enumerate(compiled.elements):
                    if element.kind != 'not':
                        continue
                    if any(e.kind in {'lit', 'slot'} for e in compiled.elements[i + 1:]):
                        raise ValueError(f'Training cannot construct a nonterminal exclusion: {raw!r}')
                    for word in sorted(element.values):
                        if len(word) < 3:
                            continue
                        anchor = f"{base} {word}"
                        # A short trigger may exclude a continuation owned by its longer positive trigger.
                        if anchor.casefold() not in positive_triggers:
                            out += [(anchor, f) for f in forms.get(cid, [])]
    return out + extra_pairs()[1]


def opposites() -> list[tuple[str, str]]:
    path = R["sources"].get("opposites")
    return [tuple(p) for p in yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) or ()] if path else []


def opposite_negatives(d, train) -> list[tuple[str, str]]:
    """Same topic, opposite meaning: for each pair in the recipe's opposites file, A's triggers and glosses
    against B's forms, both ways, so "a heap of money" learns to stay away from *stony broke*."""
    na, nf = R["pairs"]["opposite_anchors_per_concept"], R["pairs"]["opposite_forms_per_concept"]
    out = []
    for a, b in opposites():
        for x, y in ((a, b), (b, a)):
            anchors = [t for t in triggers(d, x) if t and "|" not in t and "?" not in t][:na]
            anchors += [e.gloss for e in train if x in e.concept and e.gloss][:na]
            targets = R["pairs"].get("opposite_targets", ["forms"])
            ys = [e for e in train if y in e.concept]
            far = [clean(e.form) for e in ys][:nf] if "forms" in targets else []
            far += [e.gloss for e in ys if e.gloss][:nf] if "glosses" in targets else []
            far += [d.concepts[y].description] if "description" in targets else []
            out += [(t, f) for t in anchors for f in far]
    return out


def pair_sets(d, train) -> tuple[list, list, list]:
    """Generate the exact positive, wrong-sense and opposite rows used by both fitting stages."""
    return pairs(d, train), sense_negatives(d, train), opposite_negatives(d, train)


def pair_conflicts(rows: tuple[list, list, list]) -> dict[str, list[list[str]]]:
    """An undirected similarity pair cannot simultaneously attract and repel, regardless of case/spacing."""
    def key(pair):
        return tuple(sorted(" ".join(text.casefold().split()) for text in pair))
    positives = {key(pair) for pair in rows[0]}
    conflicts = {name: [list(pair) for pair in sorted(positives & {key(pair) for pair in negatives})]
            for name, negatives in zip(('wrong_sense', 'opposite'), rows[1:])}
    conflicts['negative_self'] = [list(pair) for pair in sorted({key(p) for group in rows[1:] for p in group
                                                            if key(p)[0] == key(p)[1]})]
    return conflicts


def checked_pairs(d, train) -> tuple[list, list, list]:
    rows = pair_sets(d, train)
    conflicts = pair_conflicts(rows)
    if any(conflicts.values()):
        raise ValueError('Contradictory training labels; run audit before fitting: ' + json.dumps(conflicts))
    return rows


def audit(holdout: float, report: Path | None = None) -> int:
    """Inspect generated rows without loading a model; sharing concepts is reported, not called an error."""
    d = load_dictionary()
    train, held = split(d, holdout)
    rows = pair_sets(d, train)
    conflicts = pair_conflicts(rows)
    result = {'scope': 'Exact generated label conflicts; not a model-quality or in-batch-negative assessment.',
              'entries': len(train), 'held': len(held), 'holdout': holdout,
              'dictionary_sha256': dictionary_fingerprint(), 'recipe_sha256': sha256(RECIPE_PATH),
              'trainer_sha256': sha256(Path(__file__)),
              'counts': dict(zip(('positive', 'wrong_sense', 'opposite'), map(len, rows))),
              'pair_sha256': {name: hashlib.sha256(json.dumps(data, ensure_ascii=False).encode()).hexdigest()
                              for name, data in zip(('positive', 'wrong_sense', 'opposite'), rows)},
              'multi_concept_entries': [{'id': e.id, 'concepts': list(e.concept)} for e in train if len(e.concept) > 1],
              'conflicts': conflicts}
    encoded = json.dumps(result, indent=2) + '\n'
    if report is not None:
        report.write_text(encoded, encoding='utf-8')
    else:
        print(encoded, end='')
    return int(any(conflicts.values()))


def vocabulary(es) -> list[str]:
    """Whole words from the entries' forms and riffs, so slang gets its own static vector rather than the mean
    of its word pieces. Only training entries, so the held-back forms stay unseen."""
    texts = [clean(f) for e in es for f in e.all_forms] + [r.text for e in es for r in e.riffs]
    return sorted({w for t in texts for w in re.findall(r"[a-z][a-z']+[a-z]|[a-z]{2}", t.lower())})


# --- encoders: sims(queries, docs) -> matrix of cosine similarities ---------------------------------------

class Ngram:
    def __init__(self, *_):
        self.e = NgramEmbedder()

    def sims(self, queries, docs):
        import numpy as np

        return np.array([[self.e.similarity(q, t) for t in docs] for q in queries])


class Dense:
    def __init__(self, path, revision=None):
        from sentence_transformers import SentenceTransformer

        self.m = SentenceTransformer(str(path), device="cpu", revision=revision)

    def encode(self, texts):
        return self.m.encode(list(texts), normalize_embeddings=True, batch_size=64)

    def sims(self, queries, docs):
        return self.encode(queries) @ self.encode(docs).T


class Static(Dense):
    def __init__(self, path):
        from model2vec import StaticModel

        self.m = StaticModel.from_pretrained(str(path))

    def encode(self, texts):
        import numpy as np

        v = self.m.encode(list(texts))
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


class Bundled(Static):
    """The model the package ships (or one exported with --dest), read by aussiefy.static: no torch."""

    def __init__(self, path=None):
        from aussiefy.static import MODEL_DIR, StaticEmbedder

        self.m = StaticEmbedder(Path(path) if path else MODEL_DIR)

    def encode(self, texts):
        import numpy as np

        return np.array([self.m.encode(t) for t in texts])


def encoder(spec: str):
    """ngram, bundled, an exported folder (meta.json), a Model2Vec folder, or a sentence-transformers model."""
    p = Path(spec)
    if spec == "ngram":
        return Ngram()
    if spec == "bundled" or (p / "meta.json").exists():
        return Bundled(None if spec == "bundled" else p)
    if (p / "tokenizer.json").exists() and not (p / "config_sentence_transformers.json").exists():
        return Static(p)
    return Dense(spec)


def base_encoder():
    return Dense(R["base"]["model"], R["base"]["revision"])


# --- train / distil ---------------------------------------------------------------------------------------

def fit(model, rows, epochs, lr, batch, path, work: Path) -> None:
    """MultipleNegativesRankingLoss on the pairs; ContrastiveLoss pushes the wrong senses apart."""
    from datasets import Dataset
    from sentence_transformers import SentenceTransformerTrainer
    from sentence_transformers.sentence_transformer import losses
    from sentence_transformers.sentence_transformer.training_args import (BatchSamplers,
                                                                          SentenceTransformerTrainingArguments)

    ps, negs, opp = rows
    print(f"{len(ps)} pairs, {len(negs)} wrong-sense pairs, {len(opp)} opposite pairs")

    def apart(rows):
        return Dataset.from_dict({"sentence1": [a for a, _ in rows], "sentence2": [b for _, b in rows],
                                  "label": [0.0] * len(rows)})

    margin = R["finetune"]["sense_margin"]
    data = {"pairs": Dataset.from_dict({"anchor": [a for a, _ in ps], "positive": [b for _, b in ps]}),
            "senses": apart(negs)}
    loss = {"pairs": losses.MultipleNegativesRankingLoss(model), "senses": losses.ContrastiveLoss(model, margin=margin)}
    if opp:
        data["opposites"] = apart(opp)
        loss["opposites"] = losses.ContrastiveLoss(model, margin=R["finetune"].get("opposite_margin", margin))
    targs = SentenceTransformerTrainingArguments(
        output_dir=str(work / "checkpoints"), num_train_epochs=epochs, per_device_train_batch_size=batch,
        learning_rate=lr, warmup_steps=R["finetune"]["warmup"], batch_sampler=BatchSamplers.NO_DUPLICATES,
        seed=R["seed"], data_seed=R["seed"], save_strategy="no", logging_steps=50, report_to=[], use_cpu=True)
    SentenceTransformerTrainer(model=model, args=targs, train_dataset=data, loss=loss).train()
    model.save(str(path))
    print("saved", path)


def train(work: Path, holdout: float) -> None:
    """Fine-tune the base model on the training entries' pairs, into work/aussie-minilm."""
    from sentence_transformers import SentenceTransformer

    f = R["finetune"]
    d = load_dictionary()
    tr, _ = split(d, holdout)
    rows = checked_pairs(d, tr)
    model = SentenceTransformer(R["base"]["model"], device="cpu", revision=R["base"]["revision"])
    fit(model, rows, f["epochs"], f["lr"], f["batch"], work / "aussie-minilm", work)


def distil(work: Path, holdout: float, compare: bool) -> None:
    """Model2Vec distillation of the fine-tuned model (and of the base, for comparison), then the static model
    tuned on the same pairs: distilling alone loses most of what fine-tuning taught."""
    from huggingface_hub import snapshot_download
    from model2vec import StaticModel
    from model2vec.distill import distill
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.models import StaticEmbedding

    ds, st = R["distil"], R["static_tune"]
    d = load_dictionary()
    tr, _ = split(d, holdout)
    rows = checked_pairs(d, tr)
    sources = [("static-aussie", work / "aussie-minilm")]
    if compare:
        sources.insert(0, ("static-stock", snapshot_download(R["base"]["model"], revision=R["base"]["revision"])))
    for name, src in sources:
        m = distill(model_name=str(src), pca_dims=ds["pca_dims"], sif_coefficient=ds["sif_coefficient"],
                    vocabulary=vocabulary(tr) if ds["dictionary_vocabulary"] else None)
        m.save_pretrained(str(work / name))
        print("saved", work / name)
    emb = StaticEmbedding.from_model2vec(str(work / "static-aussie"))
    emb.embedding.float()   # distilled vectors are float16, which overflows at a static model's learning rate
    model = SentenceTransformer(modules=[emb], device="cpu")
    fit(model, rows, st["epochs"], st["lr"], st["batch"], work / "checkpoints" / "static-tuned-st", work)
    vectors = emb.embedding.weight.detach().cpu().numpy()
    a = st.get("blend", 1.0)
    if a < 1.0:   # blend back towards the distilled vectors: one scale per matrix, so relative norms (the
        import numpy as np   # frequency weighting Model2Vec keeps in them) survive

        base = StaticModel.from_pretrained(str(work / "static-aussie")).embedding.astype(np.float32)
        vectors = a * vectors / np.linalg.norm(vectors, axis=1).mean() + (1 - a) * base / np.linalg.norm(base, axis=1).mean()
    vectors = vectors.astype("float16")   # half the size, same Recall@3
    StaticModel(vectors=vectors, tokenizer=emb.tokenizer, normalize=True).save_pretrained(
        str(work / "static-aussie-tuned"))
    print("saved", work / "static-aussie-tuned")


# --- evaluation -------------------------------------------------------------------------------------------

def recall_at(sims, gold, k=3) -> float:
    import numpy as np

    top = np.argsort(-sims, axis=1)[:, :k]
    return float(np.mean([bool(set(t) & g) for t, g in zip(top, gold)]))


def size_mb(path: Path) -> float:
    return round(sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / 1e6, 1)


def reference(d, enc, cutoff: float, ref_path: Path | None = None) -> dict:
    """The reference set (training/reference.yaml) for one encoder, scored the way lookup scores: the query
    against every entry's gloss and concept descriptions; a concept scores its best entry."""
    import numpy as np

    ref = yaml.safe_load((ref_path or ROOT / R["reference"]).read_text(encoding="utf-8"))
    es = [e for e in entries(d) if e.gloss]
    texts, owner = [], []
    for i, e in enumerate(es):
        for t in meaning_texts(e, d):
            texts.append(t)
            owner.append(i)
    owner = np.array(owner)
    checks = [("must_not", c) for c in ref.get("must_not") or ()] + [("should", c) for c in ref.get("should") or ()]
    checks += [(c["kind"], {**c, "known": True}) for c in ref.get("known") or ()]
    sims = enc.sims([c["query"] for _, c in checks], texts)
    out = []
    for (kind, c), row in zip(checks, sims):
        per_entry = np.full(len(es), -1.0)
        np.maximum.at(per_entry, owner, row)
        top_entries = [es[i] for i in np.argsort(-per_entry)[:3]]
        concept_score = best_by((cid, per_entry[i]) for i, e in enumerate(es) for cid in e.concept)
        top_concepts = sorted(concept_score, key=concept_score.get, reverse=True)[:3]
        if kind == "should":
            ok = bool(set(c["concepts"]) & set(top_concepts))
        else:
            bad_forms, bad_concepts = set(c.get("forms") or ()), set(c.get("concepts") or ())
            hits = [i for i, e in enumerate(es) if e.form in bad_forms or set(e.concept) & bad_concepts]
            # as lookup sees it: offered only at or above the cut-off, so a wrong sense must stay under it,
            # and never be the best match even when nothing reaches it
            worst = max((float(per_entry[i]) for i in hits), default=0.0)
            ok = worst < cutoff and es.index(top_entries[0]) not in hits
        out.append({"kind": kind, "query": c["query"], "pass": ok, "known": c.get("known", False),
                    "top_concepts": top_concepts, "top_forms": [e.form for e in top_entries]})
    required = [r for r in out if not r["known"]]
    return {"passed": sum(r["pass"] for r in required), "required": len(required),
            "known_fixed": [r["query"] for r in out if r["known"] and r["pass"]], "checks": out}


def gap_benchmark(d, enc) -> dict:
    """training/gap_benchmark.yaml, scored as `aussiefy gaps` scores: the word against each concept's description
    and first triggers per frame; the nearest concept wins, and it counts as filled at the gaps cut-off."""
    b = yaml.safe_load((ROOT / R["gap_benchmark"]).read_text(encoding="utf-8"))
    labels, owner = [], []
    for cid, ts in concept_labels(d).items():
        for t in ts:
            if t:
                labels.append(t)
                owner.append(cid)
    words = list(b["fill"]) + list(b["no_fill"])
    sims = enc.sims(words, labels)
    cut = R["cutoffs"]["gaps"]
    rows = []
    for w, row in zip(words, sims):
        per = best_by(zip(owner, row))
        top = max(per, key=per.get)
        rows.append((w, top, per[top]))
    fill = [(w, top, s) for w, top, s in rows if w in b["fill"]]
    nofill = [(w, top, s) for w, top, s in rows if w not in b["fill"]]
    return {"gap right@1": round(sum(b["fill"][w] == t for w, t, _ in fill) / len(fill), 3),
            "gap filled right": round(sum(b["fill"][w] == t and s >= cut for w, t, s in fill) / len(fill), 3),
            "gap filled wrong": round(sum(b["fill"][w] != t and s >= cut for w, t, s in fill) / len(fill), 3),
            "everyday filled": round(sum(s >= cut for *_, s in nofill) / len(nofill), 3),
            "detail": [{"word": w, "nearest": t, "score": round(s, 3), "want": b["fill"].get(w)} for w, t, s in rows]}


GAP = ("gap right@1", "gap filled right", "gap filled wrong", "everyday filled")


def evaluate(work: Path, holdout: float) -> list[dict]:
    """Every setup in work on the held-back entries, and on the reference set."""
    d = load_dictionary()
    tr, held = split(d, holdout)
    es = entries(d)
    forms = [clean(e.form) for e in es]
    idx = {e.id: i for i, e in enumerate(es)}
    cids = sorted(d.concepts)
    descs = [d.concepts[c].description for c in cids]
    held_g = [e for e in held if e.gloss]
    # always the repo's opposites file, so versions with and without opposite training compare on the same queries
    opp_pairs = [tuple(p) for p in yaml.safe_load((ROOT / "training" / "opposites.yaml").read_text(encoding="utf-8"))]
    opp_of = {}
    for a, b in opp_pairs:
        opp_of.setdefault(a, set()).add(b)
        opp_of.setdefault(b, set()).add(a)

    lk_texts, lk_owner = [], []   # every entry's gloss and concept descriptions, as lookup compares them
    for j, o in enumerate(es):
        for t in meaning_texts(o, d):
            lk_texts.append(t)
            lk_owner.append(j)

    def opp_gold(cids_):
        bad = set().union(*(opp_of.get(c, set()) for c in cids_))
        return {j for j, o in enumerate(es) if set(o.concept) & bad}

    skip = R["pairs"].get("opposite_anchors_per_concept", 6)
    opp_queries = [(e.gloss, opp_gold(e.concept)) for e in held_g if set(e.concept) & set(opp_of)]
    opp_queries += [(t, opp_gold([c])) for c in sorted(opp_of)
                    for t in [t for t in triggers(d, c) if t and "|" not in t and "?" not in t][skip:]]
    opp_queries = [(q, g_) for q, g_ in opp_queries if g_]
    w = work
    setups = [("n-gram", lambda: Ngram(), None), ("stock MiniLM", base_encoder, None),
              ("stock MiniLM, static", lambda: Static(w / "static-stock"), w / "static-stock"),
              ("Aussie MiniLM", lambda: Dense(w / "aussie-minilm"), w / "aussie-minilm"),
              ("Aussie static, distilled only", lambda: Static(w / "static-aussie"), w / "static-aussie"),
              ("Aussie static, tuned", lambda: Static(w / "static-aussie-tuned"), w / "static-aussie-tuned")]
    rows = []
    for label, make, path in setups:
        if path and not path.exists():
            continue
        enc = make()
        # meaning -> slang: a held-back gloss should find its own form among all the dictionary's forms
        g = enc.sims([e.gloss for e in held_g], forms)
        r_form = recall_at(g, [{idx[e.id]} for e in held_g])
        # same, but any form of the right concept counts (several entries share a meaning)
        r_concept = recall_at(g, [{i for i, o in enumerate(es) if set(o.concept) & set(e.concept)} for e in held_g])
        # slang -> meaning: a held-back form should find its concept among all concept descriptions
        r_explain = recall_at(enc.sims([clean(e.form) for e in held], descs),
                              [{cids.index(c) for c in e.concept if c in cids} for e in held])
        # opposites: how often lookup would offer an opposite, i.e. an entry of an opposite concept reaches the
        # cut-off, scored as lookup scores (gloss and concept descriptions). Queries: held-back glosses of concepts
        # with an opposite, plus those concepts' triggers past the first few, which the opposite pairs never use
        r_opp = 0.0
        if opp_queries:
            sims = enc.sims([q for q, _ in opp_queries], lk_texts)
            worst = [max((v for v, i in zip(row, lk_owner) if i in bad), default=0.0)
                     for row, (_, bad) in zip(sims, opp_queries)]
            r_opp = sum(w >= R["cutoffs"]["lookup"] for w in worst) / len(worst)
        ref = reference(d, enc, R["cutoffs"]["lookup"])
        gb = gap_benchmark(d, enc) if R.get("gap_benchmark") else {}
        rows.append({"setup": label, METRICS[0]: round(r_form, 3), METRICS[1]: round(r_concept, 3),
                     METRICS[2]: round(r_explain, 3), LOWER[0]: round(r_opp, 3), "opposite_queries": len(opp_queries),
                     **{k: gb[k] for k in GAP if k in gb}, "gap_detail": gb.get("detail"),
                     "size_mb": size_mb(path) if path else None,
                     "reference": f"{ref['passed']}/{ref['required']}", "reference_detail": ref})
    print(f"{len(held)} held-back entries ({len(held_g)} with a gloss); {len(forms)} forms, {len(descs)} concepts")
    print(f"  {'setup':30} {'R@3: ' + ' | '.join(METRICS):58} opp.offered reference  MB")
    for r in rows:
        print(f"  {r['setup']:30} {'      '.join(f'{r[m]:.2f}' for m in METRICS):58} {r[LOWER[0]]:<10.2f} "
              f"{r['reference']:10} {r['size_mb'] or ''}")
    if any(GAP[0] in r for r in rows):
        print(f"  {'gap benchmark':30} {' | '.join(GAP)}")
        for r in rows:
            print(f"  {r['setup']:30} " + "   ".join(f"{r[k]:.2f}" for k in GAP))
    (w / "eval.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return rows


def calibrate(model_spec: str, *, held_only: bool = False, holdout: float = 0.0, quiet: bool = False) -> dict:
    """Cosine scores for plain query -> right entry vs unrelated pairs, compared the way harness.lookup and
    gaps compare them, and the cut-off that best separates them."""
    import numpy as np

    d = load_dictionary()
    model = encoder(model_spec)
    rng = random.Random(R["seed"])
    es = [e for e in entries(d) if e.gloss]
    # for a model trained here, sample the related pairs from the held-back entries only, so they're unseen
    sample_from = [e for e in split(d, holdout)[1] if e.gloss] if held_only else es

    # lookup: a concept trigger against an entry of that concept, a random unrelated entry, and the
    # best-scoring unrelated entry in the whole dictionary (what a query really meets)
    flat = [(i, t) for i, e in enumerate(es) for t in meaning_texts(e, d)]
    pos, neg, hard = [], [], []
    for e in rng.sample(sample_from, 30):
        q = rng.choice(triggers(d, e.concept[0]) or [e.gloss])
        s = model.sims([q], [t for _, t in flat])[0]
        per = best_by((i, v) for (i, _), v in zip(flat, s))
        pos.append((q, e.form, per[es.index(e)]))
        others = [i for i in per if not set(es[i].concept) & set(e.concept)]
        o = rng.choice(others)
        neg.append((q, es[o].form, per[o]))
        o = max(others, key=per.get)
        hard.append((q, es[o].form, per[o]))

    # gaps: a word against every concept's labels (gaps.py's own). Related: a trigger word, leave-one-out.
    # Unrelated: words no concept is about.
    lab_flat = [(cid, t) for cid, ts in concept_labels(d).items() for t in ts if t]
    all_trig = {w for cid in d.concepts for t in triggers(d, cid) for w in re.findall(r"[a-z]+", t.lower())}

    def best_concept(w):   # leave-one-out: a gap word is by definition not a label itself
        s = model.sims([w], [t for _, t in lab_flat])[0]
        return best_by((cid, v) for (cid, t), v in zip(lab_flat, s) if t.lower() != w.lower())

    words = sorted({(t, cid) for cid in d.concepts for t in triggers(d, cid) if t.isalpha() and len(t) > 3})
    gpos = []
    for w, cid in rng.sample(words, 30):
        per = best_concept(w)
        top = max(per, key=per.get)
        gpos.append((w, cid, per[cid], top, per[top]))
    unrelated = [w for w in ("theorem molecule carburettor continent algorithm cathedral telescope proposition "
                             "photosynthesis spreadsheet manuscript volcano harbour orchestra treaty equation "
                             "glacier vaccine sculpture telegraph satellite census ledger archive monastery "
                             "voltage granite chair porridge bowl spoon pebble umbrella kettle").split()
                 if w not in all_trig][:30]
    gneg = []
    for w in unrelated:
        per = best_concept(w)
        top = max(per, key=per.get)
        gneg.append((w, top, per[top]))

    def summary(p, n):
        p, n = np.array(p), np.array(n)
        cands = np.round(np.arange(0.20, 0.90, 0.01), 2)
        acc = [((p >= t).mean() + (n < t).mean()) / 2 for t in cands]
        return {"related": {"p25": round(float(np.percentile(p, 25)), 3), "median": round(float(np.median(p)), 3)},
                "unrelated": {"median": round(float(np.median(n)), 3), "p90": round(float(np.percentile(n, 90)), 3),
                              "max": round(float(n.max()), 3)},
                "best_threshold": float(cands[int(np.argmax(acc))]), "balanced_accuracy": round(float(max(acc)), 3),
                "at": {str(t): {"related_kept": round(float((p >= t).mean()), 3),
                                "unrelated_kept": round(float((n >= t).mean()), 3)}
                       for t in (0.4, 0.45, 0.5, 0.55, 0.6)}}

    # gaps' verdict trusts the nearest concept, so a related word counts only if its nearest concept is right
    gp = [s_top if top == cid else 0.0 for _, cid, _, top, s_top in gpos]
    report = {"lookup_random": summary([x[2] for x in pos], [x[2] for x in neg]),
              "lookup_hardest": summary([x[2] for x in pos], [x[2] for x in hard]),
              "gaps": summary(gp, [x[2] for x in gneg]),
              "gaps_nearest_right": round(sum(top == cid for _, cid, _, top, _ in gpos) / len(gpos), 3),
              "lookup_pairs": {"related": pos, "unrelated": neg, "hardest_unrelated": hard},
              "gaps_pairs": {"related": gpos, "unrelated": gneg}}
    if not quiet:
        print(json.dumps(report, indent=1, default=lambda x: round(float(x), 3)))
    return report


def check(model: str | None = None) -> int:
    """The reference set against the shipped model (or an exported one): what CI and a maintainer can run without
    torch."""
    d = load_dictionary()
    enc = Bundled(model)
    ref = reference(d, enc, enc.m.lookup_threshold)
    for r in ref["checks"]:
        mark = "ok   " if r["pass"] else ("known" if r["known"] else "FAIL ")
        print(f"{mark} {r['kind']:9} {r['query']:34} {', '.join(r['top_concepts'])}")
    print(f"{enc.m.name}: {ref['passed']}/{ref['required']} required checks pass"
          + (f"; known failures now passing: {', '.join(ref['known_fixed'])}" if ref["known_fixed"] else ""))
    return 0 if ref["passed"] == ref["required"] else 1


# --- export / release -------------------------------------------------------------------------------------

def wordnet_version() -> str:
    from nltk.corpus import wordnet as wn

    return f"WordNet {wn.get_version()}"


def toolchain() -> dict:
    from importlib.metadata import PackageNotFoundError, version

    out = {"python": sys.version.split()[0]}
    for p in TOOLCHAIN:
        try:
            out[p] = version(p)
        except PackageNotFoundError:
            out[p] = None
    return out


def git_state() -> dict:
    """The commit a release is built from, for its provenance; a git failure stops the release rather than
    recording a blank commit."""
    def run(*cmd):
        return subprocess.run(["git", *cmd], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()

    return {"commit": run("rev-parse", "HEAD"),
            "dirty": bool(run("status", "--porcelain", "--", "aussiefy/data", "training", "scripts"))}


def export(work: Path, version: str, dest: Path | None = None, extra: dict | None = None) -> Path:
    """Write the tuned static model in the package's own format (aussiefy/static.py reads it with no dependencies):
    float16 rows, the vocabulary in row order, and meta.json with the version, cut-offs and provenance."""
    import numpy as np
    from safetensors.numpy import load_file

    from aussiefy.static import MODEL_DIR, dictionary_fingerprint

    src = work / "static-aussie-tuned"
    vectors = load_file(str(src / "model.safetensors"))["embeddings"].astype("<f2")
    tok = json.loads((src / "tokenizer.json").read_text(encoding="utf-8"))
    vocab = sorted(tok["model"]["vocab"].items(), key=lambda kv: kv[1])
    if [i for _, i in vocab] != list(range(vectors.shape[0])):
        raise ValueError(f"{src}: the tokenizer's ids aren't the rows 0..{vectors.shape[0] - 1} of the vectors")
    if any("\n" in t for t, _ in vocab):
        raise ValueError(f"{src}: a vocabulary token contains a newline, which vocab.txt can't hold")
    dest = dest or MODEL_DIR
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "vectors.f16").write_bytes(np.ascontiguousarray(vectors).tobytes())
    (dest / "vocab.txt").write_text("\n".join(t for t, _ in vocab), encoding="utf-8")
    meta = {"name": R["name"], "version": version, "dims": int(vectors.shape[1]), "rows": int(vectors.shape[0]),
            "unk_token": tok["model"]["unk_token"],
            "added_tokens": [a["content"] for a in tok["added_tokens"] if not a["special"]],
            "lookup_threshold": R["cutoffs"]["lookup"], "gaps_confident": R["cutoffs"]["gaps"],
            "dictionary_sha256": dictionary_fingerprint(),
            "vectors_sha256": sha256(dest / "vectors.f16"), "vocab_sha256": sha256(dest / "vocab.txt"),
            "trained": datetime.date.today().isoformat(),
            "about": f"scripts/train_embedder.py from training/recipe.yaml; report: training/reports/{version}.json",
            **(extra or {})}
    (dest / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {dest}: {meta['rows']} x {meta['dims']}, {size_mb(dest)} MB")
    return dest


def release(args) -> int:
    """Evaluation run (hold-out) and release run (every entry) from the recipe, reference checks on the result,
    then export it into the package and write training/reports/<version>.json."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        print("--version must look like 1.2.0 (training/README.md: Versioning)")
        return 1
    report_path = REPORTS / f"{args.version}.json"
    if report_path.exists() and not args.force and not args.dest:
        print(f"{report_path} exists: versions are immutable; pick a new version (or --force to redo this one)")
        return 1
    work = args.out or home() / "train" / args.version
    git = git_state()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    # 1. evaluation run: hold back entries, train, distil (and the stock comparison), evaluate, calibrate
    trial, holdout = work / "eval", R["holdout"]
    train(trial, holdout)
    distil(trial, holdout, compare=True)
    rows = evaluate(trial, holdout)
    cal = calibrate(str(trial / "static-aussie-tuned"), held_only=True, holdout=holdout, quiet=True)

    # 2. release run: every entry
    final = work / "release"
    train(final, 0.0)
    distil(final, 0.0, compare=False)
    d = load_dictionary()
    ref = reference(d, Static(final / "static-aussie-tuned"), R["cutoffs"]["lookup"])
    if ref["passed"] < ref["required"] and not args.allow_failures:
        failed = [r["query"] for r in ref["checks"] if not r["pass"] and not r["known"]]
        print(f"release model fails the reference set ({', '.join(failed)}): not exported. Fix the recipe or "
              "sources, or move the check to `known` with a reason (--allow-failures to export anyway).")
        return 1

    provenance = {
        "recipe": R, "recipe_sha256": sha256(RECIPE_PATH), "reference_sha256": sha256(ROOT / R["reference"]),
        **({"opposites_sha256": sha256(ROOT / R["sources"]["opposites"])} if R["sources"].get("opposites") else {}),
        **({"gap_benchmark_sha256": sha256(ROOT / R["gap_benchmark"])} if R.get("gap_benchmark") else {}),
        **({"wordnet": wordnet_version()} if (R["sources"].get("wordnet") or {}).get("enabled") else {}),
        "script_sha256": sha256(Path(__file__)), "git": git, "toolchain": toolchain(),
        "training_data": {"entries": len(entries(d)), "pairs": len(pairs(d, entries(d))),
                          "wrong_sense_pairs": len(sense_negatives(d, entries(d))),
                          "opposite_pairs": len(opposite_negatives(d, entries(d)))},
        "evaluation": {r["setup"]: {k: r[k] for k in (*METRICS, *LOWER, *GAP, "reference") if k in r} for r in rows},
        "reference": f"{ref['passed']}/{ref['required']}"}
    dest = export(final, args.version, Path(args.dest) if args.dest else None, extra=provenance)
    shipped = reference(d, Bundled(dest), R["cutoffs"]["lookup"])   # as the package will read it
    if shipped["passed"] != ref["passed"]:
        print(f"the exported model in {dest} scores {shipped['passed']}/{shipped['required']} on the reference set, "
              f"the trained one {ref['passed']}/{ref['required']}: the export is wrong. No report written; restore "
              f"{dest} (git checkout, for the package's) before shipping.")
        return 1

    report = {"version": args.version, "started": started,
              "finished": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "model": json.loads((dest / "meta.json").read_text()), "evaluation": rows,
              "calibration": {k: cal[k] for k in ("lookup_random", "lookup_hardest", "gaps", "gaps_nearest_right")},
              "reference": ref}
    if args.dest:   # a dry run: keep the report with it, not in training/reports
        report_path = Path(args.dest) / "report.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"released {R['name']} {args.version}: reference {ref['passed']}/{ref['required']}; report {report_path}")
    if git["dirty"]:
        print("note: data, training or scripts had uncommitted changes; commit them together with the model")
    return 0


def main() -> int:
    global R, RECIPE_PATH
    recipe = argparse.ArgumentParser(add_help=False)
    recipe.add_argument("--recipe", type=Path, default=ROOT / "training" / "recipe.yaml",
                        help="experimental recipe (default: training/recipe.yaml)")
    selected, argv = recipe.parse_known_args()
    RECIPE_PATH = selected.recipe.resolve()
    R = load_recipe(RECIPE_PATH)
    ap = argparse.ArgumentParser(description=__doc__, parents=[recipe],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rl = sub.add_parser("release", parents=[recipe], help="build, check and export a new version of the bundled model")
    rl.add_argument("--version", required=True)
    rl.add_argument("--dest", help="export here instead of aussiefy/data/model (a dry run)")
    rl.add_argument("--force", action="store_true", help="redo an existing version")
    rl.add_argument("--allow-failures", action="store_true", help="export even if reference checks fail")
    # (any command also takes --recipe PATH, for experiments with a variant of training/recipe.yaml)
    ck = sub.add_parser("check", parents=[recipe], help="the reference set against the shipped model (no torch)")
    ck.add_argument("--model", help="an exported model folder (default: the shipped one)")
    au = sub.add_parser("audit", parents=[recipe], help="inspect training labels without loading a model")
    au.add_argument("--report", type=Path, help="write JSON here instead of stdout")
    sub.add_parser("train", parents=[recipe])
    ds = sub.add_parser("distil", parents=[recipe])
    ds.add_argument("--no-compare", dest="compare", action="store_false", help="skip distilling the base model")
    sub.add_parser("eval", parents=[recipe])
    c = sub.add_parser("calibrate", parents=[recipe])
    c.add_argument("--model", default="bundled", help="ngram, bundled (default), or a model folder")
    c.add_argument("--held-only", action="store_true", help="related lookup pairs from held-back entries only")
    x = sub.add_parser("export", parents=[recipe])
    x.add_argument("--dest", help="folder to write (default: aussiefy/data/model)")
    x.add_argument("--version", required=True)
    for p in sub.choices.values():
        p.add_argument("--out", type=Path, help="working folder (default: $AUSSIEFY_HOME/train)")
        p.add_argument("--holdout", type=float, default=R["holdout"], help="share of entries held back")
    args = ap.parse_args(argv)
    work = args.out or home() / "train"
    run = {"release": lambda: release(args),
           "check": lambda: check(args.model),
           "audit": lambda: audit(args.holdout, args.report),
           "train": lambda: train(work, args.holdout),
           "distil": lambda: distil(work, args.holdout, args.compare),
           "eval": lambda: evaluate(work, args.holdout),
           "calibrate": lambda: calibrate(args.model, held_only=args.held_only, holdout=args.holdout),
           "export": lambda: export(work, args.version, Path(args.dest) if args.dest else None)}[args.cmd]
    rc = run()
    return rc if isinstance(rc, int) else 0


if __name__ == "__main__":
    sys.exit(main())
