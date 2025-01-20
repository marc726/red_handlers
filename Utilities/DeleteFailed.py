import os
import shutil

def delete_failed_folder(full_folder_path):  
    try:
        shutil.rmtree(full_folder_path)
        print(f"\033[91mDeleted failed folder: {full_folder_path}\033[0m")
    except Exception as e:
        print(f"\033[91mError deleting folder: {e}\033[0m")


def delete_failed_torrent_file(full_folder_path):
    try:
        os.remove(full_folder_path)
        print(f"\033[91mDeleted failed torrent file: {full_folder_path}\033[0m")
    except Exception as e:
        print(f"\033[91mError deleting torrent file: {e}\033[0m")