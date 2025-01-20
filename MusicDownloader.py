import os
import subprocess
import shutil

from Utilities.FixDescription import fix_description
from Utilities.EnsureFlac import ensure_flac_and_quantity
from Utilities.DeleteFailed import delete_failed_folder
from Utilities.TrackCountValidation import validate_track_count
from Utilities.ConfigParser import get_config
from Models.Request import Request
from Utilities.GenerateViewSpectrals import generate_view_spectrals, spectrals_ok

config = get_config()
    
def download_verify_music(request: Request, domain):
    
    print("Preparing download folder...")
    TEMP_FOLDER_PATH = config["PATHS"]["DL_TEMP_FOLDER_PATH"]
    if os.path.exists(TEMP_FOLDER_PATH):
        shutil.rmtree(TEMP_FOLDER_PATH)
    
    print(f"Starting download for {request.title}...")
    
    try:
        print(f"Downloading from {request.url_link}...")

        if domain == "deezer" or domain == "tidal":
            print("Domain Recognized: Deezer/Tidal")
            subprocess.run(["rip", "url", f"{request.url_link}"], check=True)
        elif domain == "qobuz":
            print("Domain Recognized: Qobuz")
            subprocess.run(["qobuz-dl", "dl", f"{request.url_link}"], check=True)
        else:
            raise Exception(f"Domain {domain} not recognized.")

        print("Download completed.")
        
        temp_folders = os.listdir(TEMP_FOLDER_PATH)
        if len(temp_folders) != 1:
            raise Exception(f"There should be exactly one folder in the temp directory. Found {len(temp_folders)}.")
        
        folder_name = temp_folders[0]
        temp_folder_path = os.path.join(TEMP_FOLDER_PATH, folder_name)
        real_folder_path = os.path.join(config["PATHS"]["REAL_FOLDER_PATH"], folder_name)

        #FLAC and Single Check
        bad_file, flac_and_quantity_check = ensure_flac_and_quantity(request, temp_folder_path)
        if flac_and_quantity_check is False:
            input(f"\033[91mError detected: {bad_file}. Press any key to continue...\033[0m")
            delete_failed_folder(temp_folder_path)
            return None, None
        
        #If not single, API checks for track count consistency
        if request.is_album:
            print("Album detected. Checking track count consistency...")
            if not validate_track_count(request, temp_folder_path):
                delete_failed_folder(temp_folder_path)
                print("Mismatched folder was deleted.")
                return None, None
        
        generate_view_spectrals(temp_folder_path, folder_name)
        ans = spectrals_ok()
        
        if ans is False:
            delete_failed_folder(temp_folder_path)
            delete_failed_folder(f"{config['PATHS']['SPECTRAL_FOLDER_PATH']}\\{folder_name}")
            print("Folder was deleted. Moving on...")
            return None, None
                
        # Move the folder to REAL_FOLDER_PATH, overwrite if found
        if os.path.exists(real_folder_path):
            shutil.rmtree(real_folder_path)
        os.rename(temp_folder_path, real_folder_path)
        print(f"Moved folder {folder_name} to {config["PATHS"]["REAL_FOLDER_PATH"]}.\n")

        request.desc_for_upload = fix_description(f"{config["PATHS"]["REAL_FOLDER_PATH"]}\\{folder_name}", request)

        return folder_name, f'{config["PATHS"]["REAL_FOLDER_PATH"]}\\{folder_name}'
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
    