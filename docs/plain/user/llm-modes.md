# Model-assisted polishing and retelling

The rule engine runs offline and produces repeatable drafts, but they can read like word swaps. Your agent
can use the toolkit to polish or retell them, with the dictionary supplying genuine slang. Claude, Codex
and other agents follow the same [writing workflow](agents.md).

The commands below use the optional built-in API client to run that work automatically. Its guarantees are
in the [LLM modes reference](../functional/llm-modes.md); it is one client of the shared harness.

## Before you start

1. Install the `llm` extra: `pip install "aussiefy[llm] @ git+https://github.com/underware-gg/aussiefy@v0.2.0"`
   (or `pip install -e '.[llm]'` from a clone).
2. Set `ANTHROPIC_API_KEY`, or log in with an `ant auth login` profile.

Every mode uses `claude-opus-5-5` unless you pass `--model`.

## Smooth the joins

```sh
aussiefy story.txt -l 5 --surface
```

Claude rewrites the draft for flow, keeping every phrase the engine planned and adding no new slang.

## Rewrite the sentences the dictionary can't carry

```sh
aussiefy speech.txt -l 5 --rewrite hard   # only the formal, difficult sentences
aussiefy speech.txt -l 5 --rewrite all    # every sentence
```

Add `--explain` to see which sentences were rewritten and why.

## Retell a whole text as a yarn

```sh
aussiefy yarn story.txt -l 5
aussiefy yarn story.txt -l 5 --vulgarity nan --json
```

Claude retells the text using the toolkit (lookup and lint) and must pass the same checks an agent would.
This gives the most natural result: it can change tense, pace and dialogue, which rules can't.

## If Claude isn't available

Nothing is lost: each mode falls back to the engine's own draft, prints the reason on stderr (for example
`[yarn] kept draft: ...`) and exits with code 4.

Accepted sentence rewrites and yarns are cached in `cache/rewrite/` and `cache/yarn/` under
`$AUSSIEFY_HOME` (default `~/.aussiefy`), so repeating those runs gives the same text, offline. Use
`aussiefy yarn story.txt --no-cache` to request a fresh yarn without reading or writing that cache.
`--surface` is not cached: each run asks Claude again.
