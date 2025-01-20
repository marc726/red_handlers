import requests
from RedRequestHandler import fetch_manual_request
from RedLocalTorrentHandler import create_torrent, add_torrent
from RedUpDownTorrentHandler import upload_torrent_to_red, download_torrent_from_red
from ParseResponse import manual_parse_response
from MusicDownloader import download_verify_music
from Utilities.StartOptions import start_options    
from Utilities.DomainRoute import route_request_by_domain
from Utilities.AutoTranscodeMp3 import transcode_and_add_torrent
from Utilities.CheckIfFilled import is_request_filled
from Utilities.DeleteFailed import delete_failed_folder, delete_failed_torrent_file
from Utilities.UploadPTP import upload_to_ptp
from Utilities.ConfigParser import get_config
from ParseResponse import extract_link_from_desc

config = get_config()

def main():
    
    red_url = input("Please enter the RED link: ")
    raw_request = fetch_manual_request(red_url)
    music_url = extract_link_from_desc(raw_request.get("response", {}).get("bbDescription"))
    
    if not music_url or music_url == "":
        music_url = input("Link not found, please enter the Deezer/Qobuz link: ")
    else:
        use_link = input(f"\033[92mLink found: {music_url}. Use it?: \033[0m")
        
        while True:
            if use_link.lower() == "y" or use_link.lower() == "n":
                break
            use_link = input("Please enter 'y' or 'n': ")
            
        if use_link.lower() == "n": 
            music_url = input("Please enter the Deezer/Qobuz link: ")
        
    request = manual_parse_response(raw_request, music_url)
    
    will_transcode = start_options()
    
    raw_request = fetch_manual_request(red_url)
    request = manual_parse_response(raw_request, music_url)
    
    if not request:
        print("\033[91mError: Request could not be parsed. Press any key to continue...\033[0m")
        input()
        return

    domain = route_request_by_domain(request)
    folder_name, full_folder_path = download_verify_music(request, domain) #also handles fixing description here
    
    if folder_name is None or full_folder_path is None:
        print("\033[91mError: Request could not be parsed. Press any key to continue...\033[0m")
        input()
        return
    
    upload_to_ptp(request, folder_name)
    
    input("Please check the files before continuing to ensure it is correct. Press any key to continue...")
    full_announce_torrent_path = create_torrent(folder_name, full_folder_path)
    
    if is_request_filled(request):
        delete_failed_folder(full_folder_path)
        delete_failed_torrent_file(full_announce_torrent_path)
        delete_failed_folder(f"{config['PATHS']['SPECTRAL_FOLDER_PATH']}\\{folder_name}")
        print("\033[91mRequest is already filled. Folder was deleted. Press any key to exit...\033[0m")
        input()
        
    response = upload_torrent_to_red(request, full_announce_torrent_path)
    torrent_personal_file_path = download_torrent_from_red(response, folder_name)
    add_torrent(torrent_personal_file_path)

    if will_transcode:
        transcode_and_add_torrent(response)

    input("All requests have been processed. Press any key to continue...")

if __name__ == "__main__":
    main()