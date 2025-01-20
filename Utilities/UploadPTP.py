from Models.Request import Request
from Utilities.ConfigParser import get_config
import os
import requests
from Models.Request import Request  

config = get_config()

def upload_image_to_ptpimg(image_path: str, api_key: str) -> str:
    """
    Upload a single image to ptpimg.me and return the resulting URL.
    PTPImg docs (unofficial) require form fields:
      - 'api_key'
      - 'file-upload[]'
    """
    url = "https://ptpimg.me/upload.php"
    with open(image_path, 'rb') as f:
        files = {
            "file-upload[]": (os.path.basename(image_path), f, "image/png")
        }
        data = {
            "api_key": api_key
        }
        resp = requests.post(url, files=files, data=data)
    
    if resp.status_code != 200:
        raise Exception(f"Error {resp.status_code} uploading {image_path} to ptpimg: {resp.text}")
    
    # Expected JSON response: [{"code":"abcd1234","ext":"png"}]
    try:
        json_resp = resp.json()
        if not json_resp or not isinstance(json_resp, list) or "code" not in json_resp[0]:
            raise Exception(f"Invalid JSON response from ptpimg: {resp.text}")
        code = json_resp[0]["code"]
        ext = json_resp[0]["ext"]
        return f"https://ptpimg.me/{code}.{ext}"
    except Exception as e:
        raise Exception(f"Failed parsing ptpimg response for {image_path}:\n{e}")

def upload_spectrals_in_folder(folder_path: str, api_key: str) -> dict:
    """
    Scans the given folder for Full spec PNG files, 
    uploads them to ptpimg, and returns a mapping:
      {
         "SongName": {
            "full": "ptpimg.me/full_url.png"
         },
         ...
      }
    
    We only expect file naming like:
        SongName - (Full Spec).png
    """
    results = {}
    
    for file in os.listdir(folder_path):
        if not file.lower().endswith(".png"):
            continue
        if " - (Full Spec)" not in file:
            # We skip partial or any other spectral naming
            continue
        
        # Now upload only the Full Spec
        file_path = os.path.join(folder_path, file)
        song_name = file.split(" - (Full Spec)")[0].strip()
        full_url = upload_image_to_ptpimg(file_path, api_key)
        results[song_name] = {"full": full_url}
    
    return results

def build_bbcode_spectrals(mapping: dict) -> str:
    """
    Given a dictionary of {SongName: {'full': url}},
    return a BBCode string in the requested format:

    [center]
    [hide=Spectrals]
    {Song1 name}
    [img=full_url]
    [pad=0|0|10|0][/pad]
    [hr]
    {Song2 name}
    ...
    [/hide]
    [/align]
    """
    lines = ["[align=center]", "[hide=Spectrals]"]
    
    for song_name in sorted(mapping.keys()):
        full_url = mapping[song_name].get("full", "")
        lines.append(song_name)
        lines.append(f"[img={full_url}]")
        lines.append("[pad=0|0|10|0][/pad]")
        lines.append("[hr]")
    
    # Replace the final [hr] with [/hide], then close alignment if needed
    if lines and lines[-1] == "[hr]":
        lines[-1] = "[/hide]"
        lines.append("[/align]")
    else:
        lines.append("[/hide]")
        lines.append("[/align]")
    
    return "\n".join(lines)

def upload_to_ptp(request: Request, folder_name: str):
    """
    1. Identify the spectral folder path: SPECTRAL_FOLDER_PATH\{folder_name}
    2. Upload ONLY the full PNGs in that folder to PTPImg
    3. Construct the BBCode
    4. Store that in request.release_desc_for_upload
    """
    spectral_folder = os.path.join(config["PATHS"]["SPECTRAL_FOLDER_PATH"], folder_name)
    if not os.path.exists(spectral_folder):
        raise FileNotFoundError(f"Spectral folder does not exist: {spectral_folder}")
    
    # 1) Upload only full spectrals to ptpimg
    mapping = upload_spectrals_in_folder(spectral_folder, config["API"]["PTPIMG_API_KEY"])
    
    # 2) Build BBCode
    bbcode_desc = build_bbcode_spectrals(mapping)
    
    # 3) Store in the request object
    request.release_desc_for_upload = bbcode_desc
    print("release_desc_for_upload set. Here's the result:\n")
    print(bbcode_desc)