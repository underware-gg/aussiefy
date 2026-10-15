# Classic Australian texts

Public-domain Australian poems and stories with plenty of period Australianisms: bush and larrikin
slang, droving and selection vocabulary, Irish-Australian dialect. They are here as source material for
extracting Australianisms and as test input for the translator. Each `.txt` file holds one complete poem,
or one named story or chapter. It is plain UTF-8 text with no headers or licence boilerplate. Verse keeps
its line breaks, and stanzas are separated by blank lines. `manifest.yaml` lists each file's author,
dates, source edition, the second source it was checked against, its word count, and every textual
difference found between sources and how it was resolved.

## Public-domain rule

A text goes in this folder only if its author died before 1955, which makes it public domain in
Australia. Everything here was also published before 1929, so it is public domain in the US too. The
authors are Paterson (d. 1941), Lawson (d. 1922), Dennis (d. 1938), O'Brien/Hartigan (d. 1952) and
Steele Rudd (d. 1935).

## Copyrighted texts

Texts still in copyright in Australia, such as Dorothea Mackellar's "My Country" (author d. 1968, in
copyright until the end of 2038), are never committed. They are listed in `tests/corpus/remote.yaml`
with a pointer to a public copy. `aussiefy dev ingest tests/corpus/remote.yaml` downloads them into
`tests/corpus/local/`, which is gitignored. `manifest.yaml` lists them with `file: null`, their
`remote:` name and `status: copyright`.
