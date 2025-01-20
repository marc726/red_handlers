import os
import mutagen
import sys
# Add the parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from Utilities.MoreInfo import gather_more_info

def fix_description(directory, request):
    description = ["[b]Tracklist:[/b]\n"]

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".flac"):
                file_path = os.path.join(root, file)
                audio = mutagen.File(file_path)
                if audio:
                    length = audio.info.length
                    minutes, seconds = divmod(length, 60)
                    # Remove .flac extension and format track info
                    track_name = file[:-5]  # Remove .flac extension
                    description.append(f"{track_name} - ({int(minutes):02d}:{int(seconds):02d})")

    first_artist = request.artist[0][0]['name']
    links, allmusic_review = gather_more_info(first_artist, request.title, request.upc) # Credit: Mofo on redacted.

    
    # Append the links
    if links:
        more_info = " | ".join(f"[url={r['url']}]{r['source']}[/url]" for r in links)
        description.append(f"\n[b]More info:[/b] {more_info}")
    
    return "\n".join(description)