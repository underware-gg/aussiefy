# Package integration follow-through, 18 October 2026

Continues [the maintenance plan](../maintenance-2026-10-17/README.md) after the website agent's W10/W3 work
and Dad ratings were integrated at `0e12b9b`. No model retraining or release promotion is part of this slice.

## Installed-package verification

[The probe](probe_integrations.py) runs against a locally built, unreleased wheel installed into a temporary
target directory. Its working directory is outside the checkout. The parent and stdio child both verify
which package they imported. [Captured results](integrations.json) retain every runtime file's digest, the
driver/dependency versions, discovered tools, call arguments and canonical response digests. Every imported
package file also matches the wheel's payload; the wheel digest is retained.

- All six tools run through the actual stdio entry point and the SDK's Streamable HTTP transport over ASGI.
  Every successful response exactly matches the shared toolkit. HTTP uses an injected bundled-model translator;
  stdio resolves its default against an empty temporary home.
  Translation keeps the emoji, Australian, Rob, 30 and protected `get_user()`; verification accepts it.
- The restricted HTTP server hides unlock/gated/custom-config controls, rejects Custom, caps text/original
  at 180 code points, query at 24 and lookup results at three. Every text/original boundary is exercised;
  emoji also verifies the character-count unit. Extra hidden arguments keep the toolkit defaults. These
  arbitrary probe limits are fixtures, not website tier policy.
- Both servers advertise read-only, non-destructive, idempotent and closed-world tools.
- Both changes fixtures validate against the schema packaged in the wheel, reproduce exactly and retain
  byte-identical translation output. Output regions and each chosen alternative's region slice correctly.

The HTTP probe uses the SDK's real HTTP encoding/decoding and ASGI application in-process, in stateless
JSON-response mode. It opens no TCP listener and contacts no deployed host. It does not establish site
authentication, rate limits, deployment, browser latency or registration inside a separate agent client.

## Browser offsets

W3 already counts Unicode code points. Its schema and guide previously said only “character offsets”, which
leaves JavaScript consumers vulnerable to UTF-16 indexing after emoji. This slice documents the existing unit
and adds regression coverage for emoji, combining marks, joined emoji, all three translation routes and mask
positions. It preserves contract version 1 and every translation.

[The Node probe](probe_browser_offsets.mjs) applies an actual alternative from the Python API using the
guide's `Array.from` approach. [The result](browser-offsets.json) retains the selected region and successful
swap, and confirms ordinary JavaScript string slicing would select the wrong region. This checks consumer
mechanics; it does not claim the website has implemented its editor.

## Initial Basic-only changes captures

[Measurements](changes-performance.json) use the existing benchmark, five warm samples per operation, six
roughly 5,000-character everyday texts per setting and two lookup configurations. **Both translate in Basic
mode:** `Translator.lookup_embedder` controls lookup/gaps; translation needs its own `embedder` argument.
These captures do not compare Basic and Smart. They retain settings, input/code hashes
and all 36 case rows. They describe this capture on one developer machine, not a browser or deployment SLA.

| Lookup backend | Settings | Median changes/translate | Slowest case |
|---|---|---:|---:|
| n-grams | Website defaults | 1.22× | 1.49× |
| n-grams | Swaggie/Troppo/Tradie | 1.16× | 1.36× |
| n-grams | All-garnish stress | 1.41× | 1.50× |
| Bundled model | Website defaults | 1.10× | 1.37× |
| Bundled model | Swaggie/Troppo/Tradie | 1.20× | 1.69× |
| Bundled model | All-garnish stress | 1.50× | 2.17× |

The existing criterion is each setting's **median** ratio at most 1.5, not a per-case ceiling. All meet it
in these captures. The unused lookup configuration cannot explain timing differences between runs; this is
not evidence of a bundled-model cost. Keep the outliers visible and measure the actual site's routes and
load before setting its latency expectations. The local website checkout currently
contains scaffolding and a health route, so translation-service and browser checks remain with its build.

## Explicit Basic/Smart capture

[The explicit mode driver](measure_matching_modes.py) calls the shared translation router with each
translation embedder, verifies the resolved policy and activated scorer, and checks translation/changes text
parity. Both modes use the same translator and lookup configuration. [The capture](matching-modes.json)
retains five warm samples' median per operation, all 36 cases, corpus/settings/code hashes and runtime hashes.
It ran after the complete pytest suite finished, against the same wheel outside the checkout.

| Translation mode | Settings | Median changes/translate | Slowest case | Median budget ≤1.5 |
|---|---|---:|---:|---|
| Basic | Website defaults | 0.93× | 3.16× | Met |
| Basic | Swaggie/Troppo/Tradie | 1.61× | 1.87× | **Not met** |
| Basic | All-garnish stress | 1.13× | 1.51× | Met |
| Smart | Website defaults | 1.10× | 1.36× | Met |
| Smart | Swaggie/Troppo/Tradie | 1.40× | 2.46× | Met |
| Smart | All-garnish stress | 1.14× | 1.84× | Met |

Basic's Swaggie median is 1.606, above the existing criterion. Several cases also measure the extra changes
work faster than plain translation. These inversions and outliers make the local wall-clock comparison too
variable for a reliable cost estimate; the capture does not establish their cause or a runtime regression.
The failed criterion is retained, rather than replaced by a more favourable run.

Observed median Smart/Basic ratios over matched cases are 1.16×, 1.08× and 0.93× for plain translation,
and 1.10×, 1.17× and 1.13× with changes, in the table's settings order. The same variability applies: values
below one are not evidence that Smart or the changes builder saves work. Controlled measurements and the
website's actual routes still need checking before asserting a latency budget or a stable Smart/Basic ratio.

## Reproduction

Install `.[dev]` and `jsonschema` into a temporary environment, build a wheel with `python -m build --wheel`,
then install that wheel into a separate directory with `pip install --no-deps --target WHEEL_SITE WHEEL`.
Run the probe from outside the checkout, using that directory as `PYTHONPATH`:

```sh
PYTHONPATH=WHEEL_SITE python /path/to/aussiefy/research/maintenance-2026-10-18/probe_integrations.py --wheel WHEEL --output /tmp/integrations.json
node /path/to/aussiefy/research/maintenance-2026-10-18/probe_browser_offsets.mjs < /tmp/integrations.json
```

The performance command is `python scripts/benchmark_changes.py --repeats 5 --output /tmp/changes.json`.
Changing that benchmark's translator lookup backend still leaves translation in Basic mode. The explicit
mode driver is `python research/maintenance-2026-10-18/measure_matching_modes.py --output /tmp/matching-modes.json`.
It calls the shared `aussiefy.translation.run` routing seam with explicit `embedder=None`/`"bundled"` and
`_changes=False`/`True`. The public convenience wrappers do not expose `embedder`. Resolved policy and the
activated scorer cache verify n-gram/Basic versus bundled/Smart; lookup configuration stays identical.
Do not overwrite these historical capture files when repeating the checks.

## Verification

The complete pre-commit suite passed: **2,212 tests, two expected local-corpus skips, 1,768.57 seconds**.
Ruff, whitespace and generated-publication checks pass. An independent reviewer exactly reproduced the
installed-wheel integration report and Node swap, matched all 94 runtime package hashes to the wheel and
checkout, and passed all 48 focused changes/masks tests. The corrected mode driver's small wheel-backed
probe also verifies both resolved policies, actual scorer activation and output parity. Final independent
review reproduced all 36 explicit-mode output hashes, parity checks and rendering counts, verified every
fingerprint and recomputed all timing summaries. No findings remain for this integration/documentation
slice; this does not clear the failed performance criterion.

## Remaining work

Package-side W10/W3 integration is verified here. The website still needs a tagged release containing those
features and its pin-time checks. It owns its service routes, policy composition,
authentication and browser/editor implementation. Live provider execution and actual agent-client registration
also remain unverified. The local Basic/Swaggie changes-overhead budget miss needs a controlled timing recheck;
no performance acceptance is claimed here. Model 1.2.0 remains in place; meaning-specific training and a refreshed unknown-word
benchmark still need shaping as described in the earlier maintenance record.
