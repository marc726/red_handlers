import json
import html
import unicodedata
import regex  # pip install regex

def clean_title(title):
    """
    Converts HTML entities like &Oslash; to actual Unicode (Ø), 
    normalizes (NFKC so e + \u0300 becomes è), and replaces anything
    that isn't a letter, digit, whitespace, underscore, or hyphen with `_`.
    """
    # 1. Convert HTML entities
    html_decoded = html.unescape(title)

    # 2. Normalize (NFKC) => precomposed characters if possible
    normalized = unicodedata.normalize('NFKC', html_decoded)

    # 3. Replace unwanted characters:
    #    [^\p{L}\p{N}\s-_]
    #    - \p{L} = any letter, including accented or non-Latin
    #    - \p{N} = any numeric digit
    #    - \s = any whitespace
    #    - underscore, hyphen
    cleaned = regex.sub(r'[^\p{L}\p{N}\s-_]', '_', normalized)

    # 4. Replace multiple underscores with a single underscore
    cleaned = regex.sub(r'_+', '_', cleaned)

    # 5. Strip leading/trailing underscores
    cleaned = cleaned.strip('_')

    return cleaned


def clean_artist(artistdata):
    """
    Takes the nested structure from item.get("artists") and fixes special characters
    by unescaping HTML entities and normalizing Unicode.
    """
    if not artistdata:
        return artistdata 

    for sublist in artistdata:
        for artist in sublist:
            if "name" in artist:
                # 1. Unescape HTML (example: &Oslash; -> Ø)
                name = html.unescape(artist["name"])
                # 2. Normalize Unicode (example: e + \u0300 -> è)
                name = unicodedata.normalize("NFKC", name)
                artist["name"] = name

    return artistdata

