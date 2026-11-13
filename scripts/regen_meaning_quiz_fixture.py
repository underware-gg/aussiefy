"""Regenerate the current real quiz response after intentional dictionary/model/quiz changes."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from aussiefy import Translator, meaning_quiz

    request = {'seed': 7, 'level': 5, 'vulgarity': 0, 'embellishment': 0}
    result = {'request': request, 'lookup_embedder': 'bundled',
              'response': meaning_quiz(translator=Translator(lookup_embedder='bundled'), **request)}
    path = ROOT / 'tests/fixtures/meaning-quiz.json'
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {path.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
