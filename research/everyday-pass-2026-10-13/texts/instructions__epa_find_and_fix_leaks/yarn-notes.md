# Yarn notes: instructions__epa_find_and_fix_leaks (-l 4 --vulgarity 1)

Accepted on the second submit (first rejected for "meter").

- Wrong-sense planned phrases: "Give a stuff about" for "Pay attention to" (it means "care at all" and is
  negative-polarity: "didn't give a stuff"); "heaps" for "loads" in "60 loads of dishes" (a dishwasher load,
  not "lots"); "a beaut" for "a good" in "ensure a good seal" (adequate/tight, not excellent). All declined.
  Kept "a geek", "rocks up" (colour arriving in the bowl, a fair figurative fit), "dunny", "the folding stuff".
- Lint/validation false positive: spelling "meter (use metre)" on "If the meter changes" -- a water meter is a
  measuring device, spelled "meter" in Australia too. The engine's own draft made the same error ("If the
  metre changes"). Had to rephrase ("the reading on it") to get accepted. The spelling rule should exempt
  meter as a device (water/gas/parking meter, "the meter" after a device mention).
- Lint suggestion "loads -> heaps" repeats the same wrong sense for "60 loads of dishes".
- Lookups wrong: "hardware store" -> "bottle-o"; "handyman" -> "garbo"; "probably" -> "no bloody way",
  "not on your nelly", "Buckley's chance" (opposite sense); "a good tight seal" -> "a feed", "a legend".
  Empty: "cistern", "plumber", "tap washer". "money" and "check" (suss out) were useful.
- Vocabulary reached for, not in lookup: "cistern" (the standard Australian word for the toilet tank),
  "hardware shop" / "the hardware", "get in a plumber" (hire one), "tradie".
