import re
from .anchorpeer import AnchorPeer
from .server import Server, NetworkServer


class Peer(Server):
    def __init__(self, name=None, domain=None, peer_id=0):
        self.anchor = AnchorPeer(name)
        self.name = name
        self.domain = domain
        self.peer_id = peer_id
        self.couchdb = None
        NetworkServer.PEER_SERVER_EXTERN_PORT += 10
        super().__init__(self.getHostname(),
                         NetworkServer.PEER_SERVER_EXTERN_PORT)
        self.intern_port = NetworkServer.PEER_SERVER_INTERN_PORT

    def getHostname(self):
        if self.name and self.domain:
            return "{}.{}".format(self.name.lower(), self.domain.lower())
        elif self.domain:
            return self.domain.lower()
        elif self.name:
            return self.name.lower()

    def getChainCodeInternPort(self):
        return NetworkServer.PEER_SERVER_CHAINCODE_INTERN_PORT

    def getChainCodeAddress(self):
        return "{}:{}".format(self.getHostname(), NetworkServer.PEER_SERVER_CHAINCODE_INTERN_PORT)

    def create_couchdb(self):
        self.couchdb = Server("couchdb." + self.getHostname())
        NetworkServer.COUCHDB_SERVER_EXTERN_PORT += 5
        self.couchdb.port = NetworkServer.COUCHDB_SERVER_EXTERN_PORT
        self.couchdb.intern_port = NetworkServer.COUCHDB_SERVER_INTERN_PORT

    def getCouchDbHostname(self):
        return self.couchdb.host

    def getCouchDb(self):
        return self.couchdb
