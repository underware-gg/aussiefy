## deadset

- Accepted after 1 submit. One planned phrase, "every man and his dog" for "everyone"; right sense, kept.
- Lint suggested "the good oil" / "the dinkum oil" for my "the lowdown" (information); useful, took "the good oil" once. It warned "you want to" said 3 times as a repeated phrase: two are the original's own ("if you want to rename...", "if you want to keep..."), so at deadset the warning pushes against sentence-for-sentence.
- The brief's rules conflict on headings: the system prompt says a heading's "words may be Aussified like any others", the MARKUP note says keep every heading "exactly as it is". I kept headings and link texts exact (link texts are page titles).
- Technical terms (branch, commit, push, revert, merge, repository, default branch, collaborators) all kept; the Aussie went into the prose ("stuff up", "chip in on", "chuck in").

## dinkum

- Accepted after 1 submit; "every man and his dog" kept.
- The dinkum ENGINE_DRAFT tags insults onto technical docs aimed at the reader: "a GitHub account and a repository, ya drongo", "GitHub Desktop, ya mug", "fix the mistake, ya flamin' mongrel", plus "Listen, Additionally," (an opener on top of a connective) and "Stone the crows, GitHub flow is...". The tag picker needs to know the genre (technical: no insults, no tags in a doc's prose).
- OPENINGS for a docs page ("Back in the day,", "Okay, so.", "Picture this:") don't fit; I started with the heading, as the markup requires.
- Lint suggestions were good: "a squiz" for "a look", "heaps" for "a lot". It also offered "a Captain Cook" and "a geek" for "a look", fine as slang but "a geek" is easy to misread in a developer doc.

## troppo

- Accepted after 1 submit. The single planned phrase ("every man and his dog") fit.
- Validation gap: lint's markup check (markup_changed) catches a missing or altered code span (I tested: `increase-test-timeouts` is flagged), but not an added one. My first troppo draft brought in an inline code span of my own (`daves-stuff-2`, as a joke bad branch name) and lint passed it; a re-run on a scratch copy with it in passed too. Under the MARKUP rule ("keep every inline code span... exactly") a new span is new code in the doc. I took it out and checked code spans, link targets, link texts and headings against the original with a script.
- Troppo on technical docs: the colour went into the connecting prose ("That's the whole shoppin' list", "yer own little paddock", "Bob's yer uncle", "Ask me how I know."), with every term of art, link and code span left alone. "Picture this:" (offered) worked as the first prose line under the kept heading, not before it.
- Lint suggested "too easy" / "sweet as" for "Easy:"; took "Too easy".
