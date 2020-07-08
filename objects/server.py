

class Server:
    def __init__(self, host=None, port=7051):
        self.host = host
        self.port = port
        self.intern_port = port

    def getaddress(self):
        return "{}:{}".format(self.host, self.port)

    def getinternal_address(self):
        return "{}:{}".format(self.host, self.intern_port)


class NetworkServer:

    CA_SERVER_EXTERN_PORT = 6053
    CA_SERVER_INTERN_PORT = 7054
    COUCHDB_SERVER_EXTERN_PORT = 5053
    COUCHDB_SERVER_INTERN_PORT = 7054
    ORDERER_SERVER_EXTERN_PORT = 7053
    ORDERER_SERVER_INTERN_PORT = 7054
    PEER_SERVER_EXTERN_PORT = 7053
    PEER_SERVER_INTERN_PORT = 7054
