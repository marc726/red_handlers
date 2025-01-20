import re 

from Models.Request import Request
from Models.ReleaseTypes import RELEASE_TYPES

from Utilities.FixTags import manual_format_tags, format_tags
from Utilities.CleanText import clean_title, clean_artist
"""
Parse response from Redacted API. Check for links from applicable websites.
"""


def parse_response(data):
    
    results = data.get("response", {}).get("results", [])
    valid_request_list = []

    for item in results:
        url_link = extract_link_from_desc(item.get("bbDescription"))

        if url_link is not None:
            if "FLAC" in item.get("formatList") and "WEB" in item.get("mediaList"):
                
                req = Request(
                    request_id=item.get("requestId"),
                    title=clean_title(item.get("title")),
                    year=item.get("year"),
                    image_link=item.get("image"),
                    artist=clean_artist(item.get("artists")),
                    release_type=RELEASE_TYPES.get(item.get("releaseType")),
                    tags=format_tags(item.get("tags")),
                    url_link=url_link,
                    upc=item.get("catalogueNumber")
                )
                valid_request_list.append(req)
    
    return valid_request_list   


def manual_parse_response(data, music_url):
    item = data.get("response", {})

    if not item:
        print("Error: No results found in the response.")
        return None

    if ("FLAC" in item.get("formatList", []) and ("WEB" in item.get("mediaList", [])) or "Any" in item.get("mediaList", [])) or "Any" in item.get("formatList", []):
        artists = [[{"name": artist.get("name")} for artist in item.get("musicInfo", {}).get("artists", [])]]
        #print(f'Artists are: {artists}')
        #print(f'Tags are: {item.get("tags")}')
        req = Request(
            request_id=item.get("requestId"),
            title=clean_title(item.get("title")),
            year=item.get("year"),
            image_link=item.get("image"),
            artist=artists,
            release_type=item.get("releaseType"),
            tags=manual_format_tags(item.get("tags")),
            url_link=music_url,
            upc=item.get("catalogueNumber")
        )
        return req
    elif "FLAC" not in item.get("formatList", []):
        print(f"\033[91mError: Request is not a FLAC request. It's in {item.get('formatList', [])}\033[0m")
    elif "WEB" not in item.get("mediaList", []) and "Any" not in item.get("mediaList", []):
        print(f"\033[91mError: Request is not a WEB request. It's in {item.get('mediaList', [])}\033[0m")
    
    return None


def extract_link_from_desc(description):
    if not description:
        return None

    # Deezer pattern:
    # Example: https://www.deezer.com/album/12345 or /track/12345
    # optionally with a language prefix (e.g. /us, /fr)
    pattern_deezer = r"https://www\.deezer\.com(?:/[a-zA-Z]+)?/(album|track)/(\d+)"

    # Qobuz pattern (STRICT):
    # Example: https://www.qobuz.com/us-en/album/sambas-e-mais-sambas-elza-soares/gm3xnquml9pka
    # Breakdown:
    #   https://www.qobuz.com/us-en/
    #   (album|track)/
    #   [a-zA-Z0-9-]+ -> slug
    #   /[a-zA-Z0-9]+ -> ID
    pattern_qobuz = (
        r"https://www\.qobuz\.com/us-en/"
        r"(album|track)/"
        r"[a-zA-Z0-9-]+/"
        r"[a-zA-Z0-9]+"
    )


    deezer_matches = re.findall(pattern_deezer, description)
    # This returns a list of tuples [(link_type, link_id), (link_type, link_id), ...]

    qobuz_matches = re.findall(pattern_qobuz, description)
    # note: findall(pattern_qobuz, description) will only return the (album|track)
    # group, because our pattern only has one capturing group. We also need the full URL
    qobuz_full_urls = [m.group(0) for m in re.finditer(pattern_qobuz, description)]
    # Then qobuz_matches[i] corresponds to (album|track), qobuz_full_urls[i] is the full link.

    # If more than one distinct ID is found for Deezer or Qobuz, we return None.
    # Deezer
    deezer_ids = set()
    # We'll also store a single "normalized" Deezer URL we intend to return if there's exactly one.
    # Normalization: https://www.deezer.com/<type>/<id>
    deezer_normalized_link = None

    for (link_type, link_id) in deezer_matches:
        deezer_ids.add(link_id)

    if len(deezer_ids) > 1:
        # More than one distinct Deezer ID => ignore and return None
        return None
    elif len(deezer_ids) == 1:
        # Exactly 1 unique Deezer ID. Let's pick it out and build the normalized link.
        unique_id = list(deezer_ids)[0]
        link_type = deezer_matches[0][0]  # Either "album" or "track" from the first match
        deezer_normalized_link = f"https://www.deezer.com/{link_type}/{unique_id}"

    # Qobuz
    qobuz_ids = set()
    # We also need to store exactly one Qobuz link if there's a unique ID
    qobuz_single_link = None

    for i, link_type in enumerate(qobuz_matches):
        # link_type is "album" or "track"
        full_link = qobuz_full_urls[i]

        qobuz_id = full_link.rsplit("/", 1)[-1]
        qobuz_ids.add(qobuz_id)

    if len(qobuz_ids) > 1:
        return None
    elif len(qobuz_ids) == 1:
        qobuz_single_link = qobuz_full_urls[0]

    #   1) If there's exactly one unique Deezer ID, return the Deezer link (ignore Qobuz).
    #   2) Otherwise, if no Deezer link but exactly one unique Qobuz ID, return that Qobuz link.
    #   3) Else return None.

    if deezer_normalized_link is not None:
        return deezer_normalized_link

    if qobuz_single_link is not None:
        return qobuz_single_link

    return None