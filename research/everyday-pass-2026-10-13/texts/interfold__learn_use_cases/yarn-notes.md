## Yarn pass (harness), 2026-10-13

Accepted on the first submit.

- Wrong-sense planned phrase: "knock together" for "build" in "Before you build an auction" (it means quick and rough, the opposite of careful design for a security-sensitive E3 program). Declined. Lint kept suggesting it afterwards.
- The engine draft uses level-5 drawl ("wanna", "ya", "yer", "'ave", "adds 'em") in developer docs classed as "official" genre, against the genre guidance. The drawl even reached inside a `<LinkCard>` body ("on yer computer").
- Lookups wrong or empty: "collude" returned "the joint" (The place) and "donger" (Penis), both nonsense matches. "corrupt" and "in cahoots" came back empty; I used "get in cahoots" (general English, common in Australia).
- Brief: the genre is "official", which fits docs well enough (plain register), but at level 5 it's unclear how much colour is allowed. I went with light idiom in the connecting prose ("ticks these boxes", "chip in", "stuff up", "the catch is") and kept the front matter, import, headings, table, inline code, links and LinkCard components verbatim. DIFFICULT_SENTENCES lists technical terms ("aggregate", "computation", "template", "validation") that must stay as they are.
- Validation: the MDX structure check passed with prose edited around inline code and links. No false positives.
