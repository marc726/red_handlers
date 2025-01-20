import requests
from Models.Request import Request
from Utilities.ConfigParser import get_config

# Constants
config = get_config()

UPLOAD_URL = "https://redacted.sh/ajax.php?action=upload"
DOWNLOAD_URL = "https://redacted.sh/ajax.php?action=download"

HEADERS = {
    "Authorization": config['API']['RED_API_KEY']
}

def upload_torrent_to_red(request: Request, torrent_path):
    ArgumentList = {
        #"dryrun": True,
        "type": 0,
        "artists[]": [artist["name"] for artist_list in request.artist for artist in artist_list],
        "importance[]": [1 for artist_list in request.artist for _ in artist_list],  # Assuming all artists are main artists
        "title": request.title,
        "year": request.year,
        "remaster_year": request.year,
        "releasetype": request.release_type,
        "format": "FLAC",
        "bitrate": "Lossless",
        "media": "WEB",
        "tags": request.tags,
        "image": request.image_link,
        "requestid": request.request_id,
        "release_desc": request.release_desc_for_upload,
        "album_desc": request.desc_for_upload,
    }
    
    if request.upc and request.upc != "":
        ArgumentList["remaster_catalogue_number"] = request.upc

    try:
        with open(torrent_path, 'rb') as file:
            files = {'file_input': file}
            response = requests.post(UPLOAD_URL, headers=HEADERS, data=ArgumentList, files=files)
            response.raise_for_status()
            #print(response.json()) #uncomment to see the response
            
            response_data = response.json()
            if response_data.get("status") == "success":
                print("\033[92mTorrent successfully uploaded to RED.\033[0m")
                print(f"Source: {response_data.get('response', {}).get('source')}, "
                      f"Request ID: {response_data.get('response', {}).get('requestid')}, "
                      f"Torrent ID: {response_data.get('response', {}).get('torrentid')}, "
                      f"Group ID: {response_data.get('response', {}).get('groupid')}, "
                      f"New Group: {response_data.get('response', {}).get('newgroup')}\n")
                
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print(f"Response content: {e.response.content}")
        return False


def download_torrent_from_red(response, folder_name):

    torrent_id = response.get("response", {}).get("torrentid")
    print("Downloading torrent from RED...")

    params = {
        "id": torrent_id,
        "usetoken": 0
    }
    
    try:
        response = requests.get(DOWNLOAD_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        torrent_file_path = f"{config["PATHS"]["PERSONAL_TORRENT_SAVE_PATH"]}\\{folder_name}.torrent"
        with open(torrent_file_path, 'wb') as file:
            file.write(response.content)
        print(f"Torrent successfully downloaded and saved at {torrent_file_path}")
        return torrent_file_path
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print(f"Response content: {e.response.content}")
        return False