# Design review: sourced lexical distinctions, 2026-10-19

Status: Independent review converged; integrated verification passed.

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

Give-best object binding remains an independent availability follow-up. Unreviewed semantic degree and
intentional localisation policies remain product choices; these clear lexical and grammatical fixes do
not silently decide them.

## Verification

At the initial source/listener stage, focused verification passed **493 runtime tests in 17.40
seconds**, covering listener/source regressions, matching, semantic context, noun phrases, engine, fidelity,
schema and genres. That includes 132 listener/source-specific cases. **241 documentation/change-contract
tests passed in 27.22 seconds** after canonical regeneration. Historical positive cases explicitly opt into
their registers and existing gates; these are not changes to default availability.

Ruff, whitespace checks and publication generation/check passed. Canonical golden and changes fixtures
were regenerated and read back. Source URLs alter existing source-count weights, producing seeded choice
and probability changes as well as the intended sense corrections. Case/beer packaging guards were tested
through detected concepts and candidate eligibility, rather than relying on a chosen output alone.
A direct baseline comparison confirmed that all existing status and flag values remain unchanged.
At that stage, 239 proposed source records grew the sidecar from 127 to 366 entry IDs, with 266 new
entry/URL pairs. The combined branch now preserves **all 476 proposed IDs and 530 new entry/URL pairs**
from batches 3–6: **127 to 603 sidecar IDs**, all baseline URLs retained and no duplicate pairs.

No full-suite, release, independent integrated approval or commit is claimed by this branch.

The parent also applied clear batches 5/6 distinctions and 237 source proposals, preserving all existing
sidecar URLs. Mass-noun metadata resolves the former kid-stakes availability limit and prevents plural
goss agreement errors. Generic beer can use attested mass wording instead of inventing packaging or
turning a mass noun into a bare count noun. The combined focused run passed 317 tests in 6.70 seconds;
this is not a full-suite claim.


## Integrated review corrections

The shared mass-number check now rejects count selectors and numerals across nominal/adjectival modifiers,
including `one warm beer`, `another beer`, `every beer` and `each beer`. It reads the sentence's already-cached
POS tags through canonical eligibility, so translation and change options share the rule without retagging
candidates. Mass-compatible `some`, `much` and `no`, and an enclosing container such as `a pint of beer`,
remain valid. Existing unrestricted and plural-only number handling remains unchanged.

Longer dictionary guard concepts retain `root beer` and `ginger beer` as named beverages, rather than
letting generic beer consume their final word. This makes no assumption about their alcohol content.
Shared terminal-argument grammar now recognises bounded multiword `as well as` coordination, including
comma-led forms; incomplete coordinated listener/object captures are declined, while finite-clause
continuations remain available. Nonfinite ambiguous continuations stay conservative.

The contributor guide no longer describes mass-number support as future work or kid-stakes rejection as
an outstanding limitation. The independent give-best binding follow-up remains. Canonical plain guides
and generated public copies were updated together.

The four-finding regression run passed **309 tests in 2.17 seconds**, covering source/listener cases,
matching, semantic context and existing noun-phrase number behaviour, plus canonical changes-option parity.
The dictionary validation, source preservation assertions, Ruff, whitespace and publication generation/check
passed. A separate changes-contract/oracle, engine, schema and publication-test run finished with **266 passed,
1 failed in 231.47 seconds**. The sole failure is the legacy closing-list test requiring `jewels, the lot/whole`;
its seeded output uses the valid existing tail `jewels, and stuff`. No assertion or garnish policy was changed
to conceal that mismatch. Parent integration will reconcile the current seeded fixture/expectation. No full-suite
verification or commit is claimed.

## Parent integration review

The original checkout combines these changes with the earlier temporal/lexical slice and narrator-opinion
controls. Independent review found no remaining findings, with **368 scoped tests passing in 4.90 seconds**.
The parent also observed **509 runtime tests passing in 40.27 seconds**. Existing temporal-argument checks,
opinion permissions, entry IDs, status, flags and semantic-effect metadata are retained.

Every original sidecar URL survives: 212 pre-integration IDs become 688, retaining all 530 new source-branch
entry/URL pairs and removing no earlier references. The earlier 85 entry additions contain 110 URL pairs;
these are retained as well. Source counts remain references, not independent attestation scores.

Generated-output readback exposed self-rewriting coolibah spelling in existing Australian verse. The own-form
triggers were removed while retaining the precise scientific-name trigger; all Waltzing Matilda runs now
preserve their existing slang. Source-weight changes legitimately alter seeded choices: the named stacked
rendering expectation now records stonkered. The closing-list assertion checks every selected tail after
the final list item and before punctuation, instead of requiring one of two first-seed phrases. Selection
weights were not biased to reproduce old fixtures. Golden and changes fixtures were regenerated and read back.

Full-suite success and a commit are not claimed. Severity preservation, the solemn/comic default and the
historical Gettysburg pass gate remain separate work; that gate's threshold and frozen inputs are unchanged.

## Full-suite follow-up

The parent observed **2,789 passed, two expected local-corpus skips and eight failures in 725.12 seconds**.
One genuine argument-check regression treated protective patterns as replacements: a coordinated
`fellow Texans` guard disappeared. Guard status is now derived once from the loaded replacement inventory;
only protective patterns bypass terminal-argument completeness. Adding a replacement through an extension
removes that exception automatically. Independent review found no remaining issues, with 227 focused passes.

The remaining five affected expectations now use explicit small beer bottles, pounds sterling and
emotional versus physical solitude. They retain their original positive assertions and add negatives for
unsupported container/currency assumptions. The parent observed 154 focused passes and 313 broader
integrated passes; these overlapping counts do not replace a full-suite pass. The genuine model-reference
retrieval failure and unchanged historical wording gate remain unresolved.

## Final integration verification

The complete reviewed integration passed **2,825 tests with two expected local-corpus skips in 840.53 seconds**.
Ruff, generated-document checks and provenance checks passed. The user approved enabling comic dictionary
terms in solemn text at Troppo, retaining other defaults off and exact overrides winning. Independent
review verified that matrix across the public surfaces. The frozen historical wording gate now passes;
its anchors, input texts and threshold are unchanged. Earlier failed/pending results above describe prior
snapshots and are superseded by this verification. No package release or main promotion is included.
