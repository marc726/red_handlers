import requests
from Utilities.ConfigParser import get_config

config = get_config()

HEADERS = {
    "Authorization": config['API']['RED_API_KEY']
}
PARAMS = {
    "action": "requests",
    "media[]": 7,
    "formats[]": 1, 
    "bitrates[]": 8
}

def fetch_requests(page):
    #print(f"{HEADERS}") debug stuff
    
    if page:
        PARAMS["page"] = page
        
    try:
        response = requests.get("https://redacted.sh/ajax.php", params=PARAMS, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            return data 
    else:
        print(f"Error: HTTP {response.status_code}")

    return []

def fetch_manual_request(url):
    #example: https://redacted.sh/requests.php?action=view&id=323363 we need "323363"
    req_id = url.split("id=")[1]
    
    try:
        response = requests.get(f"https://redacted.sh/ajax.php?action=request&id={req_id}", headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []
    
    if response.status_code == 200:
        data = response.json()
        #print(f'Data is: {data}') #uncomment to see the data
        if data.get("status") == "success" and data.get("response").get("isFilled") == False:
            return data
    else:
        print(f"Error: HTTP {response.status_code}")