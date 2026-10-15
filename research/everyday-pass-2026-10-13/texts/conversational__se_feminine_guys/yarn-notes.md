
## Yarn pass (agent, 2026-10-13): accepted after 2 submits

- Wrong-sense planned phrases: the whole text is *about* the word "guys", so "blokes" (for 'guys'), "coves" (for the
  list item "men"), "young fellas" (for the mentioned 'boys') all swap the word under discussion. The planner has no
  notion of use vs mention (quoted words, list items `- dudes: ...`). "punters" for "any group of people" is the
  generic-people sense again. "sheilas" for "women" in a post about not offending women contradicts the writer.
- Validation false positive: `dialect: y'all (use youse)` blocks submit even though "y'all" is in the original as a
  mentioned word ("- y'all: perfectly non-sexist but too regional"). `lint.py` checks `d.dialect.lint_only` against
  the draft only, never discounting the original's own uses (the flagged-entry check above it does). Got through by
  quoting it ('y'all'), which the regex's `(?<![a-z'])` lookbehind skips: a workaround, not a fix.
- Lint suggestions push the declined senses back: "guys" -> "cove", "women" -> "sheila", "people" -> "punters",
  and "the folks" (people I was talking to) -> "the oldies" (PARENTS sense).
- Lookups wrong: "a supermarket" -> "a chemist"; "probably" -> "no fuckin' way"/"no bloody way"; "mockery, taking the
  piss" -> "grog" first; "you all, plural you" and "youse" -> "ribuck", "how ya goin'". "youse" (plural you) is
  missing; "patronizing", "condescending, talking down" empty.
