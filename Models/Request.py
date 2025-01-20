class Request:
    def __init__(self, request_id, title, year, image_link, artist, release_type, tags, url_link, desc_for_upload=None, release_desc_for_upload = None, is_album=None, upc=None):
        self.request_id = request_id
        self.title = title
        self.year = year
        self.image_link = image_link
        self.artist = artist
        self.release_type = release_type
        self.tags = tags
        self.url_link = url_link
        self.desc_for_upload = desc_for_upload
        self.release_desc_for_upload = release_desc_for_upload
        self.is_album = is_album
        self.upc = upc


    def __repr__(self):
        return f"<Request {self.request_id} - {self.title}>"