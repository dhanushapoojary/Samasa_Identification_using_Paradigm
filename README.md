# Kannada Samasa Identification Webpage — in-memory processing

## What changed

The Flask webpage no longer writes each request's word or split components to `input.txt`, `output.txt`, `split_output.txt`, `morph_output.txt`, or `samasa_output.txt`.

For each submission:

1. Direct Dvigu rules are checked in memory.
2. The direct Karmadharaya word list is checked in memory (the word list and linguistic dictionaries remain on disk as configuration/resources).
3. `word_split.py` is imported once, which loads the forward/reverse WX dictionaries once. Its `split_word(word)` function returns split candidates as Python tuples in memory.
4. Each split component is passed directly to `morph_kan.pl` through standard input.
5. The Samasa type is returned to Flask and displayed in the webpage. No per-word split or result files are written by a web request.

The command-line `main()` path in `samasa_pipeline_updated.py` remains available for the older file-based workflow if you run that script directly. The webpage does not use that path.

## Files required in the project folder

- `app.py`
- `templates/index.html`
- `samasa_pipeline_updated.py`
- `word_split.py`
- `karmadharaya_words.txt`
- `morph_kan.pl`
- `dict_all.txt`
- `dfsa_270526.txt`
- `alloMorphMappingFile.txt`
- `wx_dictionary2.txt` or `wx_dictionary_unique.txt`
- `reverse_wx_dictionary2.txt` or `reverse_wx_dictionary_unique.txt`

The actual dictionaries and Morph Tool resources must contain real entries; do not replace them with empty files.

## Install and run

Use the Python environment where `wxconv` is installed:

```bash
python -m pip install Flask wxconv
python app.py
```


If your Morph Tool resources are in a different directory, set `MORPH_TOOL_DIR` to the directory containing `dict_all.txt`, `dfsa_270526.txt`, `alloMorphMappingFile.txt`, and `morph_kan.pl` before starting Flask.

## Notes

- The web route handles one word at a time.
- The first request imports `word_split.py` and loads the dictionaries; later requests reuse the loaded module to avoid repeating that work.
- Dictionary and FSA files remain on disk because the splitter and Morph Tool need them. Only each request's word, split candidates, analyses, and result stay in memory.
- The full linguistic accuracy depends on the entries in the WX dictionaries, the rules in `word_split.py`, and the analyses returned by `morph_kan.pl`.

index.html should be inside the Template directory.
