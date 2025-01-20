import os
import requests
from Models.Request import Request

MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/"


def validate_track_count(request: Request, full_folder_path):
    track_count = get_track_count(full_folder_path)
    
    album_is_valid = musicbrainz_api_check(request, track_count)
    if album_is_valid:
        return True
    elif album_is_valid == "MISCOUNT":
        print("\033[91mTrack count validation for MusicBrainz failed. Track count mismatch.\033[0m")
        ans = input("Continue Anyway? (Y/N): ").strip().lower()
        
        while True:
            if ans == "y" or ans == "yes":
                return True
            elif ans == "n" or ans == "no":
                return False
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
                ans = input("Continue Anyway? (Y/N): ").strip().lower()
    else:
        print("Unable to get track count from MusicBrainz. Check manually before continuing.")
        ans = input("Continue Anyway? (Y/N): ").strip().lower()
        
        while True:
            if ans == "y" or ans == "yes":
                return True
            elif ans == "n" or ans == "no":
                return False
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
                ans = input("Continue Anyway? (Y/N): ").strip().lower()

        

#=======================================================================================================================    
    
    
def get_track_count(full_folder_path):
    """Ensure that the track count of the music files in the folder is consistent with the track count of the request."""
    track_count = 0
    for root, dirs, files in os.walk(full_folder_path):
        for file in files:
            if file.endswith(".flac"):
                track_count += 1
    return track_count


def musicbrainz_api_check(request, track_count):
    # Extract plain artist name
    if isinstance(request.artist, list) and request.artist:
        first_artist_group = request.artist[0]
        if isinstance(first_artist_group, list) and first_artist_group:
            artist_name = first_artist_group[0].get('name', '')
        else:
            artist_name = request.artist[0]
    else:
        artist_name = request.artist


    print(f"GET {MUSICBRAINZ_URL}release?query=release:{request.title} AND artist:{artist_name}&fmt=json")
    try:
        response = requests.get(MUSICBRAINZ_URL + "release", params={"query": f"release:{request.title} AND artist:{artist_name}", "fmt": "json"})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

    if response.status_code == 200:
        releases = response.json().get("releases", [])
        
        #print(releases)
        
        if releases and releases[0].get("score", 0) >= 95:
            first_release = releases[0]
            if first_release.get("track-count") == track_count:
                print(f"\033[92mTrack size of {track_count}/{first_release.get("track-count")} matches with {first_release.get('score')} score.\033[0m")
                return True
            else:
                print(f"\033[91mTrack size of {track_count}/{first_release.get("track-count")} does not match with {first_release.get('score')} score.\033[0m")
                return "MISCOUNT"
        elif not releases:
            print(f"\033[91mNo releases found for {request.title} by {artist_name}. Track count validation for MusicBrainz failed.\033[0m")
            print(f"Number of tracks downloaded: {track_count}")
            return False
        elif releases[0].get("score", 0) < 95:
            print(f"\033[91mScore of {releases[0].get('score')} is below 95. Track count validation for MusicBrainz failed.\033[0m")
            return False
    else:
        print(f"Error: Received status code {response.status_code}")
        return False

    print("\033[91mTrack count validation for MusicBrainz failed for unknown reason.\033[0m")
    return False



def extract_title_from_nested_structure(title):
    """
    Extract a plain string title from a nested structure.
    """
    if isinstance(title, list) and title:
        # Assuming the first list contains a dictionary with a 'name' key
        if isinstance(title[0], list) and title[0]:
            return title[0][0].get('name', '')
        elif isinstance(title[0], dict):
            return title[0].get('name', '')
    return title  # Return as-is if no transformation needed