from RedRequestHandler import fetch_requests
from RedLocalTorrentHandler import create_torrent, add_torrent
from RedUpDownTorrentHandler import upload_torrent_to_red, download_torrent_from_red
from ParseResponse import parse_response
from MusicDownloader import download_verify_music
from Utilities.StartOptions import start_options    
from Utilities.DomainRoute import route_request_by_domain
from Utilities.AutoTranscodeMp3 import transcode_and_add_torrent
from Utilities.CheckIfFilled import is_request_filled
from Utilities.DeleteFailed import delete_failed_folder, delete_failed_torrent_file
from Utilities.ViewPage import view_page
from Utilities.UploadPTP import upload_to_ptp
from Utilities.ConfigParser import get_config
import time



config = get_config()

def main():

    will_transcode = start_options()
    raw_request = fetch_requests(view_page())
    requests_to_upload = parse_response(raw_request)
    titles = "\n".join([request.title for request in requests_to_upload])
    print(f"\n\033[1mRequests to process ({len(requests_to_upload)}):\033[0m\n{titles}")
    print("__________________________________________________________\n")
    for request in requests_to_upload:

        domain = route_request_by_domain(request)
        folder_name, full_folder_path = download_verify_music(request, domain) #also handles fixing description here
        if folder_name is None or full_folder_path is None:
            print("\033[91mError: Request could not be parsed. Moving to next request...\033[0m")
            continue
        
        upload_to_ptp(request, folder_name)
        
        if not request.is_album:
            input("\nPlease check the single before continuing to ensure it is correct. Press any key to continue...")
        print("Checking if request was filled...")
        
        full_announce_torrent_path = create_torrent(folder_name, full_folder_path)
        
        if is_request_filled(request):
            delete_failed_folder(full_folder_path)
            delete_failed_folder(f"{config['PATHS']['SPECTRAL_FOLDER_PATH']}\\{folder_name}")
            delete_failed_torrent_file(full_announce_torrent_path)
            print("\033[91mRequest is already filled. Folder & torrent were deleted. Moving to next request...\033[0m")
            continue
        
        response = upload_torrent_to_red(request, full_announce_torrent_path)
        torrent_personal_file_path = download_torrent_from_red(response, folder_name)
        add_torrent(torrent_personal_file_path)
        
        if will_transcode:
            transcode_and_add_torrent(response)
            
        for i in range(5, 0, -1):
            print(f"\rCooling off.. Continuing in {i} seconds...", end="", flush=True)
            time.sleep(1)
    
    if len(requests_to_upload) == 0:
        input("No requests to process. Press any key to continue...")
    else:
        input("All requests have been processed. Press any key to continue...")

if __name__ == "__main__":
    main()