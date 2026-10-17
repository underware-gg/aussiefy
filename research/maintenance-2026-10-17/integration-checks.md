# Available integration checks, 17 October 2026

At capture time the website was not built. Its planned repository is `underware-gg/aussiefy-web`. These checks exercise the
available installed engine/toolkit interfaces; no website Smart/Basic route or browser latency is inferred.
The [captured evidence](integration-checks.json) records the exact source/settings, implementation digests,
model version, checked outcomes and explicit verification limits. Its Git base plus dirty flag identifies
the then-uncommitted prose corrections; it does not claim the base contains those corrections.
The initial capture remains historical. `final_recheck` separately repeats all six MCP tools, CLI
lint/verify/submission and missing-key fallback against committed prose slice `328d8d1`; all eight recorded
runtime-input hashes match that commit. The bundled model remains 1.2.0.

## Observed interfaces

- The current Codex agent read the portable skill, obtained a real `yarn-tools brief` and looked up tiredness
  and delight through the installed CLI from outside the checkout. Its own draft retained Rob, the station,
  30 minutes, tiredness, the train's arrival and the resulting delight. All three planned phrases fit and
  were kept: knackered, over the moon and rocked up. No declined phrases were needed.
- `yarn-tools lint`, `verify --original` and `yarn-tools submit` returned exit 0. Submission was accepted with
  no problems and the saved output matched the submitted draft. Verification's only informational item
  reports the deliberately unchanged first sentence. This is one actual agent workflow, not a claim of
  comprehensive linguistic fidelity or a separate Codex CLI/MCP client registration.
- A real Python MCP SDK client launched `python -m aussiefy.mcp_server` over stdio from outside the checkout.
  It discovered and called all six tools: guide, lookup, plan, translate, lint and verify. Each returned the
  requested Swaggie/Dad settings and the same resolved numeric profile. The translated Markdown kept
  Australian, Rob, the 30-second lower bound and `get_user()`; verification accepted it.
- The optional built-in API client was exercised with no current process API key and cache disabled. It
  returned exit 4, an authentication-unavailable reason and the unchanged deterministic draft. This verifies
  the fallback boundary; live provider execution remains unverified. Existing offline real-SDK serialization
  and provider-neutral session tests remain part of the full suite.

## Performance and launch limits

The earlier [core performance study](../document-refinement-2026-10-15/README.md#semantic-fallback-performance)
measured explicit semantic and n-gram paths, with input/code hashes and complete-result parity. It did not
establish which future UI labels select those paths. No new timing claim is made while model training and
the complete test suite contend for the machine.

Before web launch, verify actual request routing/configuration, public API behaviour, browser end-to-end
latency, cold/warm costs and bounded long-input behaviour in the new application. Choose whether its own
backend lives at same-origin `/api` and whether a separate public API needs `api` hosting when that application
is shaped. A future domain choice does not itself provision a website or API.

The user provisionally selected `aussiefy.au`. Subsequent coordination confirms the website agent has begun
package support on `web-support` in a separate `aussiefy-web-support` worktree, initially based on `2028a88`.
It is handling hosted MCP options before a changes builder and will rebase onto the committed prose fixes
before overlapping engine work. That coordination does not establish a built or deployed website.

## Reproduction

Use an installed checkout with the MCP extra. Pass the evidence's level, vulgarity, embellishment,
document type and JSON document overrides consistently to `yarn-tools brief/lookup/lint/submit`, `verify`
and all six MCP calls. The source, accepted draft and per-call arguments are retained in the evidence.
The existing `tests/functional/test_retelling.py` also exercises the actual stdio entry point and an
SDK-blocked neutral session; the complete suite covers surface parity and provider serialization.
