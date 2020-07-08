
from .server import Server
from .certificate import Certificate


class Concenter:
    def __init__(self):
        self.server = Server()
        self.certificate = Certificate()
