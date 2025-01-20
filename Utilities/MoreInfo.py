#!/usr/bin/env python3

import re
import requests
import os
import sys
from bs4 import BeautifulSoup
from html import unescape

# Import the config object created in your "utilities/ConfigParser.py".
# That file presumably loads and returns a configparser.ConfigParser instance.
# Add the parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from Utilities.ConfigParser import get_config

config = get_config()


#Credit to Mofo creators on Redacted forums. 

# Utility Functions

def decodeHTML(orig: str) -> str:
    """Replicates the decodeHTML in the JS code."""
    return unescape(orig)

def sanitize(text: str) -> str:
    """Lowercase, strip trailing spaces, remove certain suffixes."""
    if not text:
        return ''
    text = re.sub(r"\s+\(?EP\)?$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\(cover\)$", "", text, flags=re.IGNORECASE)
    return text.lower().strip()

def fetch_json(url: str, headers=None) -> dict:
    """Similar to fetchJSON in the JS code."""
    if headers is None:
        headers = {}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_dom(url: str, headers=None) -> BeautifulSoup:
    """Similar to fetchDOM in the JS code."""
    if headers is None:
        headers = {}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

########################################
# Search Functions
########################################

def apple_search(artist: str, album: str, upc: str) -> dict:
    """Search on Apple Music via iTunes API."""
    try:
        if upc:
            upc_url = f"https://itunes.apple.com/lookup?upc={upc}&entity=album"
            resp_upc = fetch_json(upc_url)
            if resp_upc.get("results"):
                itunes_id = resp_upc["results"][0]["collectionId"]
                return {"source": "Apple", "url": f"https://music.apple.com/album/{itunes_id}"}

        print("Apple: UPC search failed; trying direct artist - title query.")
        query_url = f"https://itunes.apple.com/search?term={artist} - {album}&entity=album"
        resp_query = fetch_json(query_url)
        for release in resp_query.get("results", []):
            if sanitize(artist) in sanitize(release["artistName"]) and \
               sanitize(album)  in sanitize(release["collectionName"]):
                return {
                    "source": "Apple",
                    "url": f"https://music.apple.com/album/{release['collectionId']}"
                }
    except Exception as e:
        print(f"Apple search failed: {e}")
    return {}

def search_discogs(artist: str, album: str) -> dict:
    """Search on Discogs using a user’s token from config."""
    token = config["MOFO"]["discogs_token"]
    if not token:
        print("Discogs token not provided in config.")
        return {}
    try:
        url = (f"https://api.discogs.com/database/search"
               f"?release_title={album}&artist={artist}&token={token}")
        resp = fetch_json(url)
        for result in resp.get("results", []):
            title = result.get("title", "")
            if sanitize(artist) in sanitize(title) and sanitize(album) in sanitize(title):
                if "master_id" in result and result["master_id"]:
                    return {
                        "source": "Discogs",
                        "url": f"https://www.discogs.com/master/{result['master_id']}"
                    }
                else:
                    return {
                        "source": "Discogs",
                        "url": f"https://www.discogs.com{result['uri']}"
                    }
    except Exception as e:
        print(f"Discogs search failed: {e}")
    return {}

def deez_search(artist: str, album: str, upc: str) -> dict:
    """Search on Deezer."""
    try:
        if upc:
            upc_url = f"https://api.deezer.com/album/upc:{upc}"
            resp_upc = fetch_json(upc_url)
            if "error" not in resp_upc and "id" in resp_upc:
                return {"source": "Deezer", "url": f"https://www.deezer.com/en/album/{resp_upc['id']}"}

        print("Deezer: UPC search failed; trying direct artist - title.")
        query = f'https://api.deezer.com/search?q=artist:"{sanitize(artist)}" album:"{sanitize(album)}"'
        resp_query = fetch_json(query)
        for release in resp_query.get("data", []):
            if sanitize(artist) in sanitize(release["artist"]["name"]) and \
               sanitize(album)  in sanitize(release["album"]["title"]):
                return {
                    "source": "Deezer",
                    "url": f"https://www.deezer.com/en/album/{release['album']['id']}"
                }
    except Exception as e:
        print(f"Deezer search failed: {e}")
    return {}

def qobuz_search(artist: str, album: str) -> dict:
    """Search on Qobuz (scraping)."""
    try:
        doc = fetch_dom(f"https://www.qobuz.com/nz-en/search?q={artist} - {album}")
        releases = doc.select(".ReleaseCard")
        for release in releases:
            subtitle = release.select_one(".ReleaseCardInfosSubtitle > a")
            title_el = release.select_one(".ReleaseCardInfosTitle")
            if not subtitle or not title_el:
                continue
            if (sanitize(artist) in sanitize(subtitle.text)) and \
               (sanitize(album) in sanitize(title_el.get("data-title", ""))):
                link = title_el.get("href", "")
                if link:
                    return {
                        "source": "Qobuz",
                        "url": f"https://www.qobuz.com{link}"
                    }
    except Exception as e:
        print(f"Qobuz search failed: {e}")
    return {}

def bleep_search(artist: str, album: str) -> dict:
    """Search on Bleep via Bing (scraping)."""
    try:
        doc = fetch_dom(f"https://bing.com/search?q={artist} {album} site:bleep.com")
        results = doc.select("li.b_algo h2 > a")
        for item in results:
            if sanitize(artist) in sanitize(item.text) and sanitize(album) in sanitize(item.text):
                # Follow the link
                r = requests.get(item["href"], timeout=20)
                match = re.search(r'bleep\.com\/release\/([^";]+)', r.text)
                if match:
                    return {
                        "source": "Bleep",
                        "url": f"https://bleep.com/release/{match.group(1)}"
                    }
    except Exception as e:
        print(f"Bleep search failed: {e}")
    return {}

def spotify_search(artist: str, album: str) -> dict:
    """Search on Spotify via Bing (scraping)."""
    try:
        doc = fetch_dom(f"https://bing.com/search?q={artist} {album} site:open.spotify.com/album")
        results = doc.select("li.b_algo h2 > a")
        for item in results:
            if sanitize(artist) in sanitize(item.text) and sanitize(album) in sanitize(item.text):
                r = requests.get(item["href"], timeout=20)
                match = re.search(r'album/([a-zA-Z0-9]+)', r.text)
                if match:
                    return {
                        "source": "Spotify",
                        "url": f"https://open.spotify.com/album/{match.group(1)}"
                    }
    except Exception as e:
        print(f"Spotify search failed: {e}")
    return {}

def band_search(artist: str, album: str) -> dict:
    """Search on Bandcamp via Bing or fallback to direct Bandcamp search."""
    try:
        # Bing approach first
        doc = fetch_dom(f"https://bing.com/search?q=site:bandcamp.com/album {artist} {album}")
        results = doc.select("li.b_algo h2 > a")
        for item in results:
            if sanitize(artist) in sanitize(item.text) and sanitize(album) in sanitize(item.text):
                r = requests.get(item["href"], timeout=20)
                match = re.search(r'"(https://.+bandcamp\.com.+?)"', r.text)
                if match:
                    return {
                        "source": "Bandcamp",
                        "url": match.group(1)
                    }

        # Fallback: Bandcamp search
        print("Bandcamp: Bing failed; attempting direct search.")
        doc = fetch_dom(f"https://bandcamp.com/search?q={artist} - {album}")
        search_results = doc.select(".searchresult.album")
        for res in search_results:
            heading_el = res.select_one(".heading")
            subhead_el = res.select_one(".subhead")
            if not heading_el:
                continue
            album_title = heading_el.text.strip()
            album_artist = subhead_el.text.strip()[3:] if subhead_el and subhead_el.text.strip().startswith("by ") else ""
            if sanitize(album_title) in sanitize(album) and sanitize(artist) in sanitize(album_artist):
                link_el = heading_el.select_one("a")
                if link_el:
                    direct_url = link_el["href"].split("?")[0]
                    return {
                        "source": "Bandcamp",
                        "url": direct_url
                    }
    except Exception as e:
        print(f"Bandcamp search failed: {e}")
    return {}

def beat_search(artist: str, album: str) -> dict:
    """Search on Beatport using the token from config.cfg."""
    token = config["MOFO"]["beatport_token"]
    if not token:
        print("Beatport token not provided in config.")
        return {}
    try:
        query = f"{artist} - {album}"
        url = f"https://api.beatport.com/v4/catalog/search/?q={query}"
        headers = {"Authorization": f"Bearer {token}"}
        resp = fetch_json(url, headers=headers)
        for release in resp.get("releases", []):
            release_artist = release["artists"][0]["name"] if release["artists"] else ""
            if sanitize(artist) in sanitize(release_artist) and sanitize(album) in sanitize(release["name"]):
                slug = release["slug"]
                release_id = release["url"].split("/", 7)[-1]
                return {
                    "source": "Beatport",
                    "url": f"https://www.beatport.com/release/{slug}/{release_id}"
                }
    except Exception as e:
        print(f"Beatport search failed: {e}")
    return {}

def juno_search(artist: str, album: str) -> dict:
    """Search on Juno Download (scraping)."""
    try:
        query = f"https://www.junodownload.com/search/?solrorder=relevancy&q[all][]={artist} - {album}&track_sale_format=flac"
        doc = fetch_dom(query)
        items = doc.select(".juno-artist")
        for it in items:
            if sanitize(artist) in sanitize(it.text):
                title_el = it.find_next("span", {"class": "juno-title"})
                if title_el and sanitize(album) == sanitize(title_el.get_text()):
                    link = title_el.get("href", "")
                    if link.startswith("/"):
                        link = "https://www.junodownload.com" + link
                    return {"source": "Juno", "url": link}
    except Exception as e:
        print(f"Juno search failed: {e}")
    return {}

def allmusic_search(artist: str, album: str) -> dict:
    """Search on AllMusic, optionally fetch review if config says so."""
    fetch_review = config["MOFO"]["allmusic_review"]
    try:
        doc = fetch_dom(f"https://www.allmusic.com/search/all/{artist} {album}")
        albums = doc.select("#resultsContainer div.album")
        found_link = None
        for a in albums:
            title_el = a.select_one(".title")
            artist_el = a.select_one(".artist")
            if not title_el or not artist_el:
                continue
            if sanitize(album) in sanitize(title_el.text) and \
               sanitize(artist) in sanitize(artist_el.text):
                link_el = title_el.select_one("a")
                if link_el:
                    found_link = link_el.get("href")
                    break
        if not found_link:
            print("AllMusic: no match.")
            return {}

        result = {"source": "AllMusic", "url": found_link}
        if fetch_review:
            review_url = found_link.rstrip("/") + "/reviewAjax"
            review_doc = fetch_dom(review_url, headers={"Referer": found_link})
            author_el  = review_doc.select_one("div#review > h3")
            review_els = review_doc.select("div#review > p")
            if author_el and review_els:
                author_name = author_el.text.replace("Review by ", "").strip()
                review_text = "\n\n".join(p.text.strip() for p in review_els)
                result["review"] = {
                    "author": author_name,
                    "text": review_text
                }
        return result
    except Exception as e:
        print(f"AllMusic search failed: {e}")
    return {}

def tidal_search(artist: str, album: str, upc: str) -> dict:
    """Search on TIDAL. This may be subject to change since TIDAL's public endpoint isn't guaranteed."""
    try:
        query = f"{artist} - {album}"
        url = (f"https://listen.tidal.com/v1/search?query={query}"
               "&limit=10&offset=0&types=ALBUMS&includeContributors=true&countryCode=US")
        headers = {"x-tidal-token": "CzET4vdadNUFQ5JU"}
        resp = fetch_json(url, headers=headers)
        albums = resp.get("albums", {}).get("items", [])
        for release in albums:
            if upc and upc in release.get("upc", ""):
                album_id = release["url"].split("/")[-1]
                return {"source": "Tidal", "url": f"https://tidal.com/browse/album/{album_id}"}
            if (sanitize(release["artists"][0]["name"]) == sanitize(artist) and
                sanitize(release["title"]) == sanitize(album)):
                album_id = release["url"].split("/")[-1]
                return {"source": "Tidal", "url": f"https://tidal.com/browse/album/{album_id}"}
    except Exception as e:
        print(f"Tidal search failed: {e}")
    return {}

def musicbrainz_search(artist: str, album: str) -> dict:
    """Search on MusicBrainz."""
    try:
        url = f'https://musicbrainz.org/ws/2/release-group?query="{album}" AND artist:{artist}&fmt=json'
        resp = fetch_json(url)
        for rg in resp.get("release-groups", []):
            if sanitize(album) not in sanitize(rg["title"]):
                continue
            for credit in rg.get("artist-credit", []):
                if sanitize(artist) in sanitize(credit["name"]):
                    return {
                        "source": "MusicBrainz",
                        "url": f"https://musicbrainz.org/release-group/{rg['id']}"
                    }
    except Exception as e:
        print(f"MusicBrainz search failed: {e}")
    return {}

########################################
# Main Logic for Gathering Links
########################################

def gather_more_info(artist: str, album: str, upc: str = None) -> tuple:
    """
    Mimics the big block from the JS code:
    - calls each search function,
    - collects results,
    - returns them along with optional AllMusic review if present.
    """
    results = []
    # Add each promise-like call
    results.append(deez_search(artist, album, upc))
    am_result = allmusic_search(artist, album)
    results.append(am_result)
    results.append(apple_search(artist, album, upc))
    results.append(band_search(artist, album))
    results.append(bleep_search(artist, album))
    results.append(juno_search(artist, album))
    results.append(beat_search(artist, album))
    results.append(qobuz_search(artist, album))
    results.append(search_discogs(artist, album))
    results.append(musicbrainz_search(artist, album))
    results.append(spotify_search(artist, album))
    results.append(tidal_search(artist, album, upc))

    # Filter out empties, sort by source
    final = [r for r in results if r and "source" in r and "url" in r]
    final.sort(key=lambda x: x["source"].lower())

    # Check for AllMusic review
    am_review = am_result.get("review") if am_result and "review" in am_result else None
    return (final, am_review)
