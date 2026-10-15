# Yarn notes: instructions__nps_yellowstone_faq

## deadset
- Wrong-sense planned phrases (declined):
  - "bush" for "forest". "national forest" is a US land category the Forest Service runs, a term of art.
  - "Not on your nelly" for the factual "No." about wilderness. It's a scornful refusal, not an official answer.
  - "Parliament House" for "Congress". It's the real US Congress that hasn't acted, so localising it changes a fact.
- Planned phrases I kept: "lob", "flat chat" ("summer's flat chat" is a stretch for a season but it works), "Nah, nah", "creeks".
- Lookups that came back wrong or empty:
  - "fall season" returned "come a gutser / come a cropper" (falling over).
  - "highest" returned "high as a kite".
  - "job" returned "job {obj}" (to punch) and "a dog's breakfast".
  - "recommend" returned "tell ya what".
  - "booking", "queue", "be patient", "dangerous" and "volcano" came back empty.
- Lint false positives:
  - "repeated_phrase: 'at feet metres' x3" and "'million acres about' x3". These are the metric brackets the brief asks for.
  - "the latest" flagged as GOSSIP, suggesting "a goss". The phrase is about wildlife sightings, not gossip.
  - "tribe" got "mob" suggested for a US tribe. That's an Aboriginal-Australian self-designation and the wrong fit here.
- Lint name_dropped "United States" was a fair catch: I'd written "lower 48 states" and put the name back. Accepted on the first submit.

## dinkum
- The ENGINE_DRAFT at dinkum appends "ya flamin' mongrel" to the reader instruction "buy your pass online before you lob". That's an insult aimed at the reader in an instructions text, which the genre forbids. It also opens a question with "Bugger me,". I didn't use either.
- Same three declines. Lint suggested "yonks" for "a long time" in "for a long time to come". "yonks" usually means since long ago, so I left it.
- Accepted on the first submit.

## troppo
- Lint at troppo kept suggesting the declined senses: "forest/forests/wilderness/the backcountry -> bush" and "Congress -> Parliament House". Lint doesn't know they were wrong-sense, and a wilderness designation isn't "bush" either.
- My first troppo draft opened "Right, so". The style guide bans it, but lint didn't flag it. Worth a lint rule.
- The setting was clear. I kept the FAQ's Q-and-A shape and the safety line straight ("they mean it ... Stay out"), and put the colour on the name story, the acreage rivalry and the Congress line ("Over fifty years and counting", from 1972).
- Accepted on the first submit.
