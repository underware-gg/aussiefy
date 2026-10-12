# aussiefy

Rewrites plain English as Australian slang, on two independent dials: how Aussie it gets (level 1-5, `tourist`
to `swaggie`) and how rude it may be (vulgarity 0-3, `nan` to `tradie`). A deterministic, seeded rule engine
does the translating from a YAML slang dictionary; optional Claude-powered modes smooth the result or retell a
whole text as a yarn.

```
$ aussiefy "I'm extremely busy." -l 4 -s 7
I'm flat out like a lizard drinking.
```

## Install

Requires Python 3.10+.

```sh
pip install "git+https://github.com/underware-gg/aussiefy"            # core: PyYAML only
pip install "aussiefy[llm] @ git+https://github.com/underware-gg/aussiefy"   # + Claude modes (yarn, --surface, --rewrite)
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

The same text, level and seed always give the same output. See [docs/usage.md](docs/usage.md) for the full
guide: every command, the dictionary, yarn mode, the MCP server and how the engine works.

## License

[MIT](LICENSE)
