import subprocess
import os
import time
import sys
from qbittorrentapi import Client

# Add the parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from Utilities.ConfigParser import get_config

config = get_config()

def transcode_and_add_torrent(url):
    try:
        command = f'red_oxide transcode "{url}"'
        subprocess.run(command, check=True, shell=True)
        print("Transcoding completed successfully.")
        
        client = Client(
            host=config["TORRENTING"]["host"],
            username=config["TORRENTING"]["admin"],       
            password=config["TORRENTING"]["password"],    
        )
        client.auth_log_in()

        torrents_path = config["PATHS"]["OXIDE_TEMP_FOLDER_PATH"]
        final_torrent_directory = config["PATHS"]["ANNOUNCE_TORRENT_SAVE_PATH"]

        torrent_files = [f for f in os.listdir(torrents_path) if f.endswith('.torrent')]
        if not torrent_files:
            print("No .torrent files found in OxideTemp.")
            return

        for torrent_file_name in torrent_files:
            torrent_path = os.path.join(torrents_path, torrent_file_name)
            print(f"Processing: {torrent_path}")

            with open(torrent_path, 'rb') as tf:
                added = client.torrents_add(
                    torrent_files=tf,
                    is_paused=True, 
                    category="redacted"
                )

            new_torrent_hash = None
            time.sleep(3)  # Needed to ensure the process isn't skipped over from moving too fast

            all_torrents = client.torrents_info()
            new_torrent_hash = None

            torrent_base_name = os.path.splitext(torrent_file_name)[0].lower()

            for t in all_torrents:
                if t.name.lower() == torrent_base_name:
                    new_torrent_hash = t.hash
                    break

            if not new_torrent_hash:
                raise RuntimeError(f"Could not find newly added torrent for {torrent_file_name}")

            client.torrents_recheck(torrent_hashes=new_torrent_hash)

            print(f"Rechecking {torrent_file_name}...")
            start_time = time.time()

            while True:
                time.sleep(2)
                info = client.torrents_info(torrent_hashes=new_torrent_hash)
                if not info:
                    if time.time() - start_time > 60:
                        raise RuntimeError("Torrent info not found after 60s of polling.")
                    continue

                torrent_state = info[0].state
                progress = info[0].progress

                if torrent_state in ("checkingUP", "checkingDL", "checkingResumeData"):
                    # actively checking; wait until it leaves these states
                    continue

                if progress == 1: # 100% complete
                    client.torrents_resume(new_torrent_hash)
                    print(f"{torrent_file_name} is 100% complete. Resuming torrent.")
                else:
                    raise RuntimeError(
                        f"{torrent_file_name} is not fully completed after recheck "
                        f"({progress*100:.2f}% complete)."
                    )
                break

            # Move .torrent file after confirming success
            destination_path = os.path.join(final_torrent_directory, torrent_file_name)
            os.rename(torrent_path, destination_path)
            print(f"Moved {torrent_file_name} to {final_torrent_directory}.")

        print("All tasks completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"Transcoding failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    url = input("Enter the RED URL: ").strip()
    
    if url:
        transcode_and_add_torrent(url)
    else:
        print("No URL entered.")

if __name__ == "__main__":
    main()
