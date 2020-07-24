
from .peer import Peer
from .policies import Policies
from .common import Common
from .certificate import CACertificate


class Organization(Common):

    def __init__(self, name=None, type_org=None, domain=None, has_anchor=False, index=-1):
        super().__init__()
        self.name = name
        self.id = "{}MSP".format(self.name)
        self.mspdir = None
        self.has_anchor = has_anchor
        self.type_org = type_org
        self.policies = ""
        self.domain = domain
        self.list_peer = []
        self.mspdirfolder = None
        self.cacertificate = None
        self.index = index
        self.has_chain_code = False

    def getId(self):
        return "{}MSP".format(self.name)

    def isAdmin(self):
        if self.index == 0:
            return True
        return False

    def getCaCertificate(self):
        if self.cacertificate == None:
            self.create_certificate()
        return self.cacertificate

    def create_certificate(self):
        self.cacertificate = CACertificate({"org_name": self.getDomain()})

    def addAllPeers(self, number_of_peer):

        total_peer = 0

        while total_peer < number_of_peer:
            org_peer = Peer("peer{}".format(total_peer),
                            self.getDomain(), peer_id=total_peer)

            org_peer.create_couchdb()

            self.list_peer.append(org_peer)
            total_peer += 1

    def peerLen(self):
        if self.list_peer:
            return len(self.list_peer)
        return 0

    def getmspdir(self):
        if self.name.lower() not in self.domain:
            return "{}.{}".format(
                self.name.lower(), self.domain)
        return self.domain

    def getlist_policies(self):

        if self.type_org == "admin":
            list_policies = {
                "Readers": ["ADMIN", "PEER", "CLIENT"],
                "Writers": ["ADMIN", "PEER", "CLIENT"],
                "Admins": ["ADMIN"]
            }
        else:
            list_policies = {
                "Readers": ["ADMIN", "PEER", "CLIENT"],
                "Writers": ["ADMIN", "CLIENT"],
                "Admins": ["ADMIN"]
            }

        for name, role in list_policies.items():
            self.policies += Policies(name, self.id, role=role).dump()

    def getDomain(self):
        name = self.name.lower()
        if name not in self.domain:
            return "{}.{}".format(
                name, self.domain)
        return self.domain

    def getNotDomainName(self):
        name = self.name.lower()
        domain = self.domain.split(".")[0]
        if name not in domain:
            return "{}.{}".format(
                name, domain)
        return domain

    def getAdminEmail(self):
        return "Admin@{}".format(self.getDomain())

    def getAnchorPeer(self):
        if len(self.list_peer) > 0:
            return self.list_peer[0]
        return

    def getGossipPeer(self):
        if len(self.list_peer) > 1:
            return self.list_peer[1]
        return

    def getGossipPeerBootstrapByPeerId(self, id=0):
        if len(self.list_peer) > 1:
            if id == 0:
                return self.list_peer[1]
            return self.list_peer[0]
        return

    def getConfigurationPath(self):
        return self.getDomain()

    def getPeerPem(self):
        return "crypto-config/peerOrganizations/{0}/tlsca/tlsca.{0}-cert.pem".format(self.getDomain())

    def getCaPem(self):
        return "crypto-config/peerOrganizations/{0}/ca/ca.{0}-cert.pem".format(self.getDomain())

    def dump(self):

        self.id = "{}MSP".format(self.name)

        if self.mspdirfolder == None:
            self.mspdirfolder = self.domain

        self.getlist_policies()

        if self.mspdirfolder == None:
            self.mspdirfolder = "{}.{}".format(
                self.name.lower(), self.domain)

        self.mspdir = "crypto-config/peerOrganizations/{}/msp".format(
            self.mspdirfolder)

        str_org = "\n  - &{0}\n\n  \tName: {0}\n\n  \tID: {1}\n\n  \tMSPDir: {2}\n\n\n  \tPolicies:{3}".format(
            self.name, self.id, self.mspdir, self.policies)

        if self.has_anchor:
            self.peer = Peer("peer0")
            self.peer.anchor.server.host = self.domain
            self.peer.anchor.org_name = self.name
            str_org += "\n\n  \tAnchorPeers:{}".format(self.peer.anchor.dump())

        return str_org
