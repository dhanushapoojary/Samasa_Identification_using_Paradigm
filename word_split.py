# ============================================================
# KANNADA SAMASA CANDIDATE WORD SPLITTER
# ============================================================


from wxconv import WXC
import os
import sys


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Preferred filenames plus common filenames/locations used in this project.
# The dictionaries may be in SAMASA/ or SAMASA/Dictionaries/.
FORWARD_DICT_CANDIDATES = [
    os.path.join(BASE_DIR, "wx_dictionary2.txt"),
    os.path.join(BASE_DIR, "wx_dictionary_unique.txt"),
    os.path.join(BASE_DIR, "Dictionaries", "wx_dictionary2.txt"),
    os.path.join(BASE_DIR, "Dictionaries", "wx_dictionary_unique.txt"),
]
REVERSE_DICT_CANDIDATES = [
    os.path.join(BASE_DIR, "reverse_wx_dictionary2.txt"),
    os.path.join(BASE_DIR, "reverse_wx_dictionary_unique.txt"),
    os.path.join(BASE_DIR, "Dictionaries", "reverse_wx_dictionary2.txt"),
    os.path.join(BASE_DIR, "Dictionaries", "reverse_wx_dictionary_unique.txt"),
]

INPUT_FILE = os.path.join(BASE_DIR, "input.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "output.txt")


# ============================================================
# WX CONVERTERS
# ============================================================

utf_to_wx = WXC(order="utf2wx", lang="kan")
wx_to_utf = WXC(order="wx2utf", lang="kan")


# ============================================================
# LOAD DICTIONARIES
# ============================================================

def resolve_dictionary(candidates, label):
    for path in candidates:
        if os.path.isfile(path):
            return path
    searched = "\\n".join("  - " + path for path in candidates)
    print(
        f"ERROR: {label} dictionary not found. Searched:\\n{searched}",
        file=sys.stderr,
    )
    print(
        "Put the dictionary in the SAMASA directory or its Dictionaries/ subfolder.",
        file=sys.stderr,
    )
    sys.exit(2)


def load_dictionary(path):
    """
    Load WX dictionary entries. Each line may be either a bare WX word
    or a record such as mara,N,1,n,3sg,.
    """
    dictionary = set()
    with open(path, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            word = line.split(",")[0].strip()
            if word:
                dictionary.add(word)
    if not dictionary:
        print(f"ERROR: Dictionary is empty: {path}", file=sys.stderr)
        sys.exit(2)
    print(f"Loaded {len(dictionary)} {os.path.basename(path)} entries from {path}")
    return dictionary


FORWARD_DICT_PATH = resolve_dictionary(FORWARD_DICT_CANDIDATES, "Forward WX")
REVERSE_DICT_PATH = resolve_dictionary(REVERSE_DICT_CANDIDATES, "Reverse WX")

forward_dict = load_dictionary(FORWARD_DICT_PATH)
reverse_dict = load_dictionary(REVERSE_DICT_PATH)


# ============================================================
# DICTIONARY CHECK
# ============================================================

def is_in_dictionary(wx_word):

    """
    Check whether a WX word occurs in the dictionary.

    Forward dictionary:
        word

    Reverse dictionary:
        reversed(word)
    """

    if not wx_word:
        return False

    # --------------------------------------------------------
    # Forward dictionary
    # --------------------------------------------------------

    if wx_word in forward_dict:

        return True

    # --------------------------------------------------------
    # Reverse dictionary
    #
    # Reverse dictionary stores the reversed WX form.
    # --------------------------------------------------------

    reversed_word = wx_word[::-1]

    if reversed_word in reverse_dict:

        return True

    return False


# ============================================================
# DIRECT DICTIONARY SPLITTING
# ============================================================

def generate_direct_splits(wx_word):

    """
    Try every possible direct two-part split.

    Example:

        kadegolu

    Try:

        k + adegolu
        ka + degolu
        kad + egolu
        kade + golu
        ...

    A candidate is accepted when both parts occur
    in the dictionary.
    """

    candidates = []

    for i in range(1, len(wx_word)):

        first = wx_word[:i]

        second = wx_word[i:]

        if not first or not second:
            continue

        if (
            is_in_dictionary(first)
            and
            is_in_dictionary(second)
        ):

            candidates.append(
                (first, second)
            )

    return candidates


# ============================================================
# SANDHI RECONSTRUCTION RULES
# ============================================================
#
# These rules are incorporated from the logic used by the
# existing Sandhi splitter.
#
# The important principle is:
#
#   surface form
#          ↓
#   candidate boundary
#          ↓
#   reconstruct original lexical form
#          ↓
#   dictionary validation
#
# ============================================================


# ------------------------------------------------------------
# KANNADA CONSONANT SANDHI
# ------------------------------------------------------------
#
# Existing Sandhi logic contains:
#
#     g -> k
#     d -> t
#     b -> p
#
# Example:
#
#     ಕಡೆ + ಕೋಲು
#
# surface:
#
#     ಕಡೆಗೋಲು
#
# WX:
#
#     kade + golu
#
# reconstructed:
#
#     kade + kolu
#
# ------------------------------------------------------------

# CONSONANT_RECONSTRUCTION = {

#     "g": ["k"],
#     "d": ["t"],
#     "b": ["p"],

# }


# ------------------------------------------------------------
# ADDITIONAL JAŚTWA / CONSONANT RECONSTRUCTION
# ------------------------------------------------------------

SANDHI_REVERSE_RULES = {
    # Jaśtva / consonant reconstruction
    "g": ["k"],
    "x": ["w"],
    "b": ["p"],

    # ಮೈದಡವಿ → ಮೈ + ತಡವಿ
    "da": ["wa"],
}


# ============================================================
# VOWEL RECONSTRUCTION
# ============================================================
#
# Based on the vowel Sandhi cases in the original Sandhi
# implementation.
#
# The surface form can represent combinations such as:
#
#     a + a
#     a + i
#     a + u
#     a + e
#     a + o
#     etc.
#
# We generate possible lexical forms and let the dictionary
# decide which one is valid.
#
# ============================================================

VOWEL_RECONSTRUCTION = {

    # savarna deergha

    "aa": [
        "a",
        "aa"
    ],

    "ii": [
        "i",
        "ii"
    ],

    "uu": [
        "u",
        "uu"
    ],

    "RR": [
        "R"
    ],

    # guna

    "ee": [
        "a",
        "aa",
        "i",
        "ii"
    ],

    "oo": [
        "a",
        "aa",
        "u",
        "uu"
    ],

    "aR": [
        "a"
    ],

    # vriddhi

    "ai": [
        "a",
        "aa",
        "e",
        "ee"
    ],

    "au": [
        "a",
        "aa",
        "o",
        "oo"
    ],

}


# ============================================================
# YAṆ SANDHI RECONSTRUCTION
# ============================================================

YAN_RECONSTRUCTION = {

    # yaN

    "ya": [
        "i",
        "ii"
    ],

    "yu": [
        "i",
        "ii"
    ],

    "yo": [
        "i",
        "ii"
    ],

    "ye": [
        "i",
        "ii"
    ],

    "va": [
        "u",
        "uu"
    ],

    "vu": [
        "u",
        "uu"
    ],

    "vo": [
        "u",
        "uu"
    ],

    "ve": [
        "u",
        "uu"
    ],

}


# ============================================================
# VISARGA RECONSTRUCTION
# ============================================================

VISARGA_RECONSTRUCTION = {

    "ka": [
        "r"
    ],

    "ra": [
        "r"
    ],

    "pa": [
        "r",
        "s"
    ],

    "ph": [
        "s"
    ],

}


# ============================================================
# AGAMA RECONSTRUCTION
# ============================================================

AGAMA_RECONSTRUCTION = {

    "ya": [
        ""
    ],

    "va": [
        ""
    ],

    "iy": [
        "i"
    ],

}
PREFIX_LOPA_RECONSTRUCTION = {
    "kaN": ["kaNNu"],
}
# ============================================================
# GENERATE PREFIX LOPA CANDIDATES
# ============================================================

def generate_prefix_lopa_candidates(prefix, suffix):

    """
    Reconstruct the original first word when its final vowel
    is lost in the compound.

    Example:

        kaN + muccu
             ↓
        kaNNu + muccu

    The dictionary decides whether the reconstructed prefix
    is a valid lexical word.
    """

    candidates = []

    if not prefix:
        return candidates

    # --------------------------------------------------------
    # Try longest prefix patterns first
    # --------------------------------------------------------

    for surface_form in sorted(
        PREFIX_LOPA_RECONSTRUCTION.keys(),
        key=len,
        reverse=True
    ):

        if prefix.endswith(surface_form):

            stem = prefix[:-len(surface_form)]

            for original_form in PREFIX_LOPA_RECONSTRUCTION[
                surface_form
            ]:

                reconstructed_prefix = (
                    stem + original_form
                )

                candidates.append(
                    (
                        reconstructed_prefix,
                        suffix
                    )
                )

    return candidates

# ============================================================
# GENERATE SANDHI CANDIDATES
# ============================================================

def generate_sandhi_candidates(prefix, suffix):

    """
    Generate possible lexical forms from a surface prefix
    and suffix.

    IMPORTANT:

    This function does NOT decide which candidate is correct.

    It only generates candidates.

    The dictionary check later decides whether a candidate
    is valid.
    """

    candidates = []

    # ========================================================
    # 1. CONSONANT SANDHI
    # ========================================================

    if suffix:
        for surface_form in sorted(
            SANDHI_REVERSE_RULES.keys(),
            key=len,
            reverse=True
        ):

            if suffix.startswith(surface_form):

                remainder = suffix[len(surface_form):]

                for original_form in SANDHI_REVERSE_RULES[surface_form]:

                    reconstructed_suffix = (
                        original_form + remainder
                    )

                    candidates.append(
                        (
                            prefix,
                            reconstructed_suffix
                        )
                    )       

        # first_char = suffix[0]

        # if first_char in CONSONANT_RECONSTRUCTION:

        #     replacements = CONSONANT_RECONSTRUCTION[
        #         first_char
        #     ]

        #     for replacement in replacements:

        #         reconstructed_suffix = (
        #             replacement +
        #             suffix[1:]
        #         )

        #         candidates.append(
        #             (
        #                 prefix,
        #                 reconstructed_suffix
        #             )
        #         )

    # # ========================================================
    # # 2. ADDITIONAL CONSONANT RECONSTRUCTION
    # # ========================================================

    # if suffix:

    #     first_char = suffix[0]

    #     if first_char in ADDITIONAL_CONSONANT_RECONSTRUCTION:

    #         replacements = (
    #             ADDITIONAL_CONSONANT_RECONSTRUCTION[
    #                 first_char
    #             ]
    #         )

    #         for replacement in replacements:

    #             reconstructed_suffix = (
    #                 replacement +
    #                 suffix[1:]
    #             )

    #             candidates.append(
    #                 (
    #                     prefix,
    #                     reconstructed_suffix
    #                 )
    #             )

    # ========================================================
    # 3. VOWEL SANDHI
    # ========================================================

    # Try longest WX symbols first.

    vowel_keys = sorted(
        VOWEL_RECONSTRUCTION.keys(),
        key=len,
        reverse=True
    )

    for surface_vowel in vowel_keys:

        if suffix.startswith(surface_vowel):

            remainder = suffix[
                len(surface_vowel):
            ]

            for vowel in VOWEL_RECONSTRUCTION[
                surface_vowel
            ]:

                reconstructed_suffix = (
                    vowel +
                    remainder
                )

                candidates.append(
                    (
                        prefix,
                        reconstructed_suffix
                    )
                )

    # ========================================================
    # 4. YAṆ SANDHI
    # ========================================================

    yan_keys = sorted(
        YAN_RECONSTRUCTION.keys(),
        key=len,
        reverse=True
    )

    for surface_form in yan_keys:

        if suffix.startswith(surface_form):

            remainder = suffix[
                len(surface_form):
            ]

            for vowel in YAN_RECONSTRUCTION[
                surface_form
            ]:

                reconstructed_suffix = (
                    vowel +
                    remainder
                )

                candidates.append(
                    (
                        prefix,
                        reconstructed_suffix
                    )
                )

    # ========================================================
    # 5. VISARGA
    # ========================================================

    visarga_keys = sorted(
        VISARGA_RECONSTRUCTION.keys(),
        key=len,
        reverse=True
    )

    for surface_form in visarga_keys:

        if suffix.startswith(surface_form):

            remainder = suffix[
                len(surface_form):
            ]

            for replacement in VISARGA_RECONSTRUCTION[
                surface_form
            ]:

                reconstructed_suffix = (
                    replacement +
                    remainder
                )

                candidates.append(
                    (
                        prefix,
                        reconstructed_suffix
                    )
                )

    # ========================================================
    # 6. AGAMA
    # ========================================================

    agama_keys = sorted(
        AGAMA_RECONSTRUCTION.keys(),
        key=len,
        reverse=True
    )

    for surface_form in agama_keys:

        if suffix.startswith(surface_form):

            remainder = suffix[
                len(surface_form):
            ]

            for replacement in AGAMA_RECONSTRUCTION[
                surface_form
            ]:

                reconstructed_suffix = (
                    replacement +
                    remainder
                )

                candidates.append(
                    (
                        prefix,
                        reconstructed_suffix
                    )
                )

    # ========================================================
    # 7. PREFIX-SIDE CONSONANT RECONSTRUCTION
    # ========================================================
    #
    # Sometimes the Sandhi change occurs at the end of the
    # first word.
    #
    # Example:
    #
    #     g -> k
    #     d -> t
    #     b -> p
    #     j -> c
    #
    # ========================================================

    if prefix:

        last_char = prefix[-1]

        prefix_rules = {
            "g": ["k"],
            "d": ["t"],
            "b": ["p"],
            "j": ["c"],
        }

        if last_char in prefix_rules:

            for replacement in prefix_rules[last_char]:

                reconstructed_prefix = (
                    prefix[:-1] +
                    replacement
                )

                candidates.append(
                    (
                        reconstructed_prefix,
                        suffix
                    )
                )

    # ========================================================
    # 8. PREFIX-SIDE LOPA RECONSTRUCTION
    # ========================================================
    #
    # Example:
    #
    #     ಕಣ್ಮುಚ್ಚು
    #
    # Surface:
    #     ಕಣ್ + ಮುಚ್ಚು
    #
    # Lexical:
    #     ಕಣ್ಣು + ಮುಚ್ಚು
    #
    # ========================================================

    lopa_candidates = generate_prefix_lopa_candidates(
        prefix,
        suffix
    )

    for candidate in lopa_candidates:

        candidates.append(candidate)

    return candidates

# ============================================================
# VALIDATE SANDHI CANDIDATE
# ============================================================

def validate_sandhi_candidate(prefix, suffix):

    """
    Check whether both reconstructed forms are dictionary
    entries.
    """

    if not prefix or not suffix:

        return False

    if not is_in_dictionary(prefix):

        return False

    if not is_in_dictionary(suffix):

        return False

    return True


# ============================================================
# GENERATE SANDHI-AWARE SPLITS
# ============================================================

def generate_sandhi_splits(wx_word):

    """
    Try every possible boundary and apply Sandhi
    reconstruction.

    Example:

        kadegolu

    Candidate boundary:

        kade | golu

    Sandhi reconstruction:

        kade | kolu

    Dictionary:

        kade  -> VALID
        kolu  -> VALID

    Therefore:

        kade + kolu
    """

    candidates = []

    # --------------------------------------------------------
    # Try every boundary
    # --------------------------------------------------------

    for i in range(1, len(wx_word)):

        surface_prefix = wx_word[:i]

        surface_suffix = wx_word[i:]

        if not surface_prefix or not surface_suffix:

            continue

        # ----------------------------------------------------
        # Generate possible reconstructed forms
        # ----------------------------------------------------

        reconstructed_candidates = (
            generate_sandhi_candidates(
                surface_prefix,
                surface_suffix
            )
        )

        # ----------------------------------------------------
        # Validate each candidate
        # ----------------------------------------------------

        for prefix, suffix in reconstructed_candidates:

            if validate_sandhi_candidate(
                prefix,
                suffix
            ):

                candidate = (
                    prefix,
                    suffix
                )

                if candidate not in candidates:

                    candidates.append(candidate)

    return candidates


# ============================================================
# COMBINED SPLIT GENERATOR
# ============================================================

def generate_splits(wx_word):
    """
    Generate word splits.

    Priority:
    1. Sandhi-aware / reconstructed splits
    2. Direct dictionary splits only if no Sandhi split exists
    """

    # ---------------------------------------------------------
    # FIRST: Try Sandhi-aware splits
    # ---------------------------------------------------------
    sandhi_candidates = generate_sandhi_splits(wx_word)

    if sandhi_candidates:
        return sandhi_candidates

    # ---------------------------------------------------------
    # SECOND: Try direct dictionary splits
    # ---------------------------------------------------------
    return generate_direct_splits(wx_word)


# ============================================================
# PLURAL SUFFIX HANDLING
# ============================================================

def generate_splits_with_plural(wx_word):

    """
    For words ending in 'ಗಳು', remove the plural suffix
    and try splitting the remaining stem.

    Example:

        ಗಿಡಬಳ್ಳಿಗಳು

    becomes:

        ಗಿಡಬಳ್ಳಿ + ಗಳು

    and then:

        ಗಿಡ + ಬಳ್ಳಿ
    """

    candidates = []

    # --------------------------------------------------------
    # Get WX representation of ಗಳು
    # --------------------------------------------------------

    plural_wx = utf_to_wx.convert("ಗಳು")

    if not plural_wx:

        return candidates

    # --------------------------------------------------------
    # Check suffix
    # --------------------------------------------------------

    if wx_word.endswith(plural_wx):

        stem = wx_word[
            :-len(plural_wx)
        ]

        # ----------------------------------------------------
        # Direct + Sandhi splitting of stem
        # ----------------------------------------------------

        stem_candidates = generate_splits(stem)

        for first, second in stem_candidates:

            candidates.append(
                (
                    first,
                    second,
                    plural_wx
                )
            )

    return candidates


# ============================================================
# CONVERT WX CANDIDATE TO KANNADA
# ============================================================

def convert_candidate_to_kannada(candidate):

    """
    Convert:

        (WX prefix, WX suffix)

    into:

        (Kannada prefix, Kannada suffix)
    """

    first, second = candidate

    try:

        first_utf = wx_to_utf.convert(first)

        second_utf = wx_to_utf.convert(second)

        return (
            first_utf,
            second_utf
        )

    except Exception as e:

        print(
            "WX conversion error:",
            candidate,
            e
        )

        return None


# ============================================================
# MAIN WORD SPLITTER
# ============================================================

def split_word(word):

    """
    Split one Kannada word.

    Returns all valid candidates.
    """

    word = word.strip()

    if not word:

        return []

    # ========================================================
    # Kannada → WX
    # ========================================================

    try:

        wx_word = utf_to_wx.convert(word)

    except Exception as e:

        print(
            "Conversion error:",
            word,
            e
        )

        return []

    print("\n----------------------------------------")
    print("Input :", word)
    print("WX    :", wx_word)
    print("----------------------------------------")

    results = []

    # ========================================================
    # STEP 1
    # DIRECT + SANDHI-AWARE SPLITTING
    # ========================================================

    candidates = generate_splits(wx_word)

    for candidate in candidates:

        converted = (
            convert_candidate_to_kannada(
                candidate
            )
        )

        if converted is None:

            continue

        if converted not in results:

            results.append(converted)

    # ========================================================
    # STEP 2
    # PLURAL 'ಗಳು' HANDLING
    # ========================================================

    plural_candidates = (
        generate_splits_with_plural(
            wx_word
        )
    )

    for first, second, plural in plural_candidates:

        converted = (
            convert_candidate_to_kannada(
                (first, second)
            )
        )

        if converted is None:

            continue

        if converted not in results:

            results.append(converted)

    return results


# ============================================================
# PROCESS INPUT FILE
# ============================================================

def process_file():

    if not os.path.exists(INPUT_FILE):
        print(
            "ERROR: Input file not found:",
            INPUT_FILE
        )
        return

    # --------------------------------------------------------
    # Open input and output
    # --------------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as infile, open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as outfile:

        # ----------------------------------------------------
        # Process every input word
        # ----------------------------------------------------

        for line in infile:

            word = line.strip()

            if not word:
                continue

            # ------------------------------------------------
            # Split word
            # ------------------------------------------------

            candidates = split_word(word)

            # ------------------------------------------------
            # No valid split
            # ------------------------------------------------

            if not candidates:
                continue

            # ------------------------------------------------
            # Write each split word on a new line
            # ------------------------------------------------

            for first, second in candidates:

                outfile.write(
                    f"{first}\n"
                )

                outfile.write(
                    f"{second}\n"
                )

                # Blank line between sentence pairs
                outfile.write(
                    "\n"
                )

    print(
        "POS input generated:",
        OUTPUT_FILE
    )


# ============================================================
# OPTIONAL: TEST SINGLE WORD
# ============================================================

def test_word(word):

    print("\n")
    print("=" * 60)
    print("TEST WORD :", word)
    print("=" * 60)

    candidates = split_word(word)

    if not candidates:

        print(
            "NO VALID SPLIT"
        )

        return

    for first, second in candidates:

        print(
            "ಪೂರ್ವಪದ :",
            first
        )

        print(
            "ಉತ್ತರಪದ :",
            second
        )

        print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Normal input.txt processing
    # --------------------------------------------------------

    process_file()

    print("\nDone.")
    print(
        "Output written to:",
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # To test a single word directly, uncomment:
    #
    # test_word("ಕಡೆಗೋಲು")
    # --------------------------------------------------------