# Part-of-speech tagger weights

`tagger.json.gz` holds the classes, tag dictionary and feature weights of NLTK's averaged-perceptron English
tagger (`averaged_perceptron_tagger_eng`, from the nltk_data package index, where it is listed as MIT
licensed; it derives from Matthew Honnibal's textblob-aptagger, also MIT). `aussiefy/pos.py` re-implements
the tagger's inference, and gives exactly NLTK's tags.

Rebuilt by `scripts/build_pos.py` from the nltk_data zip: the three JSON files, with weights rounded to three
decimals (which changes no tag on the corpus) and gzipped.

- Source: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger_eng.zip
  (sha256 6025f530624335c67d6547d44757b357b4e79bae030a0383e9887a92c1718f0b)
- Upstream: https://github.com/sloria/textblob-aptagger (MIT), https://www.nltk.org/_modules/nltk/tag/perceptron.html

The weights were trained on the Wall Street Journal portion of the Penn Treebank. NLTK's port carries "NLTK
modifications Copyright 2015 The NLTK Project" under the same MIT terms (nltk/tag/perceptron.py).

MIT licence (textblob-aptagger):

    Copyright 2013 Matthew Honnibal

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
    associated documentation files (the "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
    following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial
    portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
    LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
    EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    USE OR OTHER DEALINGS IN THE SOFTWARE.
