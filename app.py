"""Flask Samasa webpage using in-memory word splitting and Morph Tool analysis.

Per request, this app does NOT create or write input.txt, output.txt,
 split_output.txt, morph_output.txt, or samasa_output.txt. The existing
 word_split.py split_word() function returns split candidates in memory and
 those components are passed directly to morph_kan.pl through standard input.
Dictionary and FSA resource files remain on disk as required by the tools.
"""
from __future__ import annotations

import re
from flask import Flask, render_template, request

from samasa_pipeline_updated import identify_word_in_memory

app = Flask(__name__)


def normalize_word(value: str) -> str:
    value = (value or "").replace("\ufeff", "").strip()
    return value.strip(" \t\r\n,，;；:：\"'“”‘’`")


@app.get("/")
def home():
    return render_template("index.html", word="", result=None, detail=None, error=None)


@app.post("/identify")
def identify():
    word = normalize_word(request.form.get("word", ""))

    if not word:
        return render_template(
            "index.html",
            word="",
            result=None,
            detail=None,
            error="ಕನ್ನಡ ಪದವನ್ನು ನಮೂದಿಸಿ."
        )

    # Allow exactly two words for Gamaka Samasa:
    # ಆ ಹುಡುಗ, ಈ ಹುಡುಗ, ಆ ಮನೆ, ಈ ಪುಸ್ತಕ
    words = word.split()
    is_gamaka = (
        len(words) == 2
        and words[0] in {"ಆ", "ಈ"}
    )

    # Reject commas, semicolons, and newlines.
    if re.search(r"[,，;；\n\r]", word):
        return render_template(
            "index.html",
            word=word,
            result=None,
            detail=None,
            error="ದಯವಿಟ್ಟು ಸರಿಯಾದ ಪದವನ್ನು ನಮೂದಿಸಿ."
        )

    # Reject multiple words unless they match the Gamaka rule.
    if len(words) > 1 and not is_gamaka:
        return render_template(
            "index.html",
            word=word,
            result=None,
            detail=None,
            error="ಗಮಕ ಸಮಾಸಕ್ಕೆ 'ಆ/ಈ' ನಂತರ ಒಂದೇ ಪದವನ್ನು ನಮೂದಿಸಿ."
        )

    outcome = identify_word_in_memory(word)
    if outcome.get("error"):
        return render_template(
            "index.html", word=word, result=None,
            detail=outcome.get("detail"), error=outcome["error"]
        )

    return render_template(
        "index.html", word=word, result=outcome.get("samasa"),
        detail=outcome.get("detail"), error=None
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=False)
