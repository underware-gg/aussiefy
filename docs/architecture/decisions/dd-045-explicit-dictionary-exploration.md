# DD-045: Explicit dictionary discovery and clean names

Status: Accepted
Date: 2026-10-23
Extends: [DD-008](dd-008-one-toolkit-thin-surfaces.md), [DD-040](dd-040-term-evidence-and-usage.md), [DD-043](dd-043-typed-idiom-construction.md)

## Context

The Community Dictionary needs entry pages, explicit discovery, reproducible random examples and clean
Aussie handles. These explain vocabulary without asserting that a discovered term fits an arbitrary source
sentence. Construction editors also need compatible changes to parts, preserving the rest of the expression.

Rob approved package order 4 → 5 → 3+6 → 7 on 23 October. Slice 4 must therefore expose the current metadata
without prematurely changing the unreleased changes/card contract coordinated in slice 6.

## Decision

`explore.py` is the toolkit boundary for stable entry listing, one full card, random entry and clean name
suggestion. Python, CLI and MCP use the same functions. Listing is ordered by ID, with intersecting concept
and theme filters; offset defaults to 0, page size to 20, capped at 100. Random entry uses one context-keyed
seeded roll over all eligible entries, not a page. Hosted `lookup_limit` caps entry pages too.

Discovery shares canonical dial, register and theme gates. Explicit `include_gated` admits held-back terms
with their reasons, never omitted entries; it does not unlock translation. New discovery cards include the
existing evidence/attestation metadata and public theme names. Tag tiers, lowest default tier and dictionary
identity join the shared contract in their planned slices. No second eligibility system is introduced.

Lookup reports `matched`, `nothing_fits`, `no_word_yet` or `not_in_dictionary` alongside existing prose.
Recognition uses its existing bounded source readings and the same direct-form matcher used for ranking.
Entries the dials reject are matched and scored only when no eligible offer or prior recognition exists,
using the same matcher and entry scorer, so an offered result pays nothing for them. Imagery matching
likewise records recognition before permissions. No second ranking logic or general semantic parser is
introduced.
A filtered page may additionally be `page_exhausted`, distinct from an empty eligible set.

Meanings waiting for a word (ED13) are concepts that no non-omitted entry, image or construction family
expresses, and none of whose triggers the dialect table swaps for the Australian word ("trash can" becomes
"bin"). Rob ruled on 25 October that an image, a construction or a dialect swap counts as a word. The set is
computed once on the loaded dictionary so extension concepts count. Only genuine meanings are
listed (Rob, 24 October): a concept that keeps its words as written by design, a guard or the holding
concept, declares `no_entries: true`. That data marker replaces a name or description heuristic: the loader
refuses an entry, image or construction for any such concept. The engine itself assigns the holding concept,
so the loader also refuses a dictionary, overlay included, that removes its marker. Each listed meaning
carries `plain` wording and `examples`, which a test proves detect it for the bundled dictionary; the loader
warns about a listed meaning without them, since extension dictionaries may add concepts. Rob approved the
bundled wording and examples on 25 October. The listing shares `list_entries`'
paging. Lookup claims `no_word_yet` only on evidence, for a meaning established in context, or matched
across the whole query and not ruled out there; fuzzy similarity never claims it. Policy-blocked entries
are checked for recognition cheapest first: a held term, then its meaning by spelling, then by the model. Its
original precedence was `matched`, `nothing_fits`, `no_word_yet`, then `not_in_dictionary`.
[DD-046](dd-046-lookup-meaning-evidence.md) supersedes that precedence for established wordless meanings;
a meaning with an existing word that the settings block is still `nothing_fits`.

`names.py` owns catalogue validation and deterministic handle assembly, with no I/O, translator factory or
account state. The loader reads `names.yaml`. Clean dictionary entries supply adjectives and phrase parts;
a reviewed literal bank supplies Australian things, nicknames and places. Only active, unheld, Australian,
unthemed, non-insulting entries with vulgarity 0 and no slots may supply a generated name. Catalogue loading
checks structure and existing references; eligibility is checked at generation, so a valid overlay can
reclassify a referenced entry without breaking unrelated translation. Parts and assemblies reject known
profanity and any known themed or insulting form, including garnish, omitted vocabulary and literal uses: this
name policy is stricter than lint's permission to preserve literal subject matter.

Shapes are `descriptive`, `place` and `phrase`. Seeds select a shape and index its finite Cartesian pool
without materialising that pool. At most 32 assemblies are checked within a shape; this bounded limit is
an implementation default, chosen to handle an unsafe boundary combination without an unbounded search.
The curated names are not attestation claims. The host checks uniqueness and changes the seed on a clash.
A missing catalogue returns `nothing_fits` for existing custom dictionaries.

`variations` takes a family and complete role-to-ingredient mapping from a constructor result. It changes
one role at a time and calls the existing constructor with all remaining parts fixed. Each offer has
already passed whole-expression checks and carries its complete text, evidence and spans. This avoids a
parallel policy or a second splice path. Source/output selections and rendering remain in the later contract
work; this operation does not infer an arbitrary sentence's meaning from a construction ID.

## Consequences

Whether a borderline concept is a genuine meaning or a guard is curation, recorded in data and open to
review; a meaning whose words sit under a neighbouring concept is listed until a curator tags them.
Pages are stable for a fixed dictionary/settings snapshot; offsets do not promise stability across updates.
Random choices are reproducible, and held-back vocabulary is discoverable without changing translation
permissions. The shared contract's later update still has one coordinated place to add tier fields.

Name quality depends on the reviewed bank and known forms, not a universal insult classifier. The catalogue
has finitely many handles and cannot promise availability. Literal place/creature names require curation
when expanded. Construction variation cost is proportional to compatible ingredients and roles, rather
than their full Cartesian product; each result is safe to inspect as a complete construction, not as a
promise of contextual sentence fit.
