# Hunger degree calibration, 20 October 2026

Conventional appetite severity is separate from style intensity, profanity and exaggeration. This is not
clinical starvation assessment. Existing person/argument restrictions remain: figurative hunger for
power or opportunity does not establish a food appetite. No status, gate, level or stylistic scores change.

## Source certificates

| Source trigger | Band | Evidence and scope |
| --- | --- | --- |
| `hungry@3` | unmarked | [Collins hungry](https://www.collinsdictionary.com/dictionary/english/hungry) describes wanting food without requiring an independently mild or extreme degree. |
| `peckish@2` | mild | [Collins peckish](https://www.collinsdictionary.com/dictionary/english/peckish) specifically supports a slight appetite. Shared British use is separate from severity. |
| `starving@4` | strong | [Collins starving](https://www.collinsdictionary.com/dictionary/english/starving) supports the informal very-hungry sense. The literal deprivation sense is not being assessed. |
| `famished@4` | strong | [Collins famished](https://www.collinsdictionary.com/dictionary/english/famished) supports very hungry in the ordinary appetite sense. |
| `ravenous@5` | strong | [Collins ravenous](https://www.collinsdictionary.com/dictionary/english/ravenous) supports an extreme appetite. Figurative eagerness is separate. |
| `feel pretty? hungry ^end` | unmarked | A composed appetite description, without a separately certified mild/strong degree. The existing whole VP owns its tense and modifier; do not turn a stylistic `pretty` into an invented quantitative threshold. |

## All six HUNGRY target entries

| Entry | Band | Evidence and limits |
| --- | --- | --- |
| `starvin` | strong | A drawl spelling of the informal appetite sense above; dropping the final consonant changes accent, not degree. |
| `peckish` | mild | The lexical source meaning above. |
| `hungry-enough-horse-jockey` | strong | [Warren Fahey's sayings collection](https://warrenfahey.com.au/colloquial-sayings-slangugae/) records the horse/jockey hunger construction. Its conventional impossible appetite comparison and existing ravenous gloss support strong comic hunger; they do not assert a real capacity to eat a horse. The collection establishes attestation, not population frequency or uniquely Australian origin. |
| `hungry-enough-to-eat-the-arse-out-of-a-duck` | strong | [Wiktionary's documented duck family](https://en.wiktionary.org/wiki/could_eat_the_crotch_out_of_a_low_flying_duck) explicitly supports extreme hunger and links the arse variant; Fahey also records the family. This certificate concerns appetite, not whether a caller permits the vocabulary or sexual imagery. |
| `feel-like-a-decent-feed` | unmarked | A composed desire for a meal; `decent` modifies the meal, not the severity of deprivation. Existing feed sourcing remains attached to the entry. |
| `feel-like-some-tucker` | unmarked | A composed desire for food, with no independent extreme degree. Existing tucker sourcing remains attached to the entry. |

These notes paraphrase evidence; they reproduce no dictionary definitions or source passages. Source
inspection was recorded during the 20 October follow-up. Attestation and clinical precision are not inferred
from one another.

## Engine and verification contract

The existing generic degree system compares realised grades. Unqualified hungry keeps its colourful
range; explicit mild or strong source wording needs a known compatible target. External qualifiers stay
attached, so `very hungry` and `slightly hungry` currently stay plain where the dictionary has no compatible
unmarked single-word predicate. Consuming those qualifiers into a different construction is future work,
not permission to produce `very peckish` or silently delete severity. Plans and automatic alternatives
use the same eligibility.

The new original-aware `semantic_degree` check uses the same canonical source detection and grade
composition. It reports a major issue only for one recognised local target with matching concepts and
identical surrounding sentence tokens, a known mild/strong source grade, and incompatible known target
grades. Missing certificates, unknown qualifier compositions, negation, ambiguous matches and other
simultaneous edits can make it abstain. It does not prove the severity of arbitrary agent-written prose,
rate all dictionary families, or infer an `enough` threshold's strength.
