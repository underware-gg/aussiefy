# Local reference texts (not committed)

Copyrighted texts we test against live here, one `.txt` file each. Everything in this folder except this
README is gitignored. The repo holds only pointers to public copies in `tests/corpus/remote.yaml`. To get
them, run:

    pip install -e '.[scrape]'
    aussiefy dev ingest tests/corpus/remote.yaml tests/corpus/everyday/*-remote.yaml

That downloads each page, cuts out the excerpt between its start and end markers, and saves it here.
`tests/functional/test_local_reference.py` then runs the well-formedness checks on every file in this folder, plus
text-specific checks such as `test_moloch_specifics`. With the folder empty, those tests skip.

You can also drop any other `.txt` file here to test against it privately.

Aussie versions of a local text (from an LLM, a person, or yarn mode) go next to it as
`<name>_<who>.target`, e.g. `moloch_llm_unharnessed.target`. They can't be fetched, so keep your own copy.
Compare and lint them with:

    aussiefy compare tests/corpus/local/moloch.txt tests/corpus/local/moloch_llm_unharnessed.target
    aussiefy lint -l 5 --original tests/corpus/local/moloch.txt < tests/corpus/local/moloch_llm_unharnessed.target

## Retelling a copyrighted text

A full retelling of a copyrighted text is a derivative of it, so it stays here, uncommitted, like the source.
The repo commits at most a short excerpt of it, under a notice header (see
`research/retellings-2026-10-11/harnessed/moloch.txt`). To produce the full retelling yourself:

1. Fetch the source as above, so `tests/corpus/local/moloch.txt` exists.
2. Retell it with yarn mode, either through the API:

       pip install -e '.[llm]'
       aussiefy yarn tests/corpus/local/moloch.txt -l 5 > tests/corpus/local/moloch_yarn.target

   or as an agent working the yarn loop by hand with
   `research/retellings-2026-10-11/yarn_tools.py` (`brief`, `lookup`, `lint`, `submit moloch DRAFT`), which saves
   the accepted yarn here as `moloch_yarn_harnessed.target`.
3. Compare and lint it against the source with the commands above.
