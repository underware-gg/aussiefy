# Historical Gettysburg gate diagnosis

19 October 2026. No threshold, anchor, source, target or benchmark configuration has been changed.
This diagnosis compares committed `11aa20c` with the uncommitted narrator-opinion and sourced-meaning
integration. The [observed anchors](gettysburg-gate-diagnosis.json) record all ten seeds on both sides.

## Observed regression

Coverage changes from **15/25 (60%) to 14/25 (56%)**. Exactly one anchor changes: `diggers livin'`.
The old `brave men` trigger introduced SOLDIERS, permitting `diggers`; the corrected BRAVE mapping
produces `brave bastards`. The earlier explanation attributing this score drop to the poor-buggers
correction was incorrect. Both meaning corrections remain appropriate independently of this metric.

Bravery does not establish a soldier's occupation. The engine has local grammatical subjects, arguments
and text mood; it does not establish entity roles or resolve references across this speech. Nearby war
vocabulary cannot reliably distinguish soldiers from civilian rescuers, witnesses or medics. Restoring
the unconditional mapping would discard explicit courage and infer identity without a supported rule.

The gate checks target words anywhere across ten outputs, without checking the source-aligned use. For
example, its `those brave bastards` anchor, aligned to `they`, still hits because those words occur at
the correctly translated `brave men`. Passing this metric alone does not demonstrate correct meaning.

## Missing targets

Ten misses already existed at `11aa20c`; the eleventh is the corrected soldier mapping.

| Anchor | Diagnosis |
|---|---|
| `notion` | No mapping for proposition; introducing an ordinary synonym solely to recover a point would not establish better Australian writing. Commercial and technical senses require distinction. |
| `stoush findin' out` | Investigative complements are a useful independent improvement, but testing may remain inconclusive: an attempted test is not necessarily a completed discovery. |
| `we've gathered` | Archaic assembly constructions are a useful independent coverage gap. Distinguish `we are met here` from passive `we are met by guards/with hostility`, retaining tense and complements. |
| `battlefield` | Another reference assertion explicitly requires `battle-field` to remain unchanged. Modernising the spelling would be a separate policy change. |
| `carked it` | The existing solemn/comic rejection prevents this valid death idiom. There is currently no public override for that rule. |
| `diggers livin'` | The corrected bravery mapping accounts for the score regression; do not restore unsupported soldier identity. |
| `mightn't … notice` | The target weakens the source's `will` to `might`. Attention/negation paraphrases must retain certainty. |
| `rabbit` | Plain `say` does not establish extended, rambling speech; any added editorial judgement needs an appropriate permission and compatible arguments. |
| `determination` | Devotion and determination are not interchangeable in every context. Preserve the source's loyalty/dedication. |
| `haven't carked … nothin'` | The target turns `shall not have died` into a statement about the past, losing modal force. |
| `nelly` | A standalone emphatic refusal adds a narrator reaction; it is not an automatic synonym for `in vain`. |

## Direction and next work

The user requested more information, rather than approving removal of the pass gate. Keep it unchanged
while evaluating independently useful construction support and the unresolved tone policy. The separate
curated expression benchmark and meaning/grammar checks remain in force.

The hard solemn/comic rule exposes a real configurability gap against the project's direction that
detected signals feed resolved settings. An explicit advanced override can preserve current defaults;
whether Troppo itself should permit deliberate comic treatment of solemn source material is a product
decision. Do not silently choose that default to recover a benchmark word.

Explicit severity is settled separately: automatic translations must preserve stated degree in both
directions. Narrator opinion does not override it. Reuse the existing intensity axis with reviewed
concept policy and known-degree evidence; historical default intensity values remain heuristic until
their candidate families have been reviewed. This requirement is recorded but not implemented here.

## Subsequent resolution

The user approved enabling the shared `solemn_comic_terms` permission at Troppo, with other defaults off
and exact overrides winning. The full integration then passed 2,825 tests with two expected skips,
including the unchanged historical wording gate. The diagnostic measurements above describe the earlier
false-default snapshot; no anchors, input texts or thresholds were changed.
