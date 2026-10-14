# ============================================================
# KANNADA SAMASA COMPLETE PIPELINE
# ============================================================


import os
import re
import subprocess
import sys
from difflib import SequenceMatcher

from wxconv import WXC


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(BASE_DIR, "input.txt")
WORD_SPLITTER = os.path.join(BASE_DIR, "word_split.py")
SPLIT_OUTPUT = os.path.join(BASE_DIR, "split_output.txt")
SAMASA_OUTPUT = os.path.join(BASE_DIR, "samasa_output.txt")
MORPH_OUTPUT = os.path.join(BASE_DIR, "morph_output.txt")

# The analyzer and its dictionaries/FSA files must be together.
# The script checks these common locations; set MORPH_TOOL_DIR explicitly
# if your installation uses a different directory.
MORPH_TOOL_DIR = os.environ.get("MORPH_TOOL_DIR", "")


# ============================================================
# WX CONVERTER
# ============================================================

utf_to_wx = WXC(
    order="utf2wx",
    lang="kan"
)


# ============================================================
# DVIGU PREFIXES
# ============================================================
#
# Dvigu Samasa is checked BEFORE word splitting.
#
# If the WX representation of an input word starts with
# one of these prefixes:
#
#       -> directly classify as ದ್ವಿಗು ಸಮಾಸ
#       -> write directly to samasa_output.txt
#       -> skip word splitter
#       -> skip POS tagger
#
# IMPORTANT:
#
# Do NOT put "" in this list.
# "" matches every string.
#
# ============================================================

DWIGU_PREFIXES = [
    "imma",
    "mU",
    "ikkeV",
    "irwo",
    "iwwaM",
    "ikka",
    "IrE",
    "Irb",
    "ogga",
    "mumma",
    "mummA",
    "nAl",
    "okka",
    "paMca",
    "xasha",
    "wri",
    "cawur",
    "sapwa",
    "aRta",
    "nava",
    "eVN",
    "hawwu",
    "munn"
]


# Direct Anshi Samasa prefixes (Kannada script).
ANSHI_PREFIXES = ("ಮುಂ", "ಹಿಂ", "ನೆಟ್ಟ", "ನಟ್ಟಿ", "ಅಂ")

# Direct Dwandwa suffixes requested for this project.
# A word ending in any of these suffixes is classified directly as ದ್ವಂದ್ವ ಸಮಾಸ.
DWANDWA_SUFFIXES = ("ಗಳು", "ವೂ", "ಯರು", "ಗಳ್", "ಯೂ", "ನರು", "ರರು")

# Direct Gamaka rule: a demonstrative (ಆ/ಈ), followed by whitespace and a word.
GAMAKA_PREFIXES = ("ಆ", "ಈ")


# ============================================================
# DIRECT KARMADHARAYA WORD LIST FILE
# ============================================================
# Put one Kannada word per line in this text file. Add/remove words
# there without editing this Python script.
DIRECT_KARMADHARAYA_FILE = os.path.join(
    BASE_DIR,
    "karmadharaya_words.txt"
)

# Loaded from DIRECT_KARMADHARAYA_FILE after normalize_input_word()
# is defined below.
DIRECT_KARMADHARAYA_WORDS = set()


# ============================================================
# DIRECT DVIGU DETECTION
# ============================================================

def detect_dvigu_by_prefix(word):
    """
    Check whether a Kannada word belongs to Dvigu Samasa
    based ONLY on the WX prefix list.

    This function does NOT use:
        - word splitter
        - POS tagger
        - Morph Tool
    """

    word = word.strip()

    if not word:
        return None

    try:

        wx_word = utf_to_wx.convert(
            word
        ).strip()

    except Exception as e:

        print(
            f"ERROR converting {word} to WX: {e}"
        )

        return None

    # --------------------------------------------------------
    # Diagnostic output
    # --------------------------------------------------------

    print(
        f"DVIGU CHECK: {word} -> {wx_word}"
    )

    # --------------------------------------------------------
    # Check prefix
    # --------------------------------------------------------

    for prefix in DWIGU_PREFIXES:

        if not prefix:
            continue

        if wx_word.startswith(prefix):

            return {
                "word": word,
                "wx_word": wx_word,
                "matched_prefix": prefix,
                "samasa": "ದ್ವಿಗು ಸಮಾಸ"
            }

    return None


# ============================================================
# WRITE DIRECT DVIGU RESULT
# ============================================================

# ============================================================
# WRITE DIRECT DVIGU RESULT
# ============================================================

def write_direct_dvigu(
    outfile,
    result
):

    outfile.write(
        f"{result['word']} = ದ್ವಿಗು ಸಮಾಸ\n"
    )


# ============================================================
# STEP 0:
# CHECK DIRECT DVIGU WORDS
# ============================================================

def detect_direct_dvigu_words():

    print("\n" + "=" * 60)
    print("STEP 0: DIRECT DVIGU DETECTION")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):

        print(
            f"ERROR: {INPUT_FILE} not found."
        )

        sys.exit(1)

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        words = [
            line.strip()
            for line in f
            if line.strip()
        ]

    direct_dvigu = {}

    for word in words:

        result = detect_dvigu_by_prefix(
            word
        )

        if result:

            direct_dvigu[word] = result

            print(
                f"DIRECT DVIGU FOUND: "
                f"{word} "
                f"-> {result['matched_prefix']}"
            )

        else:

            print(
                f"NOT DVIGU: {word}"
            )

    print("\nDirect Dvigu words:")

    if direct_dvigu:

        for word, result in direct_dvigu.items():

            print(
                f"  {word} "
                f"-> {result['matched_prefix']}"
            )

    else:

        print(
            "  No Dvigu words found."
        )

    print(
        f"\nTotal Direct Dvigu: "
        f"{len(direct_dvigu)}"
    )

    return direct_dvigu


# ============================================================
# STEP 1:
# RUN WORD SPLITTER
# ============================================================

def normalize_input_word(value):
    """Normalize one input item so quotes/punctuation do not block direct rules."""
    value = value.replace("\ufeff", "").strip()
    # Strip common quote marks and separators that may surround a word in input.txt.
    value = value.strip(" \t\r\n,，;；:：\"'“”‘’`")
    return value.strip()


def detect_dwandwa_by_suffix(word):
    """Return a direct Dwandwa match when a word ends with a configured suffix."""
    word = normalize_input_word(str(word or ""))
    if not word:
        return None
    matched_suffix = next((suffix for suffix in DWANDWA_SUFFIXES if word.endswith(suffix)), None)
    if not matched_suffix:
        return None
    return {"word": word, "matched_suffix": matched_suffix, "samasa": "ದ್ವಂದ್ವ ಸಮಾಸ"}


def detect_anshi_by_prefix(word):
    """Directly classify a word as Anshi Samasa when it starts with a configured prefix."""
    word = normalize_input_word(str(word or ""))
    if not word:
        return None
    matched_prefix = next((prefix for prefix in ANSHI_PREFIXES if word.startswith(prefix)), None)
    if not matched_prefix:
        return None
    return {"word": word, "matched_prefix": matched_prefix, "samasa": "ಅಂಶಿ ಸಮಾಸ"}


def detect_gamaka_by_phrase(word):
    """Directly classify phrases beginning with 'ಆ ' or 'ಈ ' followed by a word."""
    word = normalize_input_word(str(word or ""))
    if not word:
        return None
    match = re.match(r"^(ಆ|ಈ)\s+([^\s]+)(?:\s+.*)?$", word)
    if not match:
        return None
    return {
        "word": word,
        "matched_prefix": match.group(1),
        "following_word": match.group(2),
        "samasa": "ಗಮಕ ಸಮಾಸ",
    }


def load_direct_karmadharaya_words():
    """Load direct Karmadharaya words from one-word-per-line text file."""
    words = set()
    if not os.path.isfile(DIRECT_KARMADHARAYA_FILE):
        raise FileNotFoundError(
            "Direct Karmadharaya word list not found: "
            f"{DIRECT_KARMADHARAYA_FILE}\n"
            "Create this file and put one Kannada word per line."
        )

    with open(DIRECT_KARMADHARAYA_FILE, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            # Allow comments and blank lines in the list file.
            item = line.split("#", 1)[0]
            word = normalize_input_word(item)
            if word:
                words.add(word)

    print(f"Loaded {len(words)} direct Karmadharaya words from:")
    print(f"  {DIRECT_KARMADHARAYA_FILE}")
    return words


# Load once at startup; this set is used by direct detection and by the
# splitter filter so listed words never reach word_split.py or Morph Tool.
DIRECT_KARMADHARAYA_WORDS = load_direct_karmadharaya_words()


def run_word_splitter(direct_dvigu_words=None, direct_karmadharaya_words=None, direct_anshi_words=None, direct_gamaka_words=None, direct_dwandwa_words=None):
    """Run the splitter only on words not already directly classified."""
    print("\n" + "=" * 60)
    print("STEP 1: WORD SPLITTING")
    print("=" * 60)

    if direct_dvigu_words is None:
        direct_dvigu_words = {}
    if direct_karmadharaya_words is None:
        direct_karmadharaya_words = {}
    if direct_anshi_words is None:
        direct_anshi_words = {}
    if direct_gamaka_words is None:
        direct_gamaka_words = {}
    if direct_dwandwa_words is None:
        direct_dwandwa_words = {}
    direct_words = (set(direct_dvigu_words) | set(direct_karmadharaya_words)
                    | set(direct_anshi_words) | set(direct_gamaka_words)
                    | set(direct_dwandwa_words))
    if not os.path.isfile(INPUT_FILE):
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    if not os.path.isfile(WORD_SPLITTER):
        raise FileNotFoundError(f"Word splitter not found: {WORD_SPLITTER}")

    with open(INPUT_FILE, "r", encoding="utf-8") as handle:
        original_lines = handle.readlines()
    # Filter by normalized word, not raw line text. This ensures entries such as
    #   ಹೆದ್ದಾರಿ
    #   "ಹೆದ್ದಾರಿ",
    # are both recognized as direct Karmadharaya words and never reach the splitter.
    normal_lines = []
    skipped_direct = []
    for line in original_lines:
        # Accept both one-word-per-line input and comma/semicolon-separated lists.
        items = re.split(r"[,，;；]+", line)
        for item in items:
            normalized = normalize_input_word(item)
            if not normalized:
                continue
            if normalized in direct_words:
                skipped_direct.append(normalized)
                continue
            # Give the splitter one clean input word per line.
            normal_lines.append(normalized + "\n")

    if skipped_direct:
        print("Skipping direct-classified words in word splitter:")
        for word in skipped_direct:
            print(f"  {word}")

    # If all words are direct Dvigu, do not call the splitter at all.
    if not any(line.strip() for line in normal_lines):
        with open(SPLIT_OUTPUT, "w", encoding="utf-8") as handle:
            handle.write("")
        print("All input words were handled directly; word splitter skipped.")
        return ""

    existing_output = os.path.join(BASE_DIR, "output.txt")
    if os.path.exists(existing_output):
        os.remove(existing_output)  # prevent accidentally reusing stale output

    # word_split.py reads input.txt itself. Temporarily provide only non-Dvigu
    # words, then restore the user's original input file even if splitting fails.
    try:
        with open(INPUT_FILE, "w", encoding="utf-8") as handle:
            handle.writelines(normal_lines)
        result = subprocess.run(
            [sys.executable, WORD_SPLITTER],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        with open(INPUT_FILE, "w", encoding="utf-8") as handle:
            handle.writelines(original_lines)

    if result.returncode != 0:
        raise RuntimeError("Word splitter failed:\n" + result.stderr)
    if not os.path.isfile(existing_output):
        raise FileNotFoundError("word_split.py completed but did not create output.txt")

    with open(existing_output, "r", encoding="utf-8") as handle:
        split_data = handle.read()
    with open(SPLIT_OUTPUT, "w", encoding="utf-8") as handle:
        handle.write(split_data)

    print("Word splitting completed. Split output:")
    print("-" * 40)
    print(split_data)
    return split_data


# ============================================================
# STEP 2: RUN MORPHOLOGICAL ANALYZER (morph_kan.pl)
# ============================================================

def find_morph_tool_paths():
    """Find the Perl script and the directory containing its FSA resources."""
    configured = os.path.abspath(MORPH_TOOL_DIR) if MORPH_TOOL_DIR else None
    resource_candidates = []
    if configured:
        resource_candidates.append(configured)
    resource_candidates.extend([
        os.path.join(BASE_DIR, "FSA"),
        os.path.join(BASE_DIR, "Morph_Tool"),
        BASE_DIR,
    ])
    resource_files = ["dict_all.txt", "dfsa_270526.txt", "alloMorphMappingFile.txt"]
    resource_dir = next(
        (directory for directory in resource_candidates
         if all(os.path.isfile(os.path.join(directory, name)) for name in resource_files)),
        None,
    )
    script_candidates = []
    if configured:
        script_candidates.append(os.path.join(configured, "morph_kan.pl"))
    if resource_dir:
        script_candidates.append(os.path.join(resource_dir, "morph_kan.pl"))
    script_candidates.extend([
        os.path.join(BASE_DIR, "Morph_Tool", "morph_kan.pl"),
        os.path.join(BASE_DIR, "morph_kan.pl"),
    ])
    morph_script = next((path for path in script_candidates if os.path.isfile(path)), None)

    if resource_dir and morph_script:
        return resource_dir, morph_script

    searched = "\n  ".join(resource_candidates)
    raise FileNotFoundError(
        "Could not locate morph_kan.pl and its FSA resources. Required resource files: "
        "dict_all.txt, dfsa_270526.txt, alloMorphMappingFile.txt.\n"
        "Resource directories searched:\n  " + searched + "\n"
        "Keep the resource files together, and ensure morph_kan.pl is present either "
        "in that directory or in Morph_Tool/. Set MORPH_TOOL_DIR to the resource directory."
    )


def run_morph_analyzer(wx_word, morph_dir, morph_script):
    """Analyze one WX token using Perl; resource paths resolve from morph_dir."""
    if not wx_word:
        return "", "Empty WX input"
    command = ["perl", morph_script]
    try:
        result = subprocess.run(
            command,
            input=wx_word.strip() + "\n",
            cwd=morph_dir,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Perl was not found. Install Perl or add it to PATH.") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"Morph Tool failed for {wx_word!r} (exit {result.returncode}).\n"
            f"STDERR:\n{result.stderr[-3000:]}"
        )
    return result.stdout, result.stderr


def extract_morph_tags(morph_output):
    """Extract every tag like N1, V24 or NST from analyzer output."""
    tags = []
    # The FSA analyzer prints analyses such as root(N1)|root(NST).
    for tag in re.findall(r"\(([^()|]+)\)", morph_output):
        tag = tag.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def basic_morph_categories(tags):
    """Map paradigm tags to coarse categories without losing NST."""
    categories = set()
    for tag in tags:
        tag = tag.strip().upper()
        if tag == "NST":
            categories.add("NST")
        elif tag.startswith("V"):
            categories.add("V")
        elif tag.startswith("N"):
            categories.add("N")
        elif tag in {"JJ", "ADJ"} or tag.startswith("JJ_"):
            categories.add("JJ")
        elif tag.startswith("PR"):
            categories.add("PR")
        elif tag.startswith("QT") or tag == "NUM":
            categories.add("NUM")
    return categories


def analyze_word(word, morph_dir, morph_script, log_lines):
    """Convert a Kannada component to WX and return all analyses/categories."""
    try:
        wx_word = utf_to_wx.convert(word.strip()).strip()
    except Exception as exc:
        log_lines.append(f"CONVERSION ERROR {word!r}: {exc}")
        return {"wx": "", "raw": "", "tags": [], "categories": set()}

    stdout, stderr = run_morph_analyzer(wx_word, morph_dir, morph_script)
    tags = extract_morph_tags(stdout)
    categories = basic_morph_categories(tags)
    log_lines.append(
        f"{word}	WX={wx_word}	TAGS={','.join(tags) if tags else 'NONE'}"
        f"	CATEGORIES={','.join(sorted(categories)) if categories else 'UNKNOWN'}"
    )
    if stderr.strip():
        # The Perl tool writes verbose diagnostics to stderr. Keep them in the
        # diagnostic file instead of mixing them with the final Samasa output.
        log_lines.append(f"MORPH STDERR [{word}]: {stderr.strip()}")
    return {"wx": wx_word, "raw": stdout, "tags": tags, "categories": categories}


# ============================================================
# SAMASA IDENTIFICATION FROM MORPH TOOL CATEGORIES
# ============================================================

def identify_samasa(purva_word, purva_categories, uttara_word, uttara_categories):
    """Apply current project rules to the Morph Tool's possible analyses."""
    # Direct Anshi prefix rule.
    if detect_anshi_by_prefix(purva_word) or detect_anshi_by_prefix(uttara_word):
        return "ಅಂಶಿ ಸಮಾಸ"

    # Direct Dwandwa suffix rule, preserving all configured suffixes.
    if any(str(uttara_word).endswith(suffix) for suffix in DWANDWA_SUFFIXES):
        return "ದ್ವಂದ್ವ ಸಮಾಸ"

    # NST is kept distinct from ordinary nouns. This mapping is a provisional
    # project rule and should be validated against annotated examples.
    if "NST" in purva_categories or "NST" in uttara_categories:
        return "ಅಂಶಿ ಸಮಾಸ"

    if "N" in purva_categories and "V" in uttara_categories:
        return "ಕ್ರಿಯಾ ಸಮಾಸ"

    if "JJ" in purva_categories and "N" in uttara_categories:
        return "ಕರ್ಮಧಾರಯ ಸಮಾಸ"

    if "N" in purva_categories and "N" in uttara_categories:
        return "ತತ್ಪುರುಷ ಸಮಾಸ"

    return "ಸಮಾಸ"


# ============================================================
# PARSE SPLITTER OUTPUT AND CLASSIFY WITH MORPH TOOL
# ============================================================

def _kannada_tokens_from_line(line):
    """Extract Kannada-script tokens from noisy plain/SSF output lines."""
    return re.findall(r"[\u0C80-\u0CFF]+", line)


def _parse_split_candidates(data, input_words):
    """Parse common word_split.py outputs without assuming one exact format.

    Supported formats:
      1) SSF blocks with rows like `1<TAB>ಗಿಡ<TAB>unk`
      2) enriched rows like `2<TAB>1<TAB>ಗಿಡ<TAB>unk<TAB>RD__RDF`
      3) plain headings followed by `ಗಿಡ + ಬಳ್ಳಿ`
      4) TSV with ID, Purvapada, Uttarapada columns
    """
    candidates = []
    seen = set()

    def add(compound, first, second):
        first, second = first.strip(), second.strip()
        if not first or not second or first == second:
            return
        if not compound or compound.startswith('<'):
            compound = next((w for w in input_words if w == first + second), first + second)
        key = (compound, first, second)
        if key not in seen:
            seen.add(key)
            candidates.append(key)

    # First parse each SSF sentence by extracting Kannada tokens from each row.
    # This handles both simple and decorated token rows.
    sentences = re.findall(r"<Sentence\b[^>]*>(.*?)</Sentence>", data, flags=re.DOTALL | re.IGNORECASE)
    for index, sentence in enumerate(sentences):
        tokens = []
        for line in sentence.splitlines():
            # Ignore XML/SSF tag names; take only Kannada-script strings.
            found = _kannada_tokens_from_line(line)
            tokens.extend(found)
        # Rows can occasionally repeat tokens because of embedded output fields.
        cleaned = []
        for token in tokens:
            if not cleaned or token != cleaned[-1]:
                cleaned.append(token)
        if len(cleaned) >= 2:
            compound = next((w for w in input_words if w == cleaned[0] + cleaned[1]), cleaned[0] + cleaned[1])
            add(compound, cleaned[0], cleaned[1])

    # Parse plain splitter output regardless of whether SSF blocks were found.
    # Typical output:
    #   ಮೈದಡವಿ
    #       ಮೈ + ತಡವಿ
    current_compound = None
    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.search(r"\bNO VALID SPLIT\b", line, flags=re.IGNORECASE):
            current_compound = line.split("->", 1)[0].strip()
            continue
        match = re.match(r"^(.+?)\s*\+\s*(.+?)$", line)
        if match:
            first, second = match.group(1).strip(), match.group(2).strip()
            if _kannada_tokens_from_line(first) and _kannada_tokens_from_line(second):
                compound = current_compound or next((w for w in input_words if w == first + second), first + second)
                add(compound, first, second)
            continue
        # Don't mistake SSF markup, IDs, or table headers for compound headings.
        if not line.startswith('<') and '->' not in line and not line.lower().startswith(('id\t', 'purvapada\t')):
            if _kannada_tokens_from_line(line):
                current_compound = _kannada_tokens_from_line(line)[0]

    # Parse simple tabular split lists, with or without a header.
    for line in data.splitlines():
        parts = [part.strip() for part in line.split('\t') if part.strip()]
        if len(parts) >= 3 and parts[0].isdigit():
            # Usually ID, Purvapada, Uttarapada. In noisy rows, use the last
            # two Kannada-script fields (word tokens) rather than POS labels.
            word_fields = [part for part in parts[1:] if re.fullmatch(r'[\u0C80-\u0CFF]+', part)]
            if len(word_fields) >= 2:
                first, second = word_fields[-2], word_fields[-1]
                compound = next((w for w in input_words if w == first + second), first + second)
                add(compound, first, second)

    # LAST-RESORT FORMAT: the user's splitter emits only component lines,
    # e.g. `ಮೈ\nತಡವಿ\n\nಕಣ್ಣು\nಮುಚ್ಚು`. There are no headings and no '+'
    # signs. Read Kannada-only non-empty lines in consecutive pairs.
    if not candidates:
        component_lines = []
        for raw_line in data.splitlines():
            line = raw_line.strip()
            if re.fullmatch(r'[\u0C80-\u0CFF]+', line):
                component_lines.append(line)

        # Map each pair back to the closest remaining original input word.
        # This accommodates sandhi changes such as ಕಣ್ಮುಚ್ಚು -> ಕಣ್ಣು + ಮುಚ್ಚು.
        available = list(input_words)
        search_from = 0
        for index in range(0, len(component_lines) - 1, 2):
            first, second = component_lines[index], component_lines[index + 1]
            joined = first + second
            best_word = joined
            best_index = None
            best_score = 0.0
            for word_index in range(search_from, len(available)):
                word = available[word_index]
                score = SequenceMatcher(None, joined, word).ratio()
                if word == joined:
                    score = 1.0
                if score > best_score:
                    best_score = score
                    best_word = word
                    best_index = word_index
            if best_index is not None and best_score >= 0.40:
                search_from = best_index + 1
            else:
                best_word = joined
            add(best_word, first, second)

    return candidates


def parse_split_output(direct_dvigu_words, direct_karmadharaya_words, direct_anshi_words, direct_gamaka_words, morph_dir, morph_script, direct_dwandwa_words=None):
    """Read splitter output robustly, then analyze each split with morph_kan.pl."""
    print("\n" + "=" * 60)
    print("STEP 3: MORPHOLOGY-BASED SAMASA IDENTIFICATION")
    print("=" * 60)

    input_words = read_input_words()
    if direct_dwandwa_words is None:
        direct_dwandwa_words = {}
    direct_words = (set(direct_dvigu_words) | set(direct_karmadharaya_words)
                    | set(direct_anshi_words) | set(direct_gamaka_words)
                    | set(direct_dwandwa_words))
    split_eligible_words = [word for word in input_words if word not in direct_words]
    data_sources = []
    for path in (SPLIT_OUTPUT, os.path.join(BASE_DIR, "output.txt")):
        if os.path.isfile(path):
            try:
                content = open(path, "r", encoding="utf-8").read()
            except OSError:
                continue
            if content.strip():
                data_sources.append((path, content))

    candidates = []
    used_source = None
    for path, data in data_sources:
        parsed = _parse_split_candidates(data, split_eligible_words)
        if parsed:
            candidates = parsed
            used_source = path
            break

    results = []
    morph_log = [f"Split-output source parsed: {used_source or 'NONE'}"]
    seen_pairs = set()
    processed_compounds = set(direct_words)

    if not candidates:
        morph_log.append("ERROR: No split candidates could be parsed.")
        morph_log.append("Check split_output.txt and output.txt; the parser tried SSF, plus-separated, and TSV formats.")
        if data_sources:
            morph_log.append("First non-empty source preview:")
            morph_log.extend(data_sources[0][1].splitlines()[:30])

    for compound, purva_word, uttara_word in candidates:
        pair_key = (compound, purva_word, uttara_word)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        if compound in processed_compounds or (purva_word + uttara_word) in processed_compounds:
            continue

        purva_analysis = analyze_word(purva_word, morph_dir, morph_script, morph_log)
        uttara_analysis = analyze_word(uttara_word, morph_dir, morph_script, morph_log)

        samasa_type = identify_samasa(
            purva_word, purva_analysis["categories"],
            uttara_word, uttara_analysis["categories"],
        )
        result = f"{compound} ({purva_word} + {uttara_word}) = {samasa_type}"
        results.append(result)
        print(result)

    with open(MORPH_OUTPUT, "w", encoding="utf-8") as handle:
        handle.write("WORD\tWX\tTAGS\tCATEGORIES / DIAGNOSTICS\n")
        handle.write("\n".join(morph_log))
        if morph_log:
            handle.write("\n")

    with open(SAMASA_OUTPUT, "w", encoding="utf-8") as handle:
        # Preserve direct Dvigu classifications first.
        for word in direct_dvigu_words:
            handle.write(f"{word} = ದ್ವಿಗು ಸಮಾಸ\n")
        # These listed words bypass both the splitter and Morph Tool.
        for word in direct_karmadharaya_words:
            handle.write(f"{word} = ಕರ್ಮಧಾರಯ ಸಮಾಸ\n")
        # Prefix-matched Anshi words bypass the splitter and Morph Tool.
        for word in direct_anshi_words:
            handle.write(f"{word} = ಅಂಶಿ ಸಮಾಸ\n")
        # Phrases matching the direct demonstrative rule bypass splitter/Morph Tool.
        for word in direct_gamaka_words:
            handle.write(f"{word} = ಗಮಕ ಸಮಾಸ\n")
        # Direct Dwandwa suffix matches bypass the splitter and Morph Tool.
        for word in direct_dwandwa_words:
            handle.write(f"{word} = ದ್ವಂದ್ವ ಸಮಾಸ\n")
        for result in results:
            handle.write(result + "\n")

    print(f"\nParsed split candidates: {len(candidates)}")
    print(f"Morphological analyses logged: {len(morph_log)} lines")
    print(f"Morphology diagnostics saved to: {MORPH_OUTPUT}")
    print(f"Final Samasa output saved to: {SAMASA_OUTPUT}")
    if not candidates:
        print("WARNING: No split candidates were parsed. See morph_output.txt for the source preview.")


def read_input_words():
    """Return non-empty input lines in their original order."""
    if not os.path.isfile(INPUT_FILE):
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as handle:
        words = []
        for line in handle:
            # Input may contain a word per line or several quoted words separated by commas.
            for item in re.split(r"[,，;；]+", line):
                cleaned = normalize_input_word(item)
                if cleaned:
                    words.append(cleaned)
        return words


# ============================================================
# DIRECT KARMADHARAYA DETECTION
# ============================================================

def detect_direct_karmadharaya_words():
    """Find listed direct Karmadharaya words in input.txt."""
    found = {}
    for raw_word in read_input_words():
        word = normalize_input_word(raw_word)
        if word in DIRECT_KARMADHARAYA_WORDS:
            found[word] = {"word": word, "samasa": "ಕರ್ಮಧಾರಯ ಸಮಾಸ"}
            print(f"DIRECT KARMADHARAYA FOUND: {word}")
    print(f"Total Direct Karmadharaya: {len(found)}")
    return found



# ============================================================
# WEB/API ENTRY POINT: IDENTIFY ONE WORD ENTIRELY IN MEMORY
# ============================================================

def identify_word_in_memory(word):
    """Identify one word without writing input/split/morph/result files.

    The splitter's split_word() returns (purvapada, uttarapada) tuples in
    memory. Those components are immediately sent to morph_kan.pl through
    stdin, and the Samasa type is returned directly to the Flask webpage.
    Required dictionaries and Morph Tool resource files remain on disk; only
    per-request words, splits, analyses, and results stay in memory.

    Returns a dictionary with keys: samasa, detail, error.
    """
    word = normalize_input_word(str(word or ""))
    if not word:
        return {"samasa": None, "detail": None, "error": "ಕನ್ನಡ ಪದವನ್ನು ನಮೂದಿಸಿ."}

    # 1. Direct Gamaka phrase rule: do not call the splitter or Morph Tool.
    gamaka = detect_gamaka_by_phrase(word)
    if gamaka:
        return {
            "samasa": "ಗಮಕ ಸಮಾಸ",
            "detail": f"{word} — direct Gamaka phrase rule ({gamaka['matched_prefix']} + {gamaka['following_word']})",
            "error": None,
        }

    # Direct Dwandwa suffix rule: do not call the splitter or Morph Tool.
    dwandwa = detect_dwandwa_by_suffix(word)
    if dwandwa:
        return {
            "samasa": "ದ್ವಂದ್ವ ಸಮಾಸ",
            "detail": f"{word} — direct Dwandwa suffix: {dwandwa['matched_suffix']}",
            "error": None,
        }

    # Direct Anshi rule: do not call the splitter or Morph Tool.
    anshi = detect_anshi_by_prefix(word)
    if anshi:
        return {
            "samasa": "ಅಂಶಿ ಸಮಾಸ",
            "detail": f"{word} — direct Anshi prefix: {anshi['matched_prefix']}",
            "error": None,
        }

    # 2. Direct Dvigu rule: do not call the splitter or Morph Tool.
    dvigu = detect_dvigu_by_prefix(word)
    if dvigu:
        return {
            "samasa": "ದ್ವಿಗು ಸಮಾಸ",
            "detail": f"{word} — direct Dvigu prefix: {dvigu['matched_prefix']}",
            "error": None,
        }

    # 2. Direct Karmadharaya list: do not call the splitter or Morph Tool.
    if word in DIRECT_KARMADHARAYA_WORDS:
        return {
            "samasa": "ಕರ್ಮಧಾರಯ ಸಮಾಸ",
            "detail": f"{word} — direct Karmadharaya word-list match",
            "error": None,
        }

    # 3. Load the splitter module once. Importing it loads dictionaries once;
    # each word thereafter is split directly in memory by split_word(word).
    global _IN_MEMORY_SPLITTER
    try:
        if "_IN_MEMORY_SPLITTER" not in globals() or _IN_MEMORY_SPLITTER is None:
            import importlib
            import contextlib
            import io
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            # word_split.py prints dictionary and per-word diagnostics; silence
            # those for web requests without changing its splitting behavior.
            with contextlib.redirect_stdout(io.StringIO()):
                _IN_MEMORY_SPLITTER = importlib.import_module("word_split")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            split_candidates = _IN_MEMORY_SPLITTER.split_word(word)
    except SystemExit as exc:
        return {
            "samasa": None,
            "detail": None,
            "error": (
                "Word splitter could not load its WX dictionaries. "
                "Check wx_dictionary2.txt / wx_dictionary_unique.txt and "
                "reverse_wx_dictionary2.txt in the project directory. "
                f"(exit code: {exc.code})"
            ),
        }
    except Exception as exc:
        return {"samasa": None, "detail": None, "error": f"Word splitting failed: {exc}"}

    if not split_candidates:
        return {
            "samasa": None,
            "detail": None,
            "error": (
                "No samasa Found. "
                
            ),
        }

    # 4. Analyze the split components immediately; no split output file is made.
    try:
        morph_dir, morph_script = find_morph_tool_paths()
    except Exception as exc:
        return {"samasa": None, "detail": None, "error": f"Morph Tool resources not found: {exc}"}

    diagnostics = []
    evaluated = []
    seen = set()
    for first, second in split_candidates:
        first = str(first).strip()
        second = str(second).strip()
        if not first or not second or (first, second) in seen:
            continue
        seen.add((first, second))

        try:
            first_analysis = analyze_word(first, morph_dir, morph_script, diagnostics)
            second_analysis = analyze_word(second, morph_dir, morph_script, diagnostics)
            samasa_type = identify_samasa(
                first, first_analysis["categories"],
                second, second_analysis["categories"],
            )
        except Exception as exc:
            diagnostics.append(f"ANALYSIS ERROR [{first} + {second}]: {exc}")
            continue

        evaluated.append((samasa_type, first, second, first_analysis, second_analysis))

    if not evaluated:
        return {
            "samasa": None,
            "detail": None,
            "error": "ಪದ ವಿಭಜನೆಯಾಗಿದೆ, ಆದರೆ Morph Tool ವಿಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ. Perl ಮತ್ತು Morph Tool resources ಪರಿಶೀಲಿಸಿ.",
        }

    # Prefer a specific classification over the generic fallback when multiple
    # split candidates are produced. Keep the splitter's order for ties.
    chosen = next((item for item in evaluated if item[0] != "ಸಮಾಸ"), evaluated[0])
    samasa_type, first, second, first_analysis, second_analysis = chosen
    detail = (
        f"{word} = {first} + {second}; "
        f"{first}: {','.join(first_analysis['tags']) or 'tag ಇಲ್ಲ'}; "
        f"{second}: {','.join(second_analysis['tags']) or 'tag ಇಲ್ಲ'}"
    )
    if samasa_type == "ಸಮಾಸ":
        return {
            "samasa": None,
            "detail": detail,
            "error": (
                "ಪದ ವಿಭಜನೆಯಾಗಿದೆ, ಆದರೆ ಪ್ರಸ್ತುತ Morph Tool tags ಆಧರಿಸಿ "
                "ಸಮಾಸದ ನಿರ್ದಿಷ್ಟ ವಿಧವನ್ನು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. " + detail
            ),
        }
    return {"samasa": samasa_type, "detail": detail, "error": None}


_IN_MEMORY_SPLITTER = None

# ============================================================
# DIRECT ANSHI DETECTION
# ============================================================

def detect_direct_anshi_words():
    """Find input words that start with a configured Anshi prefix."""
    found = {}
    for raw_word in read_input_words():
        word = normalize_input_word(raw_word)
        result = detect_anshi_by_prefix(word)
        if result:
            found[word] = result
            print(f"DIRECT ANSHI FOUND: {word} -> {result['matched_prefix']}")
    print(f"Total Direct Anshi: {len(found)}")
    return found


# ============================================================
# DIRECT GAMAKA DETECTION
# ============================================================

def detect_direct_gamaka_words():
    """Find input phrases matching 'ಆ <word>' or 'ಈ <word>'."""
    found = {}
    for raw_word in read_input_words():
        word = normalize_input_word(raw_word)
        result = detect_gamaka_by_phrase(word)
        if result:
            found[word] = result
            print(f"DIRECT GAMAKA FOUND: {word} -> {result['matched_prefix']} + {result['following_word']}")
    print(f"Total Direct Gamaka: {len(found)}")
    return found


def detect_direct_dwandwa_words():
    """Find input words ending in one of the configured Dwandwa suffixes."""
    found = {}
    for raw_word in read_input_words():
        word = normalize_input_word(raw_word)
        result = detect_dwandwa_by_suffix(word)
        if result:
            found[word] = result
            print(f"DIRECT DWANDWA FOUND: {word} -> suffix {result['matched_suffix']}")
    print(f"Total Direct Dwandwa: {len(found)}")
    return found


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("KANNADA SAMASA PIPELINE — MORPH TOOL")
    print("=" * 60)

    direct_dvigu_words = detect_direct_dvigu_words()
    direct_karmadharaya_words = detect_direct_karmadharaya_words()
    direct_anshi_words = detect_direct_anshi_words()
    direct_gamaka_words = detect_direct_gamaka_words()
    direct_dwandwa_words = detect_direct_dwandwa_words()

    try:
        run_word_splitter(
            direct_dvigu_words, direct_karmadharaya_words, direct_anshi_words,
            direct_gamaka_words, direct_dwandwa_words
        )
    except Exception as exc:
        print(f"ERROR during word splitting: {exc}", file=sys.stderr)
        print(
            "\\nCheck that the forward and reverse WX dictionaries are available. "
            "The splitter searches the SAMASA folder and SAMASA/Dictionaries/.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        morph_dir, morph_script = find_morph_tool_paths()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Using Morph Tool script: {morph_script}")
    print(f"Using Morph Tool resources: {morph_dir}")
    parse_split_output(
        direct_dvigu_words, direct_karmadharaya_words, direct_anshi_words,
        direct_gamaka_words, morph_dir, morph_script, direct_dwandwa_words
    )
    print("\nPIPELINE COMPLETED")


if __name__ == "__main__":
    main()
