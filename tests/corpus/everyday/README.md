# Everyday reference texts

Source texts in the registers people will actually point aussiefy at, for scoring and tuning the engine
across genres. Each group has a manifest (`<group>.yaml`) recording genre, register, tone, source URL,
licence and where the licence was seen. Texts are verbatim apart from whitespace and boilerplate; any other
cut is noted in the item's `excerpt` or `notes`.

| group | texts | what |
|---|---|---|
| `instructions/` | 13 (+1 remote) | recipes, safety and health advice, FAQs, DIY, appliance and gardening guidance |
| `news/` | 11 (+3 remote) | news, press releases, a forecast discussion, notices, sport, obituaries |
| `conversational/` | 14 | letters, dialogue, a play, humour, speeches, Stack Exchange Q&A |
| `workplace/` | 15 | tech docs (Markdown with code), a README, release notes, terms, policies, a job ad, minutes |
| `interfold/` | 15 | the Interfold docs: MDX pages with code, components, tables and maths |

Everything committed here is public domain, CC0, CC BY, CC BY-SA or a permissive software licence; CC
BY and BY-SA texts carry their attribution in the manifest. Texts we may read but not redistribute are only
pointers (`<group>-remote.yaml`), fetched into the gitignored `tests/corpus/local/everyday/` by
`aussiefy dev ingest`. The Interfold docs are committed by the founder's permission and stay under their own
LGPL-3.0 licence; `interfold.yaml` is their ingest manifest, pinned to a commit of the docs repo.

Most sources are American on purpose: the engine has to fix US spelling and Americanisms.

## Remote-only and local inputs

Rockwell's 1911 gardening passage and Kieran's 1927 sports column have US public-domain evidence, but
Australian redistribution status is unconfirmed. Their authors died in 1976 and 1981 respectively; see
[Rockwell's catalogue](https://www.gutenberg.org/ebooks/7123), [Kieran's finding aid](https://findingaids.loc.gov/repositories/19/resources/4301)
and the [National Library's duration guidance](https://www.library.gov.au/services/copyright-library-collections/how-long-does-copyright-last).
They remain local, with pointers in [instructions-remote.yaml](instructions-remote.yaml) and
[news-remote.yaml](news-remote.yaml). The latter also holds two VOA/AP stories. Each remote declaration
explicitly has `excerpts: []`; none grants permission to commit an excerpt.

[interfold.yaml](interfold.yaml) retains its pinned repository, licence evidence and 15 MDX page pointers.
With the `scrape` extra installed, `aussiefy dev ingest tests/corpus/everyday/interfold.yaml` saves missing pages verbatim to
`tests/corpus/local/interfold/`. `--force` refreshes them; `--ref REF` overrides the source pin for a local
experiment. The shared fetcher uses `$AUSSIEFY_HOME/cache/scrape` and its normal user agent. Page statistics
are reported against the pinned manifest; a ref override can legitimately differ. No local text is fetched
by the test suite, and this script does not publish page text or translations.

The everyday regression checks use bounded dial/seed cases over every committed text. Markdown and MDX
are inputs for the planned document translator; the current plain-text engine does not protect their syntax.
The original reference-text level/seed sweep remains separate.

## MIT permission notices

The Rust book excerpt is Copyright (c) 2010 The Rust Project Developers; the Black README excerpt is
Copyright (c) 2018 Łukasz Langa. The Rust release-note excerpt credits The Rust Release Team; its pinned
LICENSE-MIT has no separate copyright line. These three excerpts are redistributed under the MIT option
with the following permission notice. Sources and extraction boundaries are in [workplace.yaml](workplace.yaml).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
