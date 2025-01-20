import time

from torf import Torrent
from qbittorrentapi import Client
from Utilities.ConfigParser import get_config

config = get_config()

def create_torrent(folder_name, full_folder_path):
    """
    Create a torrent and save it to TORRENT_SAVE_PATH.
    
    Args:
        folder_name (str): The name of the folder to create the torrent for.
        full_folder_path (str): The folder path to create the torrent for.
    
    """

    try:
        print(f"Creating torrent for {folder_name}...")
        torrent = Torrent(name=folder_name, path=full_folder_path, trackers=[config["API"]["ANNOUNCE_URL"]], private=True)

        print(f"Generating torrent for {folder_name}...")
        torrent.generate()
        save_path = f"{config["PATHS"]["ANNOUNCE_TORRENT_SAVE_PATH"]}\\{folder_name}.torrent"

        print(f"Saving torrent to {save_path}...")
        torrent.write(save_path, overwrite=True)

        print(f"Torrent successfully saved at {save_path}")

        return save_path

    except Exception as e:
        print(f"Error creating torrent for {folder_name}: {e}")


def add_torrent(torrent_path):
    """
    Add a single torrent to a qBittorrent client.
    
    Args:
        torrent_path (str): The full file path to the torrent file.
    """
    try:
        client = Client(
            host=config["TORRENTING"]["host"],
            username=config["TORRENTING"]["username"],       
            password=config["TORRENTING"]["password"],
        )

        # Verify connection
        client.auth_log_in()

        print(f"[INFO] Adding torrent: {torrent_path}")
        
        client.torrents_add(torrent_files=torrent_path, category="redacted", paused=True)

        time.sleep(5)  # Wait a bit longer to ensure torrent is recognized by qBittorrent

        # Get the torrent info to monitor its progress
        torrents = client.torrents_info()
        torrent = next((t for t in torrents if t.name in torrent_path), None)
        if torrent is None:
            print(f"\033[91m[ERROR] Torrent '{torrent_path}' not found after adding.\033[0m")
            return

        # Force recheck
        print(f"[INFO] Force rechecking torrent: {torrent.name}")
        client.torrents_recheck(hashes=torrent.hash)

        # Wait for the recheck to complete and verify 100% completion
        timeout = 300  # Timeout after 5 minutes
        start_time = time.time()
        while True:
            torrent = client.torrents_info(hashes=torrent.hash)[0]
            if torrent.state in ["checkingUP", "checkingDL", "checkingResumeData"]:
                print(f"[INFO] Rechecking torrent: {torrent.name} ({torrent.state})")
            elif torrent.progress == 1.0:
                print(f"\033[92m[INFO] Success! Recheck complete: {torrent.name}\033[0m")
                break
            else:
                print(f"[INFO] Waiting for recheck to complete for: {torrent.name}")
            if time.time() - start_time > timeout:
                print(f"\033[91m[ERROR] Recheck timeout for torrent: {torrent.name}\033[0m")
                return
            time.sleep(3)

        # Resume the torrent if recheck is 100%
        if torrent.progress == 1.0:
            client.torrents_resume(hashes=torrent.hash)
            print(f"\033[92m[INFO] Resumed torrent: {torrent.name}\033[0m\n")

    except Exception as e:
        print(f"\033[91m[ERROR] An error occurred: {e}\033[0m")