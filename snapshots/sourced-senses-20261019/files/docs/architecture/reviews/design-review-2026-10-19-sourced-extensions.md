# Design review: sourced lexical distinctions, 2026-10-19

Status: Draft; independent integrated review and complete verification pending.

## Findings

Research identified mappings conflating solitude/loneliness, shouting/scolding, weary/aimless walking,
small/zero amounts, easy tasks/pretence and goods/locations. Historical terms also inferred tree identity,
baggage, construction, police roles, beer content or overflowing beyond their input triggers.
The implementation stores precise concepts and compatible forms in data, preserves negative modals and
location nouns, and merges 239 per-entry source proposals with their component/historical evidence limits.
Automatic slab mappings require an explicitly twenty-four-unit beer package, rather than inferring a count
from any case/carton or trying to enumerate every possible later qualifier. Exact-zero matching retains
exception complements such as nothing-but and minimising nothing-much. Existing status, flags and register
policy remain in force. Readback caught an overbroad experimental adverb trigger splitting
on-his-own-animal; that trigger was removed and the possessive noun phrase has negative regressions.
Existing predicate solitude forms remain available. Waltzing Matilda requires both travelling and a swag;
merely walking or carrying baggage does not establish that combined meaning.

Explicit listener-role binding is included: object possessives come from an explicit listener capture or
object, never the speaking agent. Form compatibility retains the captured listener, direct entry patterns
use the same slot as concept triggers, and standard bend/bent morphology lives in the shared table.
Shared terminal-argument completion declines coordinated nominal objects, partial multiword names and
possessive noun heads, while retaining independent coordinated verbs and finite clauses. Unknown inline
continuations remain conservative rather than being assumed to end the argument.

## What's done well

The changes reuse concept, frame, binding, domain and register checks instead of adding slang-specific core
branches. Source URLs preserve existing records and deduplicate entry/URL pairs. Composed location forms
state component evidence explicitly; a URL is not treated as proof of every trigger or full construction.
The existing PRETENCE concept is reused rather than adding a duplicate meaning.

## Related follow-ups

The generic number heuristic conservatively withholds the mass idiom kid stakes after a singular agreeing
verb. It remains available in other pretence contexts; no bad agreement is emitted. A general mass-number
contract is independent of these lexical corrections. Give-best object binding remains an independent availability follow-up.

## Verification

After the independent review findings, final focused verification passed **493 runtime tests in 17.40
seconds**, covering listener/source regressions, matching, semantic context, noun phrases, engine, fidelity,
schema and genres. That includes 132 listener/source-specific cases. **241 documentation/change-contract
tests passed in 27.22 seconds** after canonical regeneration. Historical positive cases explicitly opt into
their registers and existing gates; these are not changes to default availability.

Ruff, whitespace checks and publication generation/check passed. Canonical golden and changes fixtures
were regenerated and read back. Source URLs alter existing source-count weights, producing seeded choice
and probability changes as well as the intended sense corrections. Case/beer packaging guards were tested
through detected concepts and candidate eligibility, rather than relying on a chosen output alone.
A direct baseline comparison confirmed that all existing status and flag values remain unchanged.
All 239 proposed source records were merged: this branch's sidecar grows from 127 to 366 entry IDs,
with 266 new entry/URL pairs and no duplicates. Earlier separate source additions remain for parent merge.

No full-suite, release, independent integrated approval or commit is claimed by this branch.
