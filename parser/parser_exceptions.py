
class UnathorizedExc(Exception):
    pass

class InvalidRequestExc(Exception):
    def __init__(self, url, resp, *args):
        super().__init__(f"url: {url}", f"resp - {resp[:100]}", *args)