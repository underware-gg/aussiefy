"""Swears per 100 words, for every level x vulgarity, over the reference texts and seeds 0-4."""
import glob, json, re, sys
from aussiefy import Translator
tr = Translator()
d = tr.dictionary
texts = [open(f).read() for f in sorted(glob.glob("tests/corpus/reference/*.txt"))]
texts += [l for l in open("tests/corpus/sentences.txt").read().splitlines() if l.strip()]
grid = {}
for level in range(1, 6):
    for v in range(4):
        words = swears = top = 0
        for t in texts:
            for seed in range(5):
                out = tr.translate(t, level=level, vulgarity=v, seed=seed).text
                ws = re.findall(r"[a-z']+", out.lower())
                words += len(ws)
                s = [d.swear_strength(w) for w in ws]
                swears += sum(1 for x in s if x)
                top += sum(1 for x in s if x == v and v)
        grid[f"{level},{v}"] = (round(100 * swears / words, 2), round(100 * top / words, 2))
json.dump(grid, open(sys.argv[1], "w"))
print("level  " + "  ".join(f"{n:>13}" for n in ("nan", "dad", "uncle-bob", "tradie")))
for level in range(1, 6):
    print(f"{level:>5}  " + "  ".join(f"{grid[f'{level},{v}'][0]:>6} ({grid[f'{level},{v}'][1]:>4})" for v in range(4)))
