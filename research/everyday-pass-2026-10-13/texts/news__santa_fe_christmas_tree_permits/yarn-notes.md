# Yarn notes: news__santa_fe_christmas_tree_permits (accepted after 1 submit)

- Wrong-sense planned phrase: "bush" for "forest" in "forest health" / "Local forest health experts" (a
  forestry term; the engine wrote "bush health experts"). Declined. Lint then suggested "forest" -> "bush"
  twice more, same problem.
- Riffs for "bush" ("miles from the nearest servo", "nothin' but flies and gum trees") don't suit a
  government notice about New Mexico; not used.
- Lint false positives: `repeated` "cut" (x3, the subject of the notice); `name_dropped` "Christmas Trees"
  (just title case in "Pre-cut Christmas Trees", not a name). Suggestion "kids" -> "littlie"/"little fella"
  is wrong register for Year 4 students in news.
- Not in the engine: "Fourth graders" -> "Year 4"; I kept both.
