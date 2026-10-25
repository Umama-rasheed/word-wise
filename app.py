from flask import Flask, render_template, request, jsonify
from morphoneme import MP

app = Flask(__name__)

try:
    mp = MP()
except Exception:
    mp = None

# Comprehensive prefix list (ordered by length, longest first)
PREFIXES = [
    "counter", "inter", "intra", "macro", "micro", "multi", "over", "under",
    "anti", "auto", "dis", "extra", "hyper", "il", "im", "in", "ir", "mal",
    "mis", "mono", "non", "out", "post", "pre", "pro", "re", "semi", "sub",
    "super", "trans", "tri", "ultra", "un", "uni", "up", "down"
]

# Comprehensive suffix list (ordered by length, longest first)
SUFFIXES = [
    "ability", "ibility", "ation", "ition", "ment", "ness", "less", "ful", "able",
    "ible", "tion", "sion", "ance", "ence", "ant", "ent", "ary", "ery", "ory",
    "ing", "ed", "ly", "er", "est", "al", "ial", "ic", "ical", "ous", "ious",
    "ive", "ative", "itive", "ize", "ise", "ify", "en", "ward", "wise", "ship",
    "hood", "dom", "ism", "ist", "ity", "ty", "ry", "cy", "fy", "es", "s"
]

# Spelling adjustments for root recovery
SPELLING_RULES = {
    # If root ends with 'i' and suffix was '-ness' or '-ly', change to 'y'
    ("happi", "ness"): "happy",
    ("happi", "ly"): "happy",
    ("eas", "ily"): "easy",
    ("bus", "ily"): "busy",
    # Add more as needed
}

def restore_spelling(root, suffix):
    """Fix common spelling changes after stripping suffixes."""
    if (root, suffix) in SPELLING_RULES:
        return SPELLING_RULES[(root, suffix)]
    # Generic: if root ends with 'i' and suffix starts with a consonant (n, l, etc.)
    if root.endswith("i") and suffix and suffix[0] not in "aeiou":
        return root[:-1] + "y"
    return root

def rule_based_analyze(word):
    """Strip prefixes and suffixes using rules. Returns (prefix, root, suffix)."""
    original = word.lower()
    root = original
    prefix = ""
    suffix = ""

    # Strip prefix (only one, longest match first)
    for p in PREFIXES:
        if root.startswith(p) and len(root) > len(p) + 2:  # root must be at least 3 chars
            prefix = p
            root = root[len(p):]
            break

    # Strip suffix (only one, longest match first)
    for s in SUFFIXES:
        if root.endswith(s) and len(root) > len(s) + 2:  # root must be at least 3 chars
            suffix = s
            root = root[:-len(s)]
            # Fix spelling
            root = restore_spelling(root, s)
            break

    # If no prefix and no suffix found, return None (let morphoneme try)
    if not prefix and not suffix:
        return None

    return prefix, root, suffix

def morphoneme_analyze(word):
    """Use morphoneme as fallback."""
    if not mp:
        return None
    try:
        result = mp.word_morph(word)
        if isinstance(result, dict):
            p_list = result.get("prefixes", [])
            s_list = result.get("suffixes", [])
            r_list = result.get("roots", [])
            if p_list or s_list:
                prefix = p_list[0] if p_list else ""
                root = r_list[0] if r_list else word
                suffix = s_list[0] if s_list else ""
                return prefix, root, suffix
    except Exception:
        pass
    return None

def analyze_word(word):
    word = word.strip().lower()
    if not word or not word.isalpha():
        return None

    # Try rule-based first
    result = rule_based_analyze(word)
    if result:
        prefix, root, suffix = result
    else:
        # Fallback to morphoneme
        result = morphoneme_analyze(word)
        if result:
            prefix, root, suffix = result
        else:
            prefix, root, suffix = "", word, ""

    # Format for display
    prefix_disp = f"{prefix}-" if prefix else "None"
    suffix_disp = f"-{suffix}" if suffix else "None"

    # Build explanation
    if prefix and suffix:
        explanation = f"The prefix '{prefix}-' modifies the meaning, and the suffix '-{suffix}' changes the word's grammatical form. The core root is '{root}'."
    elif prefix:
        explanation = f"The prefix '{prefix}-' modifies the meaning of the word. The core root is '{root}'."
    elif suffix:
        explanation = f"The suffix '-{suffix}' changes the word's grammatical form. The core root is '{root}'."
    else:
        explanation = f"'{word}' appears to be a base root word with no easily detectable prefix or suffix."

    return {
        "word": word,
        "prefix": prefix_disp,
        "root": root,
        "suffix": suffix_disp,
        "prefix_raw": prefix,
        "suffix_raw": suffix,
        "explanation": explanation
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    word = data.get('word', '')
    result = analyze_word(word)
    if result is None:
        return jsonify({"error": "Please enter a valid English word (letters only)."})
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)