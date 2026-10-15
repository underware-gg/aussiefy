# aussiefy

Rewrites plain English as Australian slang, with level (1-5, `tourist` to `swaggie`),
vulgarity (0-3, `nan` to `tradie`) and embellishment (0-2, deadset/dinkum/troppo) controls. A deterministic, seeded rule engine
does the translating from a YAML slang dictionary; optional Claude-powered modes smooth the result or retell a
whole text as a yarn.

```
$ aussiefy "I'm extremely busy." -l 4 -s 7
I'm flat out like a lizard drinking.
```

## Install

Requires Python 3.10+. These commands install the `v0.1.0` release. Releases are on `main`;
development continues on `dev`. A full commit SHA can be used in place of the tag.

```sh
pip install "git+https://github.com/underware-gg/aussiefy@v0.1.0"            # core
pip install "aussiefy[llm] @ git+https://github.com/underware-gg/aussiefy@v0.1.0"   # + Claude modes (yarn, --surface, --rewrite)
```

Other extras: `mcp` (the `aussiefy-mcp` server), `embeddings`, `scrape`, `dev`. For development, clone the
repo and `pip install -e '.[dev]'`.

## Usage

```sh
aussiefy "Are you crazy?"                        # translate at level 5 (swaggie)
aussiefy story.txt -l 3 --vulgarity nan          # a file, level 3, no swearing
echo "I'm exhausted." | aussiefy -l 4 -s random  # stdin, a random seed (printed to stderr)
aussiefy "Are you crazy?" --explain              # explain every decision
aussiefy yarn story.txt                          # Claude retells it as a yarn (needs [llm])
```

```python
from aussiefy import translate

translate("I'm extremely busy.", level=4, seed=7).text
```

The rule engine gives the same output for the same text, dials, settings and seed. See [docs/README.md](../README.md) for the full
documentation: guides, every command, the dictionary, yarn mode, the MCP server and how the engine works.

## License

[MIT](../../../LICENSE). The bundled embedding model is derived from Apache-2.0 and MIT licensed models: see
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md).

See [translation controls](../functional/translation-controls.md) for the embellishment dial, genre/dialect handling and extended MDX, [verification](../functional/verification.md), [ingestion](../contributor/ingestion.md) and [judging](../contributor/judging.md).
