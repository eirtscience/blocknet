
from .server import NetworkServer


class Certificate:
    def __init__(self, org_name=None):
        self.org_name = org_name
        self.intern_port = NetworkServer.CA_SERVER_INTERN_PORT
        NetworkServer.CA_SERVER_EXTERN_PORT += 1
        self.port = NetworkServer.CA_SERVER_EXTERN_PORT

    def getCaName(self):
        return self.org_name

    def getCaExternPortNumber(self):
        return self.port

    def getCaInternPortNumber(self):
        return self.intern_port


class CACertificate(Certificate):
    def __init__(self, data):
        super().__init__(**data)
