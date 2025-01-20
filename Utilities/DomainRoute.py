import re
from Models.Request import Request

def route_request_by_domain(request: Request) -> str:
    # This regex looks for `http://` or `https://`, 
    # optionally `www.`, then captures everything until a '.' or '/'
    domain_pattern = re.compile(r'https?://(?:www\.)?([^/.]+)')
    
    match_obj = domain_pattern.search(request.url_link)
    if match_obj:
        return match_obj.group(1)  # For ex. this should be "deezer" for the given URL
    
    return None 