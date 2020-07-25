

from .kafka import Kafka
from .raft import Raft
from .capabilities_handler import CapabilitiesHandler
from .organization import Organization
from .peer import Peer
from .policies import Policies
from .server import Server, NetworkServer
from .chaincode import ChainCode


class BatchSize:
    def __init__(self, maxmessagecount=None, absolutemaxbytes=None, preferredmaxbytes=None):
        self.max_message_count = maxmessagecount
        self.absolute_max_bytes = absolutemaxbytes
        self.preferred_max_bytes = preferredmaxbytes

    def dump(self):
        return '''
        # Max Message Count: The maximum number of messages to permit in a batch
        MaxMessageCount: {}

        # Absolute Max Bytes: The absolute maximum number of bytes allowed for
        # the serialized messages in a batch.
        AbsoluteMaxBytes: {}

        # Preferred Max Bytes: The preferred maximum number of bytes allowed for
        # the serialized messages in a batch. A message larger than the preferred
        # max bytes will result in a batch larger than preferred max bytes.
        PreferredMaxBytes: {}
        '''.format(self.max_message_count, self.absolute_max_bytes, self.preferred_max_bytes)


class OrdererServer(Server):

    def __init__(self, host=None, port=None):
        super().__init__(host, port)


class Orderer(CapabilitiesHandler):
    def __init__(self, list_version=None, data=None):
        super().__init__()
        self.organization = Organization(**(data.get("org")))
        self.server = Server(
            **{"host": "orderer.{}".format(self.organization.domain), "port": 7050})
        self.version = list_version
        self.capability_name = "OrdererCapabilities"
        self.type = data.get("orderer_type")
        self.address = self.server.getaddress()
        self.batch_timeout = data.get("batchtimeout")
        self.batch_size = BatchSize(**(data.get("batchsize")))
        self.kafka = Kafka()
        self.etcdraft = Raft()
        self.number_of_orderer = data.get("number_of_orderer")
        self.name = "OrdererDefaults"
        self.generate_chainecode = False
        self.list_orderer = []
        self.list_chaincode = {}

    def getDomain(self):
        return self.organization.domain

    def add_chaincode(self, name, data):
        if name:
            chain_code = ChainCode(**data)
            self.list_chaincode[name] = chain_code

    def getChainCode(self, name):
        '''
        Returns:
            (ChainCode): Get the chaincode by its name
        '''
        return self.list_chaincode.get(name)

    def getInitialChainCode(self):
        if len(self.list_chaincode) > 0:
            first_chaincode = list(self.list_chaincode.keys())[0]
            return self.getChainCode(first_chaincode)
        return

    def create_orderer(self):

        number_of_orderer = 0
        orderer_name = ""

        while number_of_orderer <= self.number_of_orderer:

            if number_of_orderer == 0:
                orderer_name = "orderer.{}".format(self.organization.domain)
                number_of_orderer = 1

            else:
                orderer_name = "orderer{}.{}".format(
                    number_of_orderer,
                    self.organization.domain)

            NetworkServer.ORDERER_SERVER_EXTERN_PORT += 1

            server = OrdererServer(host=orderer_name,
                                   port=NetworkServer.ORDERER_SERVER_EXTERN_PORT)

            server.intern_port = NetworkServer.ORDERER_SERVER_INTERN_PORT

            self.list_orderer.append(server)

            number_of_orderer += 1

    def getAllOrderer(self, number_of_orderer=2):
        for orderer_server in self.list_orderer[number_of_orderer:]:
            yield orderer_server

    def getlist_policies(self):

        list_policies = {
            "Readers": ["MEMBER"],
            "Writers": ["MEMBER"],
            "Admins": ["ADMIN"]
        }

        policies = ""

        for name, role in list_policies.items():
            policies += Policies(name, self.organization.id, role=role).dump()

        return policies

    def getHostname(self):
        return self.server.host

    def getHostport(self):
        return self.server.port

    def getAnchorPeer(self):
        return self.server.getinternal_address()

    def getOrdererMsp(self):
        return "{}MSP".format(self.organization.name)

    def dump(self):

        self.organization.id = "{}MSP".format(self.organization.name)

        self.organization.mspdir = "crypto-config/ordererOrganizations/{}/msp".format(
            self.organization.domain)

        str_org = "\n  - &{0}\n\n  \tName: {0}\n\n  \tID: {1}\n\n  \tMSPDir: {2}\n\n\n  \tPolicies:{3}".format(
            self.organization.name, self.organization.id, self.organization.mspdir, self.getlist_policies())

        return str_org

    def list_version(self):
        data_str = ""

        for version_name, is_enable in self.version.items():
            data_str += "\n\n\t\t  {}: {}".format(
                version_name, str(is_enable).lower())

        return data_str

    def dump_all_addresses(self):
        app_str = ""
        number_of_orderer = 0

        while number_of_orderer <= self.number_of_orderer:

            port = 7050

            if number_of_orderer == 0:
                orderer_name = "orderer.{}".format(self.organization.domain)
                number_of_orderer = 1
            else:
                orderer_name = "orderer{}.{}".format(
                    number_of_orderer,
                    self.organization.domain)
            server = Server(host=orderer_name, port=port)

            app_str += '''                
                - {}'''.format(
                server.getaddress())

            number_of_orderer += 1

        return app_str

    def getAllOrdererName(self):
        app_str = ""
        number_of_orderer = 0

        while number_of_orderer <= self.number_of_orderer:

            if number_of_orderer == 0:
                orderer_name = "orderer"
                number_of_orderer = 1
            else:
                orderer_name = "orderer{}".format(
                    number_of_orderer)

            app_str += '''                
        - Hostname: {}'''.format(
                orderer_name)

            number_of_orderer += 1

        return app_str

    def create_consenter(self, padding_left=""):
        app_str = ""
        number_of_orderer = 0

        while number_of_orderer <= self.number_of_orderer:

            port = 7050

            if number_of_orderer == 0:
                orderer_name = "orderer.{}".format(self.organization.domain)
                number_of_orderer = 1
            else:
                orderer_name = "orderer{}.{}".format(
                    number_of_orderer,
                    self.organization.domain)

            app_str += """        
                - Host: {0}
                  Port: {1}
                  ClientTLSCert: crypto-config/ordererOrganizations/{2}/orderers/{0}/tls/server.crt
                  ServerTLSCert: crypto-config/ordererOrganizations/{2}/orderers/{0}/tls/server.crt

            """.format(orderer_name, port, self.organization.domain)

            number_of_orderer += 1

        return app_str

    def getBlockValidationPolicies(self):
        data = {
            "BlockValidation": "ANY Writers"
        }

        return self.getPolicies(data)

    def dump_orderer(self):

        datra_str = '''


################################################################################
#
#   SECTION: Orderer
#
#   - This section defines the values to encode into a config transaction or
#   genesis block for orderer related parameters
#
################################################################################
Orderer: &{}

    # Orderer Type: The orderer implementation to start
    # Available types are "solo","kafka"  and "etcdraft"
    OrdererType: {}

    Addresses:
        - {}

    # Batch Timeout: The amount of time to wait before creating a batch
    BatchTimeout: {}s

    # Batch Size: Controls the number of messages batched into a block
    BatchSize:

{}

    Kafka:
        # Brokers: A list of Kafka brokers to which the orderer connects
        # NOTE: Use IP:port notation
        Brokers:
            - 127.0.0.1:9092

    # EtcdRaft defines configuration which must be set when the "etcdraft"
    # orderertype is chosen.
    EtcdRaft:
        # The set of Raft replicas for this network. For the etcd/raft-based
        # implementation, we expect every replica to also be an OSN. Therefore,
        # a subset of the host:port items enumerated in this list should be
        # replicated under the Orderer.Addresses key above.
        Consenters:
            {}
    # Organizations is the list of orgs which are defined as participants on
    # the orderer side of the network
    Organizations:

    # Policies defines the set of policies at this level of the config tree
    # For Orderer policies, their canonical path is
    #   /Channel/Orderer/<PolicyName>
    Policies:
        Readers:
            Type: ImplicitMeta
            Rule: "ANY Readers"
        Writers:
            Type: ImplicitMeta
            Rule: "ANY Writers"
        Admins:
            Type: ImplicitMeta
            Rule: "MAJORITY Admins"
        # BlockValidation specifies what signatures must be included in the block
        # from the orderer for the peer to validate it.
        BlockValidation:
            Type: ImplicitMeta
            Rule: "ANY Writers"

                '''.format(self.name, self.type, self.address,
                           self.batch_timeout,
                           self.batch_size.dump(),
                           self.create_consenter())

        return datra_str
