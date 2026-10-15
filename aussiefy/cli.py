"""The `aussiefy` command: a thin shell over the toolkit (aussiefy.harness), yarn mode and the maintainer tools.

    aussiefy "I'm extremely busy" -l 4 -s 7 --explain     # translate (the default command)
    aussiefy yarn story.txt                               # Claude retells it, using the toolkit
    aussiefy yarn-tools brief|lookup|lint|submit story.txt  # yarn mode by hand, an agent as the model
    aussiefy lookup very tired | lint draft.txt | guide | plan story.txt
    aussiefy verify aussie.txt --original story.txt         # a finished translation's problems, with severity
    aussiefy validate | show QUERY | compare | gaps        # the dictionary and how the engine does on texts
    aussiefy embedder status|install|enable|disable|remove
    aussiefy dev ingest|scrape|fragments|harvest|tag|review|round  # maintainers: sources, scraping, rounds

Every command reads the same dictionary (the built-in one plus any --dict files). The toolkit commands
(translate, yarn, lookup, lint, guide, plan, verify) take the same two dials, by number or name, each on its own:
  -l/--level        1 tourist, 2 blow-in, 3 local, 4 larrikin, 5 swaggie (default)
  --vulgarity       0 nan, 1 dad, 2 uncle-bob, 3 tradie (default: the level's own: nan at 1-2, dad at 3-4,
                    uncle-bob at 5); "-l swaggie --vulgarity nan" is full Aussie with no swearing
and -s/--seed where choices are made; translate and plan also --variety, --registers, --region, --unlock; and
translate, plan, lint, verify and yarn --markup for Markdown or MDX documents.

Exit codes: 0 ok; 1 a negative answer (lookup found nothing, lint found issues, verify
found a critical or major problem, show matched nothing); 2 a bad
dictionary, setting or argument; 3 refused by the source policy; 4 an LLM mode fell back to the engine's draft.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys

import yaml
import textwrap
from collections import Counter
from pathlib import Path

from .loader import load_dictionary
from . import claude
from .errors import UserError
from .dialect import ENGLISHES
from .loader import load_genres
from .markup import MARKUPS
from .policy import parse_embellishment, parse_level, parse_vulgarity

FELL_BACK = 4
REFUSED = 3

EPILOG = """examples:
  aussiefy "I'm extremely busy" -l 4        translate: any text that isn't a command is translated
  aussiefy translate story.txt --explain    ... with every decision explained on stderr
  aussiefy yarn story.txt                   Claude retells it as a yarn, checking itself with the toolkit
  aussiefy lookup very tired                Aussie options for a meaning, or what a slang term means
  aussiefy lint draft.txt --original story.txt
                                            what's wrong with an Aussified draft
  aussiefy guide -l larrikin                voice, language limits and craft rules for a level
  aussiefy plan story.txt                   the engine's draft and planned phrases, as JSON

writing your own version with the toolkit (what an agent does):
{workflow}

Text comes from the arguments, a single file, or stdin. The toolkit commands (translate, yarn, lookup,
lint, guide, plan) take the same two dials, by number or name:
  -l/--level        1 tourist, 2 blow-in, 3 local, 4 larrikin, 5 swaggie (default)
  --vulgarity       0 nan, 1 dad, 2 uncle-bob, 3 tradie (default: the level's own: nan at 1-2, dad at 3-4,
                    uncle-bob at 5); "-l swaggie --vulgarity nan" is full Aussie with no swearing
Every command reads the built-in dictionary plus any --dict files.

exit codes: 0 ok; 1 a negative answer (lookup found nothing, lint found issues, show matched nothing);
2 a bad dictionary, setting, file or argument; 3 refused by the source policy; 4 an LLM mode fell back
to the engine's draft."""

PATH_SUFFIXES = (".txt", ".md", ".yaml", ".yml", ".json", ".html")


# --- shared plumbing ------------------------------------------------------------------------------------------

def _csv(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def _dial(parse):
    """An argparse type for a level or vulgarity, by number or name; a bad one is a usage error (exit 2)."""
    def convert(value: str) -> int:
        try:
            return parse(value)
        except UserError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from None
    convert.__name__ = parse.__name__.removeprefix("parse_")
    return convert


def _seed(value: str) -> int:
    if value == "random":
        import random

        seed = random.randrange(1_000_000)
        print(f"seed: {seed}", file=sys.stderr)
        return seed
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"seed must be a whole number or 'random', not {value!r}") from None


def _read(path: str, what: str, *, verbatim: bool = False) -> str:
    """A text file the user named; one that can't be read is a usage error that names it."""
    try:
        with Path(path).open(encoding="utf-8", newline="" if verbatim else None) as source:
            return source.read()
    except FileNotFoundError:
        raise UserError(f"{what}: no such file: {path}") from None
    except UnicodeDecodeError:
        raise UserError(f"{what}: {path} isn't UTF-8 text") from None
    except OSError as exc:
        raise UserError(f"{what}: can't read {path} ({exc.strerror})") from None


def _json_file(path: str, what: str):
    try:
        return json.loads(_read(path, what))
    except json.JSONDecodeError as exc:
        raise UserError(f"{what}: {path}: invalid JSON: {exc}") from exc


def _directory(path: str | None, what: str) -> str | None:
    if path is not None and not Path(path).is_dir():
        raise UserError(f"{what}: no such directory: {path}")
    return path


def _translator(args):
    """The one Translator for this run: the built-in dictionary plus any --dict files."""
    if getattr(args, "_translator", None) is None:
        from .engine import Translator, default_translator

        args._translator = Translator(load_dictionary(_dict_paths(args))) if args.dict else default_translator()
    return args._translator


def _dict_paths(args) -> list[str]:
    for path in args.dict:
        if not Path(path).exists():
            raise UserError(f"--dict: no such file or directory: {path}")
    return args.dict


def _looks_like_a_path(arg: str) -> bool:
    """One word that names a file ("story.txt", "drafts/a"), not text to translate."""
    return not any(c.isspace() for c in arg) and ("/" in arg or "\\" in arg or arg.lower().endswith(PATH_SUFFIXES))


def _text(args, *, verbatim: bool = False) -> str:
    """Text arguments, a single file path, or stdin. A single path-like argument that names no file is an error,
    so a mistyped file name isn't read as the text itself."""
    if args.text and len(args.text) == 1:
        arg = args.text[0]
        if Path(arg).is_file():
            return _read(arg, "text", verbatim=verbatim)
        if _looks_like_a_path(arg):
            raise UserError(f"no such file: {arg} (to use it as the text itself, add a space or quote a sentence)")
    if args.text:
        return " ".join(args.text)
    if sys.stdin.isatty():
        print("reading text from stdin; end it with Ctrl-D (Ctrl-Z Enter on Windows), or see --help",
              file=sys.stderr)
    return sys.stdin.read()


def _policy(args) -> dict:
    return {"level": args.level, "vulgarity": args.vulgarity}


def _steering(args) -> dict:
    """The engine options translate and plan share, as the toolkit's parameters."""
    return {"variety": args.variety, "registers": _csv(args.registers), "regions": _csv(args.regions),
            "unlock": _csv(args.unlock), "english": args.english, "embellishment": args.embellishment}


def _json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _steps(numbered: str, indent: str = "") -> str:
    """Numbered steps, one per line, wrapped for a terminal."""
    return "\n".join(textwrap.fill(step, 110, initial_indent=indent, subsequent_indent=indent + "   ")
                     for step in numbered.splitlines())


def _warn(warnings) -> None:
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)


# --- the toolkit ----------------------------------------------------------------------------------------------

def cmd_translate(args) -> int:
    from .explain import format_explain
    from .markdown import DocumentResult
    from .translation import run

    tr = _translator(args)
    result = run(_text(args, verbatim=args.markdown or args.markup != "text"), translator=tr,
                 seed=args.seed, embedder=args.embedder, rewrite=args.rewrite, surface=args.surface,
                 model=args.model, markdown=args.markdown, markup=args.markup, **_policy(args), **_steering(args))
    fell_back = [] if isinstance(result, DocumentResult) else [r for r in result.rewrites if r.outcome == "fell_back"]
    surface = {} if isinstance(result, DocumentResult) else result.surface or {}
    if args.json:
        _json(result.to_dict())
    else:
        if isinstance(result, DocumentResult):
            sys.stdout.write(result.text)
        else:
            print(result.text)
        if args.explain:
            print("\n" + format_explain(result, show_rejected=not args.brief), file=sys.stderr)
        for r in fell_back:
            print(f"[rewrite] sentence {r.sentence + 1} kept the draft: {r.status}", file=sys.stderr)
        if surface and surface["outcome"] != "applied":
            print(f"[surface] {surface['status']}", file=sys.stderr)
        _warn(result.warnings)
    return FELL_BACK if fell_back or surface.get("outcome") == "fell_back" else 0


def cmd_yarn(args) -> int:
    from .yarn import yarn

    result = yarn(_text(args), seed=args.seed, model=args.model, cache=not args.no_cache, markup=args.markup, english=args.english,
                  embellishment=args.embellishment, translator=_translator(args),
                  **_policy(args))
    if args.json:
        _json(result.to_dict())
    else:
        print(result.text)
        print(f"[yarn] {result.status}" + (f"; tools used: {result.tool_calls}" if result.tool_calls else ""),
              file=sys.stderr)
    return 0 if result.outcome == "applied" else FELL_BACK


def cmd_yarn_tools(args) -> int:
    """Yarn mode's loop run by hand: an agent (or a person) is the model, and each step is one call."""
    from .yarn import brief, dispatch_tool

    source = _read(args.source, "source", verbatim=True)
    session = brief(source, seed=args.seed, markup=args.markup, english=args.english,
                    embellishment=args.embellishment, translator=_translator(args), **_policy(args))
    if args.declined and args.step == "lint":   # each call is a fresh session: lint learns what was declined here
        session.decline(_declined(args.declined))
    if args.step == "brief":
        print("=== SYSTEM ===\n" + session.system)
        print("=== USER ===\n" + json.dumps(session.payload, ensure_ascii=False, indent=1))
        return 0
    if args.arg is None:
        raise UserError(f"yarn-tools {args.step} needs " + ("a query" if args.step == "lookup" else "a draft file"))
    if args.step == "lookup":
        call = {"query": args.arg}
    else:
        call = {"text": _read(args.arg, "draft", verbatim=True).strip()}
        if args.step == "submit":
            call["declined"] = _declined(args.declined) if args.declined else []
    out, accepted = dispatch_tool(session, args.step, call)
    if args.log:
        with Path(args.log).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"step": args.step, "args": call, "result": out}, ensure_ascii=False) + "\n")
    if accepted and args.output:
        Path(args.output).write_text(call["text"] + "\n", encoding="utf-8")
    _json(out)
    if args.step == "lint":
        return 0 if out["ok"] else 1
    return 0 if args.step == "lookup" or accepted else 1


def _declined(path: str) -> list[dict]:
    """A submit's declined phrases: a YAML list of {phrase, reason}."""
    try:
        raw = yaml.safe_load(_read(path, "--declined")) or []
    except yaml.YAMLError as exc:
        raise UserError(f"{path}: not valid YAML ({str(exc).splitlines()[0]}); write a list of "
                        "{phrase: ..., reason: ...}, quoting any value with a colon in it") from None
    if not isinstance(raw, list) or not all(isinstance(d, dict) and isinstance(d.get("phrase"), str)
                                            and isinstance(d.get("reason"), (str, type(None))) for d in raw):
        raise UserError(f"{path}: declined phrases must be a list of {{phrase: ..., reason: ...}}, each a string")
    # the submit tool's own shape: a missing reason is an empty one, which submit sends back
    return [{"phrase": d["phrase"], "reason": d.get("reason") or ""} for d in raw]


def cmd_lookup(args) -> int:
    from . import harness

    out = harness.lookup(" ".join(args.query), limit=args.limit, include_gated=args.include_gated,
                         short=args.short, translator=_translator(args), **_policy(args))
    if args.json:
        _json(out)
        return 0 if out["results"] else 1
    _warn(out["policy_warnings"])
    for r in out["results"]:
        extra = f" [vulgarity {r['vulgarity']}]" if r["vulgarity"] else ""
        extra += f" [gated: {', '.join(r['gated'])}]" if r.get("gated") else ""
        print(f"  {r['form']:<42} L{r['level']} {r['frame']:<13} {r['gloss']}{extra}")
        for riff in r.get("riffs", ()):
            print(f"      riff ({riff['tone']}): {riff['text']}")
    if not out["results"]:
        print(f"  (no match for {out['query']!r} at level {out['level']}) {out['note']}")
    return 0 if out["results"] else 1


def cmd_lint(args) -> int:
    from . import harness

    original = _read(args.original, "--original") if args.original else None
    out = harness.lint(_text(args), original=original, markup=args.markup, english=args.english,
                       embellishment=args.embellishment, translator=_translator(args), suggest=args.suggest,
                       **_policy(args))
    if args.json:
        _json(out)
    else:
        _warn(out["policy_warnings"])
        for i in out["issues"]:
            what = i["phrase"]
            print(f"  ! {i['kind']}: {what}" + (f" -> {i['australian']}" if i.get("australian") else ""))
        for w in out["warnings"]:
            print(f"  ? {w['kind']}: {w['phrase']!r}: {w['why']}")
        for s in out["suggestions"]:
            print(f"  ~ {s['text']!r} could be: {', '.join(s['options'])}")
        warned = f" ({len(out['warnings'])} warning(s))" if out["warnings"] else ""
        print(("ok" if out["ok"] else f"{len(out['issues'])} issue(s)") + warned)
    return 0 if out["ok"] else 1


def cmd_verify(args) -> int:
    from . import harness

    original = _read(args.original, "--original")
    out = harness.verify(_text(args), original=original, markup=args.markup, english=args.english,
                         embellishment=args.embellishment, translator=_translator(args),
                         **_policy(args))
    if args.json:
        _json(out)
        return 0 if out["ok"] else 1
    _warn(out["policy_warnings"])
    for p in out["problems"]:
        if p["severity"] != "info" or args.all:
            where = f" (sentence {p['sentence'] + 1})" if "sentence" in p else ""
            print(f"  {p['severity']:<8} {p['kind']}{where}: {p['phrase']!r}: {p['why']}")
    m, c = out["metrics"], out["counts"]
    print(f"{c['critical']} critical, {c['major']} major, {c['minor']} minor; {m['sentences']} sentences, "
          f"{m['untouched_share']:.0%} left as they were" + ("" if args.all else " (--all lists them)"))
    return 0 if out["ok"] else 1


def _candidates(pairs: list[str]) -> dict[str, str]:
    out = {}
    for pair in pairs:
        name, sep, path = pair.partition("=")
        if not sep or not name or not path:
            raise UserError(f"--candidate takes NAME=FILE, not {pair!r}")
        if name in out:
            raise UserError(f"two candidates named {name!r}")
        out[name] = _read(path, "--candidate", verbatim=True)
    return out


def cmd_judge(args) -> int:
    from . import judge as j

    if args.judge_command == "tally":
        verdicts = [j.Verdict.from_dict(_json_file(f, "verdict"), where=f) for f in args.verdicts]
        _json(j.tally(verdicts))
        return 0
    tr = _translator(args)
    if args.judge_command == "unharnessed":
        eff = tr.effective(**_policy(args))
        original = _text(args)
        if args.prompt_only:
            print(j.unharnessed_prompt(original, level=eff.level, vulgarity=eff.vulgarity, markup=args.markup))
        else:
            print(j.unharnessed(original, model=args.model, markup=args.markup, translator=tr, **_policy(args)))
        return 0
    if args.judge_command == "read":
        packet = j.Packet.from_dict(_json_file(args.packet, "packet"), where=args.packet)
        try:
            verdict = j.read(packet, _json_file(args.report, "report"), judge=args.judge)
        except j.BadReport as exc:
            for problem in exc.problems:
                print(f"  ! {problem}", file=sys.stderr)
            return 1
    else:
        candidates = _candidates(args.candidate)
        original = _read(args.original, "--original")
        if args.judge_command == "run" and args.unharnessed:
            try:
                candidates["unharnessed"] = j.unharnessed(original, model=args.model, markup="auto", translator=tr,
                                                          **_policy(args))
            except claude.Error as exc:
                print(f"[judge] no unharnessed retelling: {type(exc).__name__}: {exc}", file=sys.stderr)
                return FELL_BACK
        packet = j.blind(original, candidates, seed=args.seed, translator=tr, **_policy(args))
        rubric = j.Rubric.load()
        if args.judge_command == "brief":
            Path(args.output).write_text(json.dumps(packet.to_dict(rubric), indent=1, ensure_ascii=False),
                                         encoding="utf-8")
            judging = {k: v for k, v in packet.to_dict(rubric).items() if k in ("instructions", "prompt", "schema")}
            _json(judging)   # what the judge sees: no key
            print(f"packet (with the key) -> {args.output}; judge it, then: aussiefy judge read {args.output} "
                  "REPORT.json", file=sys.stderr)
            return 0
        try:
            verdict = j.run(packet, model=args.model, rubric=rubric)
        except (claude.Error, j.BadReport) as exc:
            print(f"[judge] no verdict: {type(exc).__name__}: {exc}", file=sys.stderr)
            return FELL_BACK
    if args.json:
        _json(verdict.to_dict())
    else:
        print(verdict.card())
    return 0


def cmd_guide(args) -> int:
    from . import harness

    from .guide import style_guide_data

    g = harness.guide(embellishment=args.embellishment, translator=_translator(args), **_policy(args))
    if args.json:
        _json(g)
    else:
        _warn(g["policy_warnings"])
        print(f"Level {g['level']} ({g['level_name']}): {g['voice']}\nLanguage ({g['vulgarity_name']}): "
              f"{g['language']}\nEmbellishment ({g['embellishment_name']}):\n{g['embellishment_guidance']}\n\n"
              f"{g['craft']}"
              f"\n\nWorkflow:\n{style_guide_data().workflow_for('cli')}")
    return 0


def cmd_plan(args) -> int:
    from . import harness

    _json(harness.plan(_text(args), seed=args.seed, markup=args.markup, translator=_translator(args),
                       **_policy(args), **_steering(args)))
    return 0


# --- the dictionary, and how the engine does on texts ----------------------------------------------------------

def cmd_validate(args) -> int:
    d = _translator(args).dictionary
    load_genres()   # genres.yaml: raises on a missing setting, genre or key, or an unknown placement
    by_status = Counter(e.status for e in d.entries.values())
    by_frame = Counter(e.frame for e in d.idioms)
    by_level = Counter(e.incoherence for e in d.idioms if e.status == "active")
    print(f"ok: {len(d.entries)} entries ({dict(by_status)}), {len(d.concepts)} concepts, "
          f"{len(d.patterns)} trigger patterns, {len(d.phonetic)} phonetic rules")
    print(f"idiom frames: {dict(sorted(by_frame.items()))}")
    print(f"active idioms by minimum level: {dict(sorted(by_level.items()))}")
    unused = [c for c in d.concepts if not any(c in e.concept for e in d.idioms)]
    if unused:
        print(f"concepts with no entries (guard concepts hold a longer match on purpose): {', '.join(unused)}")
    _warn(d.warnings)
    return 0


def cmd_show(args) -> int:
    d = _translator(args).dictionary
    q = args.query.lower()
    hits = [e for e in d.entries.values() if q in e.id or q in e.form.lower() or args.query.upper() in e.concept]
    if hits:
        from .dump import dump_entries

        print(dump_entries(hits).rstrip())
    else:
        print(f"no entry matches {args.query!r} (by id, form or concept)", file=sys.stderr)
    return 0 if hits else 1


def cmd_compare(args) -> int:
    from .scrape.harvest import target_recall, vocabulary_overlap

    original = _read(args.original, "compare ORIGINAL")
    target = _read(args.target, "compare TARGET")
    tr = _translator(args)
    outputs = [tr.translate(original, level=args.level, seed=s).text for s in range(args.seeds)]
    rows = target_recall(original, target, outputs, tr.dictionary)
    for before, after, hit in rows:
        print(f"  {'+' if hit else '-'} {after!r:45} (for {before!r})")
    got = sum(hit for *_, hit in rows)
    print(f"aligned spans: reproduced {got}/{len(rows)} of the target's slang ({got / max(len(rows), 1):.0%}) "
          f"across {args.seeds} seeds at level {args.level}")
    vocab = vocabulary_overlap(target, outputs, tr.dictionary)
    have = sum(hit for _, hit in vocab)
    print("dictionary phrases in the target: " + ", ".join(f"{'+' if h else '-'}{p}" for p, h in vocab))
    print(f"vocabulary overlap: {have}/{len(vocab)} ({have / max(len(vocab), 1):.0%}); "
          f"robust to targets that restructure or extend the text")
    return 0


def _drafts(specs: list[str] | None, names: set[str]) -> dict[str, str]:
    drafts = {}
    for spec in specs or ():
        name, sep, path = spec.partition("=")
        if not sep or not path:
            raise argparse.ArgumentTypeError(f"--draft wants NAME=PATH, got {spec!r}")
        if name not in names:
            raise argparse.ArgumentTypeError(f"--draft {name}: no text of that name (have: {', '.join(sorted(names))})")
        drafts[name] = _read(path, f"--draft {name}")
    return drafts


def cmd_gaps(args) -> int:
    from .gaps import report

    texts = {Path(f).stem: _read(f, "gaps FILE") for f in args.files}
    out = report(texts, level=args.level, embedder_spec=args.embedder, limit=args.limit,
                 drafts=_drafts(args.draft, set(texts)), translator=_translator(args))
    if args.json:
        _json(out)
        return 0
    print(f"words the engine left in plain English at level {out['level']} (nearest concept by {out['embedder']}):")
    for g in out["gaps"]:
        near = f"~ {g['nearest_concept']} {g['similarity']:.2f}" if g["confident"] else ""
        print(f"  {g['count']:>3}x {'F' if g['formal'] else ' '} {g['word']:<16} {g['verdict']:<40} {near:<22} "
              f"[{', '.join(g['texts'])}]")
    for name, lines in out.get("literal_lines", {}).items():
        print(f"\n{name}: {len(lines)} line(s) still mostly in the original wording")
        for ln in lines:
            print(f"  {ln['original_wording']:.0%}  {ln['line'][:100]}")
    return 0


def cmd_embedder(args) -> int:
    from . import models

    try:
        if args.action == "install":
            out = models.install(model=args.model, torch=args.torch, from_path=args.from_path, enable=args.enable,
                                 dry_run=args.dry_run)
        elif args.action in ("enable", "disable"):
            on = args.action == "enable"
            out = models.set_bundled(on) if args.which == "bundled" else models.set_enabled(on)
        elif args.action == "remove":
            out = models.remove()
        else:
            out = models.status()
    except subprocess.CalledProcessError as exc:
        raise UserError(f"install step failed ({' '.join(exc.cmd)}). If download.pytorch.org is blocked, try "
                        "--torch pypi; if huggingface.co is blocked, copy a saved model and use --from PATH.") from exc
    _json(out)
    return 0


# --- dev: the original scrape -> tag -> review pipeline -------------------------------------------------------

def _load_staged(path: Path):
    from .scrape.normalise import Staged

    if not path.exists():
        return []
    return [Staged(**{k: v for k, v in raw.items() if k in Staged.__dataclass_fields__})
            for raw in yaml.safe_load(path.read_text(encoding="utf-8")) or []]


def _save_staged(path: Path, items) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump([s.to_dict() for s in items], sort_keys=False, allow_unicode=True),
                    encoding="utf-8")


def cmd_ingest(args) -> int:
    from functools import partial

    from .scrape.fetch import fetch
    from .scrape.ingest import Manifest, ingest

    failed = 0
    for path in args.manifests:
        manifest = Manifest.load(path, ref=args.ref)
        for o in ingest(manifest, partial(fetch, delay=1.0, refresh=args.force), force=args.force):
            where = o.path.relative_to(Path.cwd()) if o.path.is_relative_to(Path.cwd()) else o.path
            detail = {"saved": f"{o.words} words", "present": "already there (--force to re-fetch)",
                      "failed": o.error}[o.status]
            print(f"{o.source.name}: {o.status}, {detail} -> {where}", file=sys.stderr if o.status == "failed" else sys.stdout)
            failed += o.status == "failed"
    return 1 if failed else 0


def cmd_scrape(args) -> int:
    from .scrape import ReferenceOnly, scrape
    from .scrape.normalise import load_staged, save_staged

    out = Path(args.output)
    try:
        staged = scrape(args.urls, _translator(args).dictionary, load_staged(out) if out.exists() else [],
                        source_url=args.source_url, permitted=args.permitted, refresh=args.refresh,
                        log=lambda m: print(m, file=sys.stderr))
    except ReferenceOnly as exc:
        print(f"{exc}. Use it to verify entries by hand, or pass --permitted if you have permission to extract "
              "from it.", file=sys.stderr)
        return REFUSED
    save_staged(out, staged)
    known = sum(1 for s in staged if s.known_as)
    print(f"staged {len(staged)} phrases ({known} already in the dictionary) -> {out}", file=sys.stderr)
    return 0


def cmd_fragments(args) -> int:
    from .scrape.fragments import extract_fragments
    from .scrape.normalise import save_staged

    out = Path(args.output)
    staged = extract_fragments(_translator(args).dictionary)
    save_staged(out, staged)
    print(f"staged {len(staged)} fragments -> {out}; next: aussiefy dev tag {out}", file=sys.stderr)
    return 0


def cmd_harvest(args) -> int:
    from .scrape.harvest import harvest
    from .scrape.normalise import save_staged

    out = Path(args.output)
    staged = harvest(_read(args.original, "harvest ORIGINAL"), _read(args.rewrite, "harvest REWRITE"),
                     _translator(args).dictionary, source=f"harvest:{Path(args.rewrite).name}")
    save_staged(out, staged)
    for s in staged:
        print(f"  {s.form!r:40} {s.source_meanings[0]}", file=sys.stderr)
    print(f"staged {len(staged)} candidates -> {out}; next: aussiefy dev tag {out}", file=sys.stderr)
    return 0


def cmd_tag(args) -> int:
    from .dump import dump_yaml
    from .scrape.normalise import load_staged
    from .scrape.tag import tag_all

    items = load_staged(args.staging)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)   # before the paid calls, not after
    if args.limit:
        items = items[: args.limit]
    tagged = tag_all(items, _translator(args).dictionary, model=args.model, log=lambda m: print(m, file=sys.stderr))
    Path(args.output).write_text(dump_yaml(tagged), encoding="utf-8")
    print(f"tagged {len(tagged)} -> {args.output}; review with: aussiefy dev review {args.output}", file=sys.stderr)
    return 0


def cmd_round(args: argparse.Namespace) -> int:
    """Plan a research round against the dictionary as it was before it; with --write, apply it."""
    from . import rounds
    from .loader import DATA_DIR

    if not (Path(args.directory) / "round.yaml").is_file():
        raise UserError(f"dev round: no round.yaml in {args.directory}")
    config = rounds.RoundConfig.load(args.directory)
    data_dir = Path(_directory(args.data_dir, "--data-dir")) if args.data_dir else DATA_DIR
    plan = rounds.plan_round(config, rounds.base_dictionary(config, data_dir))
    print("\n".join(plan.summary()))
    if args.write:
        d = plan.write(data_dir)
        print(f"wrote entries/{config.output} and concepts.yaml; the dictionary loads: {len(d.entries)} entries, "
              f"{len(d.concepts)} concepts")
    return 0


def cmd_review(args) -> int:
    import yaml

    from .scrape.review import plan_review

    d = load_dictionary(_dict_paths(args), data_dir=_directory(args.data_dir, "--data-dir"))
    try:
        tagged = yaml.safe_load(_read(args.tagged, "dev review TAGGED")) or []
    except yaml.YAMLError as exc:
        raise UserError(f"{args.tagged}: invalid YAML: {exc}") from exc
    plan = plan_review(tagged, d, args.data_dir)
    for line in plan.summary:
        print(line)
    diff = plan.diff()
    print("\n" + (diff or "(no changes)"))
    if args.apply and diff:
        plan.apply(tuple(args.dict))   # only once the result has loaded in a scratch copy
        print(f"applied to {plan.scraped_path} and {plan.sources_path}")
    elif diff:
        print("dry run; re-run with --apply to write these changes")
    return 0


def _did_you_mean(word: str, text: list[str], commands) -> None:
    """A word that is nearly a command is still translated, but say so: it may be a typo ("lnit draft.txt"). Only
    for two words of text at most: "how are you" or "plain English words" is a sentence."""
    if len(" ".join(text).split()) > 2:
        return
    close = difflib.get_close_matches(word, list(commands), n=1, cutoff=0.75) if word.isalpha() else []
    if close:
        print(f"note: {word!r} isn't a command, so it is translated as text (did you mean {close[0]!r}?)",
              file=sys.stderr)


# --- the parser -----------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    from .claude import DEFAULT_MODEL
    from .guide import style_guide_data
    from .models import DEFAULT_EMBEDDER

    workflow = _steps(style_guide_data().workflow_for("cli"), indent="  ")
    p = argparse.ArgumentParser(prog="aussiefy", description="Rewrite plain English as Australian English. "
                                "Without a command, arguments go to `translate`.",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=EPILOG.format(workflow=workflow))
    dictionary = argparse.ArgumentParser(add_help=False)
    dictionary.add_argument("--dict", action="append", default=[], metavar="PATH",
                            help="extra entry file or directory (repeatable)")
    level = argparse.ArgumentParser(add_help=False)
    level.add_argument("-l", "--level", type=_dial(parse_level), default=5, metavar="LEVEL",
                       help="how Aussie: 1-5 or tourist, blow-in, local, larrikin, swaggie (default 5, swaggie)")
    policy = argparse.ArgumentParser(add_help=False, parents=[level])
    policy.add_argument("--vulgarity", type=_dial(parse_vulgarity), metavar="VULGARITY",
                        help="how vulgar: 0-3 or nan, dad, uncle-bob, tradie (default: the level's own; "
                             "levels 1-2 nan, 3-4 dad, 5 uncle-bob)")
    seeded = argparse.ArgumentParser(add_help=False)
    seeded.add_argument("-s", "--seed", type=_seed, default=0,
                        help="seed for the weighted choices (default 0: the same text gives the same output); "
                             "'random' picks one and prints it to stderr so the run can be repeated")
    as_json = argparse.ArgumentParser(add_help=False)
    as_json.add_argument("--json", action="store_true", help="print the full result as JSON")
    text = argparse.ArgumentParser(add_help=False)
    text.add_argument("text", nargs="*", help="text, a file, or (none) stdin")
    marked = argparse.ArgumentParser(add_help=False)
    marked.add_argument("--markup", choices=MARKUPS, default="text",
                        help="translate only the prose of a markdown or mdx document, keeping code, tags, links, "
                             "front matter and headings exactly (auto: tell from the text; default text)")
    steering = argparse.ArgumentParser(add_help=False)
    steering.add_argument("--variety", type=int, default=0, metavar="N",
                          help="choose among the N best-fitting slang terms only (1 = always the best fit); "
                               "default 0 = weighted over every eligible term")
    steering.add_argument("--registers", help="comma list from current,dated,archaic (default: per level)")
    steering.add_argument("--region", dest="regions", help="comma list of region tags to prefer, e.g. qld")
    steering.add_argument("--unlock", help="comma list of flags whose gated entries become eligible, or 'all'")
    english = argparse.ArgumentParser(add_help=False)
    english.add_argument("--english", choices=ENGLISHES, default=None,
                          help="the English the text is in, for US and UK words Australians say differently "
                               "(faucet -> tap at every level; British pants -> undies only with uk). Default auto: "
                               "American spelling marks a text as American; none turns the swaps off")
    embellished = argparse.ArgumentParser(add_help=False)
    embellished.add_argument("-e", "--embellishment", type=_dial(parse_embellishment), metavar="EMBELLISHMENT",
                             help="how much liberty the telling takes: 0-2 or deadset (straight), dinkum (a genuine "
                                  "voice), troppo (a performed yarn). Default: for translate, the text's genre's "
                                  "own (a story troppo, a letter dinkum, news, instructions, docs and official "
                                  "prose deadset); for a retelling and its checks (yarn, plan, lint, verify, "
                                  "guide) dinkum")
    toolkit = [dictionary, policy, as_json]
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    t = sub.add_parser("translate", parents=[*toolkit, steering, english, embellished, seeded, marked, text],
                       help="the rule engine's translation (default)")
    t.add_argument("--explain", action="store_true", help="report every decision on stderr")
    t.add_argument("--brief", action="store_true", help="with --explain, omit rejected candidates")
    t.add_argument("--markdown", action="store_true", help="translate Markdown prose; preserve code, links and headings")
    t.add_argument("--embedder", choices=("ngram", "none", "bundled", "local"), default=None,
                   help="concept-detection fallback (default ngram)")
    t.add_argument("--surface", action="store_true", help="LLM fluent-surface rewrite (needs anthropic)")
    t.add_argument("--rewrite", choices=("hard", "all"),
                   help="hand whole sentences to Claude to say in Aussie drawl: the difficult ones, or all")
    t.add_argument("--model", default=DEFAULT_MODEL, help="Claude model for --surface and --rewrite")
    t.set_defaults(func=cmd_translate)

    y = sub.add_parser("yarn", parents=[*toolkit, english, embellished, seeded, marked, text],
                       help="Claude retells the whole text as an Aussie yarn, using the toolkit")
    y.add_argument("--model", default=DEFAULT_MODEL, help="Claude model")
    y.add_argument("--no-cache", action="store_true",
                   help="neither reuse nor save accepted yarns (default: kept in cache/yarn under $AUSSIEFY_HOME, "
                        "~/.aussiefy unless set)")
    y.set_defaults(func=cmd_yarn)

    yt = sub.add_parser("yarn-tools", parents=[*toolkit, english, embellished, seeded, marked],
                        help="yarn mode by hand: an agent is the model (brief, then lookup, lint and submit)")
    yt.add_argument("step", choices=("brief", "lookup", "lint", "submit"))
    yt.add_argument("source", help="the original text file")
    yt.add_argument("arg", nargs="?", help="lookup: the query; lint and submit: the draft file")
    yt.add_argument("--declined", metavar="FILE", help="submit: a YAML list of {phrase, reason} declined; lint: "
                                                       "phrases not to suggest again")
    yt.add_argument("-o", "--output", metavar="FILE", help="submit: where an accepted yarn is saved")
    yt.add_argument("--log", metavar="FILE", help="append every call and its result to this JSONL file")
    yt.set_defaults(func=cmd_yarn_tools)

    lk = sub.add_parser("lookup", parents=toolkit, help="Aussie options for a meaning, or what a term means")
    lk.add_argument("query", nargs="+")
    lk.add_argument("--limit", type=int, default=8)
    lk.add_argument("--include-gated", action="store_true", help="also show entries held back as doubtful")
    lk.add_argument("--short", action="store_true", help="each result as its form, gloss, frame, level and vulgarity")
    lk.set_defaults(func=cmd_lookup)

    ln = sub.add_parser("lint", parents=[*toolkit, marked, english, embellished, text], help="lint an Aussified draft (exit 1 if issues)")
    ln.add_argument("--original", metavar="FILE", help="the source text: also check length, names and numbers")
    ln.add_argument("--no-suggestions", dest="suggest", action="store_false",
                    help="skip the optional more-Aussie suggestions (a whole engine translation): faster")
    ln.set_defaults(func=cmd_lint)

    vf = sub.add_parser("verify", parents=[*toolkit, marked, english, embellished, text],
                        help="check a translation against its original: problems with severity (exit 1 if any "
                             "critical or major)")
    vf.add_argument("--original", metavar="FILE", required=True, help="the source text")
    vf.add_argument("--all", action="store_true", help="also list info items (sentences left as they were)")
    vf.set_defaults(func=cmd_verify)

    jd = sub.add_parser("judge", help="blind, rubric-scored comparison of translations of one original (LLM)")
    jsub = jd.add_subparsers(dest="judge_command", required=True, metavar="STEP")
    cands = argparse.ArgumentParser(add_help=False)
    cands.add_argument("original", help="the original text file")
    cands.add_argument("--candidate", action="append", required=True, metavar="NAME=FILE",
                       help="a translation to judge (2 to 8 of them, with --unharnessed counted)")
    jb = jsub.add_parser("brief", parents=[*toolkit, seeded, cands],
                         help="the blind packet, for an agent to judge (prints what the judge sees)")
    jb.add_argument("-o", "--output", default="judge-packet.json", help="the packet, with the key to unblind it")
    jr = jsub.add_parser("run", parents=[*toolkit, seeded, cands], help="judge with Claude and print the report card")
    jr.add_argument("--unharnessed", action="store_true",
                    help="add a model's own retelling (no toolkit) as a candidate, the reference point")
    jr.add_argument("--model", default=DEFAULT_MODEL, help="Claude model to judge (and retell) with")
    jrd = jsub.add_parser("read", parents=[dictionary, as_json],
                          help="validate an agent's report against its packet and print the report card")
    jrd.add_argument("packet")
    jrd.add_argument("report")
    jrd.add_argument("--judge", default="", help="who judged it, to record in the verdict")
    ju = jsub.add_parser("unharnessed", parents=[*toolkit, marked, text],
                         help="a model's own retelling, the reference")
    ju.add_argument("--prompt-only", action="store_true", help="print the brief for an agent to answer instead")
    ju.add_argument("--model", default=DEFAULT_MODEL)
    jt = jsub.add_parser("tally", help="average verdicts (JSON from judge run/read --json) across texts")
    jt.add_argument("verdicts", nargs="+")
    jd.set_defaults(func=cmd_judge)

    gd = sub.add_parser("guide", parents=[*toolkit, embellished], help="voice, language limits and craft rules for a level")
    gd.set_defaults(func=cmd_guide)

    pl = sub.add_parser("plan", parents=[dictionary, policy, as_json, steering, english, embellished, seeded, marked, text],
                        help="the engine's draft, planned phrases and difficult sentences (JSON)")
    pl.set_defaults(func=cmd_plan)

    v = sub.add_parser("validate", parents=[dictionary], help="validate the dictionary and print stats")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("show", parents=[dictionary], help="show entries by id, form substring or concept")
    s.add_argument("query", help="an entry id or concept, or part of a form")
    s.set_defaults(func=cmd_show)

    cp = sub.add_parser("compare", parents=[dictionary, level],
                        help="how much of a target translation's slang the engine reproduces (a benchmark)")
    cp.add_argument("original", help="the plain-English text")
    cp.add_argument("target", help="an Aussified version of it to measure against")
    cp.add_argument("--seeds", type=int, default=10, help="seeds to translate with (default 10)")
    cp.set_defaults(func=cmd_compare)

    gp = sub.add_parser("gaps", parents=[dictionary, level, as_json],
                        help="words the engine keeps leaving in plain English, with nearest concepts")
    gp.add_argument("files", nargs="+", help="plain-English texts to scan")
    gp.add_argument("--embedder", choices=("ngram", "bundled", "local"),
                    help="default: the embedder in use (see aussiefy embedder status)")
    gp.add_argument("--draft", action="append", metavar="NAME=PATH",
                    help="an Aussified draft of the text NAME: also list its lines left in the original wording")
    gp.add_argument("--limit", type=int, default=40)
    gp.set_defaults(func=cmd_gaps)

    em = sub.add_parser("embedder", help="the embedding model lookup and gaps use: bundled by default, or install "
                                         "a sentence-transformers one")
    em.add_argument("action", choices=["status", "install", "enable", "disable", "remove"])
    em.add_argument("which", nargs="?", choices=["bundled", "local"], default="local",
                    help="with enable/disable: the bundled static model, or an installed local one (default)")
    em.add_argument("--model", default=DEFAULT_EMBEDDER, help="with install")
    em.add_argument("--torch", default="cpu", choices=["cpu", "pypi", "skip"],
                    help="cpu: the small CPU-only PyTorch build (default); pypi: PyPI's default build; skip: "
                         "PyTorch is already installed")
    em.add_argument("--from", dest="from_path", metavar="PATH",
                    help="copy a saved sentence-transformers model folder instead of downloading")
    em.add_argument("--enable", action="store_true", help="enable it straight after installing")
    em.add_argument("--dry-run", action="store_true", help="print the steps without running them")
    em.set_defaults(func=cmd_embedder)

    dev = sub.add_parser("dev", help="maintainers: ingest sources, the scrape -> tag -> review pipeline, research rounds")
    dsub = dev.add_subparsers(dest="dev_command", required=True, metavar="STEP")
    ig = dsub.add_parser("ingest", help="fetch a manifest's sources (pages, repo files) into local text files")
    ig.add_argument("manifests", nargs="+", metavar="MANIFEST", help="YAML manifests (see aussiefy.scrape.ingest)")
    ig.add_argument("--force", action="store_true", help="re-fetch sources already saved")
    ig.add_argument("--ref", help="git ref for repo sources, instead of the manifest's pinned one")
    ig.set_defaults(func=cmd_ingest)
    sc = dsub.add_parser("scrape", parents=[dictionary], help="extract phrases from URLs or saved HTML into a staging file")
    sc.add_argument("urls", nargs="+", metavar="URL_OR_FILE")
    sc.add_argument("-o", "--output", default="data/staging/scraped.yaml")
    sc.add_argument("--source-url", help="the page a saved HTML file came from (required for a saved file: it is "
                                         "recorded and checked against the source policy)")
    sc.add_argument("--refresh", action="store_true", help="ignore the fetch cache")
    sc.add_argument("--permitted", action="store_true",
                    help="override data/source_policy.yaml for a source you have permission to extract from")
    sc.set_defaults(func=cmd_scrape)
    fr = dsub.add_parser("fragments", parents=[dictionary],
                         help="stage slang fragments found inside existing idioms (dunny in 'country dunny')")
    fr.add_argument("-o", "--output", default="data/staging/fragments.yaml")
    fr.set_defaults(func=cmd_fragments)
    hv = dsub.add_parser("harvest", parents=[dictionary],
                         help="stage slang from an Aussified rewrite of a plain text (an agent's, or a person's)")
    hv.add_argument("original")
    hv.add_argument("rewrite")
    hv.add_argument("-o", "--output", default="data/staging/harvest.yaml")
    hv.set_defaults(func=cmd_harvest)
    tg = dsub.add_parser("tag", parents=[dictionary], help="LLM-propose schema fields for staged phrases")
    tg.add_argument("staging")
    tg.add_argument("-o", "--output", default="data/staging/tagged.yaml")
    tg.add_argument("--model", default=DEFAULT_MODEL)
    tg.add_argument("--limit", type=int)
    tg.set_defaults(func=cmd_tag)
    r = dsub.add_parser("review", parents=[dictionary], help="diff tagged proposals against the dictionary; --apply to accept")
    r.add_argument("tagged")
    r.add_argument("--apply", action="store_true")
    r.add_argument("--data-dir", help="dictionary data directory (default: the package's)")
    r.set_defaults(func=cmd_review)
    rd = dsub.add_parser("round", help="apply a research round's verified verdicts (research/<round>/round.yaml)")
    rd.add_argument("directory")
    rd.add_argument("--write", action="store_true", help="write the entries and concepts (after validating them)")
    rd.add_argument("--data-dir", help="dictionary data directory (default: the package's)")
    rd.set_defaults(func=cmd_round)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    commands = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
    # `aussiefy "some text" -l 4` is shorthand for `aussiefy translate "some text" -l 4`
    implicit = not argv or (argv[0] not in commands and argv[0] not in ("-h", "--help"))
    if implicit:
        argv.insert(0, "translate")
    args = parser.parse_args(argv)
    if implicit and len(argv) > 1:
        _did_you_mean(argv[1], args.text, commands)
    try:
        return args.func(args)
    except (UserError, claude.Unavailable, argparse.ArgumentTypeError) as exc:   # the user can fix these; bugs raise
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        # `aussiefy show "" | head`: stdout's reader left, so stop quietly, as Unix tools do (the recipe in the
        # Python docs' signal notes). The CLI writes to no other pipe: the API's socket errors arrive as
        # claude.Unavailable. Pointing stdout at devnull stops a second error when Python flushes it at exit.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())
