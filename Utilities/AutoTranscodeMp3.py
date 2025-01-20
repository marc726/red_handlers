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

def transcode_and_add_torrent(response, manual_url):
    """
    Transcode a torrent via red_oxide, then add it to qBittorrent,
    re-checking/resuming only the torrent(s) generated by redoxide.
    """

    if response and not manual_url:
        torrent_id = response.get("response", {}).get("torrentid")
        group_id = response.get("response", {}).get("groupid")
        url = f"https://redacted.sh/torrents.php?id={group_id}&torrentid={torrent_id}"
    elif manual_url:
        url = manual_url
    else:
        print("No URL provided.")
        return

    try:
        # 1) Transcode
        command = f'red_oxide transcode "{url}"'
        subprocess.run(command, check=True, shell=True)
        print("Transcoding completed successfully.")
        
        # 2) Connect to qBittorrent
        client = Client(
            host=config["TORRENTING"]["host"],
            username=config["TORRENTING"]["username"],       
            password=config["TORRENTING"]["password"],
        )
        client.auth_log_in()

        # 3) Paths from config
        torrents_path = config["PATHS"]["OXIDE_TEMP_FOLDER_PATH"]
        final_torrent_directory = config["PATHS"]["ANNOUNCE_TORRENT_SAVE_PATH"]

        # 4) Get all .torrent files in OxideTemp
        torrent_files = [f for f in os.listdir(torrents_path) if f.endswith('.torrent')]
        if not torrent_files:
            print("No .torrent files found in OxideTemp.")
            return

        # 5) Process each .torrent in OxideTemp
        for torrent_file_name in torrent_files:
            torrent_path = os.path.join(torrents_path, torrent_file_name)
            print(f"Processing: {torrent_path}")

            with open(torrent_path, 'rb') as tf:
                client.torrents_add(
                    torrent_files=tf,
                    is_paused=True,
                    category="redacted", 
                )

            # DO NOT SET UNDER 3 OR ELSE IT WILL SKIP. 
            time.sleep(3)

            # 6) Identify newly added torrent’s hash by matching the torrent name
            all_torrents = client.torrents_info(category="redoxide")
            torrent_base_name = os.path.splitext(torrent_file_name)[0].lower()
            new_torrent_hash = None

            for t in all_torrents:
                # Compare sanitized name
                if t.name.lower() == torrent_base_name:
                    new_torrent_hash = t.hash
                    break

            if not new_torrent_hash:
                raise RuntimeError(f"Could not find newly added torrent for {torrent_file_name}")

            # --- 7) Re-check only this newly added torrent ---
            print(f"Rechecking {torrent_file_name}...")
            client.torrents_recheck(torrent_hashes=new_torrent_hash)

            start_time = time.time()
            while True:
                time.sleep(3)
                info_list = client.torrents_info(torrent_hashes=new_torrent_hash)
                if not info_list:
                    # Retry for up to 60s
                    if time.time() - start_time > 60:
                        raise RuntimeError("Torrent info not found after 60s of polling.")
                    continue

                info = info_list[0]
                if info.state in ("checkingUP", "checkingDL", "checkingResumeData"):
                    # Still checking...
                    continue

                # If 100% complete, resume
                if info.progress == 1:
                    client.torrents_resume(new_torrent_hash)
                    print(f"{torrent_file_name} is 100% complete. Resuming torrent.")
                else:
                    raise RuntimeError(
                        f"{torrent_file_name} is not fully completed after recheck "
                        f"({info.progress*100:.2f}% complete)."
                    )
                break

            # --- 8) Move the .torrent file itself to the final folder ---
            destination_path = os.path.join(final_torrent_directory, torrent_file_name)
            os.rename(torrent_path, destination_path)
            print(f"Moved {torrent_file_name} to {final_torrent_directory}.")

        print("\033[92mTranscode task completed successfully!\033[0m")

    except subprocess.CalledProcessError as e:
        print(f"Transcoding failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    url = input("Enter the RED URL: ").strip()
    if url:
        transcode_and_add_torrent(None, url)
    else:
        print("No URL entered.")
        main()

if __name__ == "__main__":
    main()
