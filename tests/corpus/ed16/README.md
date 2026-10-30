# ED16 source and grammar trials

`phase-b-labels.json` preserves the 704 original project-authored synthetic cases from phase B
(`7a9970e`), including classifications and limitations. Its SHA-256 is
`7b79debd6687ec1d4d13a638b900d81bccdbcb48cf07e3ed951e1dfb57ef6497`.
It is regression evidence, not a sourced language-quality benchmark or exhaustive pattern expansion.

The cases comprise 661 negative candidate-exposure checks, 42 positive/control cases and one argument
preservation case. `phase-b-controls.json` retains baseline eligible entries and recognised concepts:
only 31 positive cases had an eligible entry. The other 11 must not be reported as functioning swaps.
The beer-garden ruling permits unchanged natural wording without requiring a component beer synonym.

The functional replay checks every eligible candidate at the labelled span, rather than trusting a random
selected output. Number and state/voice requirements can safely reject an output while retaining a source
meaning. Adjective-role checks instead reject an incorrect source meaning in both translation and lookup.
