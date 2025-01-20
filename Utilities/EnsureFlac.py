import os
import subprocess
from Models.Request import Request

def ensure_flac_and_quantity(request: Request, full_folder_path):
    """
    Ensure that all music files in the folder are in FLAC format,
    verify their integrity, and determine if the download is a single or album.
    """
    bad_music_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.wma', '.alac', '.aiff']
    flac_count = 0

    # Check for invalid file types
    for root, dirs, files in os.walk(full_folder_path):
        for file in files:
            if any(file.endswith(ext) for ext in bad_music_extensions):
                return file, False
            if file.endswith(".flac"):
                flac_count += 1

    # `flac -t` to verify FLAC files in the folder
    # MUST USE. streamrip has corruption issues. 
    try:
        subprocess.run(
            ["flac", "-t", os.path.join(full_folder_path, "*.flac")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print(f"\033[91mError: Corrupted FLAC files detected.\033[0m")
        return "Corrupted FLAC files", False

    # Determine if single or an album
    if flac_count > 1:
        request.is_album = True
    else:
        request.is_album = False

    print("\033[92mAll FLAC files are verified and in good condition.\033[0m")
    return None, True
