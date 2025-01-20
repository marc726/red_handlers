import requests
import os
import sys
# Add the parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)


from Utilities.ConfigParser import get_config
from Models.Request import Request

config = get_config()

HEADERS = {
    "Authorization": config['API']['RED_API_KEY']
}

def is_request_filled(request: Request):
    #example: https://redacted.sh/requests.php?action=view&id=323363 we need "323363"
    
    try:
        response = requests.get(f"https://redacted.sh/ajax.php?action=request&id={request.request_id}", headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []
    
    if response.status_code == 200:
        data = response.json()
        #print(f'Data is: {data}') #uncomment to see the data
        if data.get("status") == "success" and data.get("response").get("isFilled") == False:
            print(f"\033[92mRequest {request.title} is not filled. Continuing...\033[0m")
            return False
        else:
            return True
    else:
        print(f"Error: HTTP {response.status_code}")
        return True