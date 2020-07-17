
import yaml
import sys
from .organization import Organization
from .capabilities import Capability
from .application import Application
from .orderer import Orderer
from .channel import Channel
from .profile import Profile
from .genesis import Genesis
from .consurtium import Consurtium
from .network_file_handler import NetworkFileHandler
from .cache import CacheServer
from .hycomposer import HyperledgerComposer


def toString(value):
    if value:
        return str(value)
    return ""


class NetworkAdministrator(Organization):
    def __init__(self, data):
        self.first_name = data.get("first_name")
        self.domain = data.get("domain")
        self.last_name = data.get("last_name")
        self.email_address = data.get("email_address").capitalize()
        self.organization_name = data.get("organization_name")
        self.login_username = data.get("login_name")
        self.login_password = data.get("login_password")
        self.organization = None


class Network:
    def __init__(self):
        self.list_version = {"V1_4_4": True, "V1_4_2": False,
                             "V1_3": False, "V1_2": False, "V1_1": False}
        self.name = None
        self.organization = {}
        self.capabilities = None
        self.orderer = None
        self.admin = None
        self.application = Application(self.list_version)
        self.current_version = None
        self.consurtium = None
        self.list_org_name = []
        self.genesis = None
        self.total_number_of_peer_per_organization = 0
        self.hy_composer = None
        self.__cache_server = CacheServer()

    def getCurrentVersion(self):
        return self.current_version.replace("_", ".").strip("V")

    def add_hy_composer(self, data):
        self.hy_composer = HyperledgerComposer(**data)

    def hasChainCode(self):
        return self.orderer.generate_chainecode

    def getInitialChainCode(self, return_type=None):
        ischaincode_exist = self.hasChainCode()
        if ischaincode_exist:
            chaincode = self.orderer.getInitialChainCode()
            if return_type == None:
                return str(not ischaincode_exist).lower(), chaincode.name, chaincode.directory, chaincode.language
            return chaincode
        else:
            if return_type == None:
                return str(not ischaincode_exist).lower(), "", "", ""
        return None,

    def addChainCode(self, name, data):
        self.orderer.add_chaincode(name, data)

    def addconsurtium(self, name=None, channelname=None):
        self.consurtium = Consurtium(name, list_version=self.list_version)
        self.consurtium.addChannel(channelname)

    def getNumberOfPeers(self):
        return self.total_number_of_peer_per_organization

    def getOrgDomain(self, name, domain):
        name = name.lower()
        domain = domain.lower()
        if name not in domain:
            return "{}.{}".format(
                name, domain)
        return domain

    def channel(self):
        if (self.consurtium.numberOfChannel() == 1):
            return self.consurtium.getInitialChannel()

    def addorg(self, name=None, domain=None, organization=None, index=0):
        org_domain = None
        if name and organization == None:
            org_domain = self.getOrgDomain(name, domain)
            organization = Organization(
                name, domain=domain, has_anchor=True, index=index)
            self.organization[org_domain] = organization
        else:
            org_domain = organization.getDomain()
            self.organization[org_domain] = organization

        if organization.isAdmin():
            self.admin.organization = organization

    def getOrganization(self, number=-1):
        list_org = list(self.organization.values())

        if number >= 0 and (number < len(list_org)):
            return list_org[number]
        return list_org

    def getInitialOrganization(self):
        '''
        Returns:
          Organization:
        '''
        return self.getOrganization(0)

    def getAdminEmail(self):
        return self.admin.organization.getAdminEmail()

    def addnetwork_admin(self, data):
        self.admin = NetworkAdministrator(data)
        self.genesis = Genesis(
            (self.admin.organization_name.lower()).capitalize())

        # organization = Organization(
        #     self.admin.organization_name, domain=self.admin.domain, type_org="admin", has_anchor=True)

        # organization.addAllPeers(data.get("number_of_peer"))
        # self.addorg(organization=organization)

        #self.admin.organization = organization

    def getAdminOrg(self):
        '''
        return: Organization
        '''
        return self.admin.organization

    def addnetwork_orderer(self, data):
        org_name = data["org"].get("name")
        if org_name:
            self.orderer = Orderer(data=data, list_version=self.list_version)
            self.orderer.create_orderer()
            # org_domain = self.orderer.getHostname()
            # self.organization[org_domain] = self.orderer

    def getOrgByDomain(self, domain):
        return self.organization.get(domain)

    def getListOrg(self, padding_left=""):
        list_org = ""
        list_org_name = []
        list_org_obj = []
        for org in self.getOrganization():
            if isinstance(org, Organization):
                list_org += """
                {} - * {} """.format(padding_left, org.name.upper())
                list_org_name.append(org.name.lower())
                list_org_obj.append(org)

        return list_org

    def getPeersConfigForAllOrgs(self):
        peers_config = ""

        for org in self.getOrganization():

            if isinstance(org, Organization):
                peers_config += """
    # ---------------------------------------------------------------------------
    # {0}:
    # ---------------------------------------------------------------------------
    - Name: {0}
      Domain: {1}
      EnableNodeOUs: {2}
      Template:
        Count: {3}
      Users:
        Count: 1
        """.format(org.name, org.getDomain(), org.getEnableNodeOUsAsStr(), org.peerLen())

        return peers_config

    def networkLogin(self):
        return self.admin.login_username+":"+self.admin.login_password

    def ca_certificate_template(self):

        template = ""
        index = -1

        for org in self.getOrganization():
            if isinstance(org, Organization):
                if index < 0:
                    ca_name = "ca"
                else:

                    ca_name = "ca{}".format(index)

                template += """

    {2}:
        image: hyperledger/fabric-ca:$IMAGE_TAG
        environment:
          - FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server
          - FABRIC_CA_SERVER_CA_NAME=ca-{0}
          - FABRIC_CA_SERVER_TLS_ENABLED=true
          - FABRIC_CA_SERVER_TLS_CERTFILE=/etc/hyperledger/fabric-ca-server-config/ca.{1}-cert.pem
          - FABRIC_CA_SERVER_TLS_KEYFILE=/etc/hyperledger/fabric-ca-server-config/${{BYFN_CA_PRIVATE_KEY}}
          - FABRIC_CA_SERVER_PORT={4}

        ports:
          - "{3}:{4}"
        command: sh -c 'fabric-ca-server start --ca.certfile /etc/hyperledger/fabric-ca-server-config/ca.{1}-cert.pem --ca.keyfile /etc/hyperledger/fabric-ca-server-config/${{BYFN_CA_PRIVATE_KEY}} -b {5} -d'
        volumes:
          - ./crypto-config/peerOrganizations/{1}/ca/:/etc/hyperledger/fabric-ca-server-config
          - ./fabric-ca-server/:/etc/hyperledger/fabric-ca-server
          - /etc/localtime:/etc/localtime:ro
          - /etc/timezone:/etc/timezone:ro
        container_name: ca.{1}
        restart: always
        networks:
          - byfn
        """.format(
                    org.name.lower(),
                    org.getCaCertificate().getCaName(),
                    ca_name,
                    org.getCaCertificate().getCaExternPortNumber(),
                    org.getCaCertificate().getCaInternPortNumber(),
                    self.networkLogin()
                )

            else:
                index -= 1

            index += 1

        return template

    def create_ca_certificate(self):

        template = """
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

networks:
  byfn:

services:
   {}
        """.format(self.ca_certificate_template())

        # with open(NetworkFileHandler.networkpath("docker-compose-ca.yaml"), "w") as f:
        #     f.write(template)

        NetworkFileHandler.create_fabric_file(
            "docker-compose-ca.yaml", template)

    def create_profile(self):

        list_org_name = ""
        list_org_last = ""

        for org_name in self.getCachedData("list_org"):
            list_org_name += """
                    - *{}
          """.format(org_name.upper())

            list_org_last += """
                - *{}
            """.format(org_name.upper())

        app_str = """

################################################################################
#
#   Profile
#
#   - Different configuration profiles may be encoded here to be specified
#   as parameters to the configtxgen tool
#
################################################################################
Profiles:

    {12}:
        <<: *{0}
        Orderer:
            <<: *{1}
            Organizations:
                - *{2}
            Capabilities:
                <<: *{3}
        Consortiums:
            {4}:
                Organizations:
{5}

    {13}:
        Consortium: {4}
        <<: *{0}
        Application:
            <<: *{6}
            Organizations:
                {5}
            Capabilities:
                <<: *{7}

    SampleMultiNodeEtcdRaft:
        <<: *{0}
        Capabilities:
            <<: *{8}
        Orderer:
            <<: *{1}
            OrdererType: {9}
            EtcdRaft:
                Consenters:
                    {10}
            Addresses:
                {11}

            Organizations:
            - *{2}
            Capabilities:
                <<: *{3}
        Application:
            <<: *{6}
            Organizations:
            - <<: *{2}
        Consortiums:
            {4}:
                Organizations:
                {14}
""".format(
            self.channel().default_name,
            self.orderer.name,
            self.orderer.organization.name,
            self.orderer.capability_name,
            self.name,
            list_org_name,
            self.application.name,
            self.application.capability_name,
            self.channel().capability_name,
            self.orderer.type,
            self.orderer.create_consenter(padding_left="\t"*2),
            self.orderer.dump_all_addresses(),
            self.genesis.getName(),
            self.channel().name,
            list_org_last
        )

        return app_str

    def create_cli_services(self):

        list_volumes = []
        list_service = []
        list_depend = []

        host_name = self.orderer.getHostname()
        list_volumes.append("""
  {}: """.format(host_name))
        list_depend.append("""
      - {} """.format(host_name))

        list_service.append("""
  {0}:
    container_name: {0}
    restart: always
    extends:
      file:  base/docker-compose-base.yaml
      service: {0}
    networks:
      - byfn
                    """.format(host_name))

        for org in self.getOrganization():
            if isinstance(org, Organization):
                for peer in org.list_peer:
                    peer_host_name = peer.getHostname()
                    list_volumes.append("""
  {}: """.format(peer_host_name))

                    list_depend.append("""
      - {}""".format(peer_host_name))

                    list_service.append("""
  {0}:
    container_name: {0}
    restart: always
    extends:
      file:  base/docker-compose-base.yaml
      service: {0}
    networks:
      - byfn
                    """.format(peer_host_name))

        return "".join(list_volumes), "".join(list_service), "".join(list_depend)

    def create_cli(self):

        volumes, services, depends_on = self.create_cli_services()

        org = self.getOrganization(0)

        chain_code = self.getInitialChainCode(return_type=object)

        chain_code_data = ""

        if self.hasChainCode():
            chain_code_data = """- {0}/{1}:/opt/gopath/src/github.com/chaincode/{2}/{3}/{1}/""".format(chain_code.directory,
                                                                                                       chain_code.language, org.name.lower(), chain_code.name)

        template = """
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

volumes:
  {0}
  hyperledger_explorer_postgresql_data:

networks:
  byfn:

services:

  {1}

  cli:
    container_name: cli
    image: hyperledger/fabric-tools:$IMAGE_TAG
    restart: always
    tty: true
    stdin_open: true
    environment:
      - SYS_CHANNEL=$SYS_CHANNEL
      - GOPATH=/opt/gopath
      - CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock
      # - FABRIC_LOGGING_SPEC=DEBUG
      - FABRIC_LOGGING_SPEC=INFO
      - CORE_PEER_ID=cli
      - CORE_PEER_ADDRESS={2}:7051
      - CORE_PEER_LOCALMSPID={3}
      - CORE_PEER_TLS_ENABLED=true
      - CORE_PEER_TLS_CERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{6}/peers/{2}/tls/server.crt
      - CORE_PEER_TLS_KEY_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{6}/peers/{2}/tls/server.key
      - CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{6}/peers/{2}/tls/ca.crt
      - CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{6}/users/{5}/msp
    working_dir: /opt/gopath/src/github.com/hyperledger/fabric/peer
    command: /bin/bash
    volumes:
        - /var/run/:/host/var/run/
        - ./chaincode/:/opt/gopath/src/github.com/chaincode
        {7}
        - ./crypto-config:/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/
        - ./scripts:/opt/gopath/src/github.com/hyperledger/fabric/peer/scripts/
        - ./channel-artifacts:/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts
        - /etc/localtime:/etc/localtime:ro
        - /etc/timezone:/etc/timezone:ro

    depends_on:
        {4}
    networks:
      - byfn

  explorer:
    container_name: explorer
    restart: always
    extends:
      file:  ../hyperledger-explorer/docker-compose-explorer.yml
      service: explorer
    links:
      - postgresql
    depends_on:
      - postgresql
    networks:
      - byfn

  postgresql:
    container_name: postgres
    restart: always
    extends:
      file:  ../hyperledger-explorer/docker-compose-postgres.yml
      service: postgresql
    networks:
      - byfn

        """.format(
            volumes,
                   services,
                   org.getAnchorPeer().getHostname(),
                   org.getId(),
                   depends_on,
                   self.getAdminEmail().capitalize(),
                   org.getDomain(),
                   chain_code_data
        )

        # with open(NetworkFileHandler.networkpath("docker-compose-cli.yaml"), "w") as f:
        #     f.write(template)

        NetworkFileHandler.create_fabric_file(
            "docker-compose-cli.yaml", template)

    def create_capability(self):

        capability_str = '''

################################################################################
#
#   SECTION: Capabilities
#
#   - This section defines the capabilities of fabric network. This is a new
#   concept as of v1.1.0 and should not be utilized in mixed networks with
#   v1.0.x peers and orderers.  Capabilities define features which must be
#   present in a fabric binary for that binary to safely participate in the
#   fabric network.  For instance, if a new MSP type is added, newer binaries
#   might recognize and validate the signatures from this type, while older
#   binaries without this support would be unable to validate those
#   transactions.  This could lead to different versions of the fabric binaries
#   having different world states.  Instead, defining a capability for a channel
#   informs those binaries without this capability that they must cease
#   processing transactions until they have been upgraded.  For v1.0.x if any
#   capabilities are defined (including a map with all capabilities turned off)
#   then the v1.0.x peer will deliberately crash.
#
################################################################################
Capabilities:
    # Channel capabilities apply to both the orderers and the peers and must be
    # supported by both.
    # Set the value of the capability to true to require it.
    Channel: &{}
{}

    # Orderer capabilities apply only to the orderers, and may be safely
    # used with prior release peers.
    # Set the value of the capability to true to require it.
    Orderer: &{}
{}

    # Application capabilities apply only to the peer network, and may be safely
    # used with prior release orderers.
    # Set the value of the capability to true to require it.
    Application: &{}
{}

        '''.format(self.channel().capability_name, self.channel().list_version(),
                   self.orderer.capability_name, self.orderer.list_version(),
                   self.application.capability_name, self.application.list_version())

        return capability_str

    def create_configtx_file(self):

        list_org_name = []
        list_org_obj = []

        section_org = """
    - &{0}
        # DefaultOrg defines the organization which is used in the sampleconfig
        # of the fabric.git development environment
        Name: {0}

        # ID to load the MSP definition as
        ID: {0}MSP

        # MSPDir is the filesystem path which contains the MSP configuration
        MSPDir: crypto-config/ordererOrganizations/{1}/msp

        # Policies defines the set of policies at this level of the config tree
        # For organization policies, their canonical path is usually
        #   /Channel/<Application|Orderer>/<OrgName>/<PolicyName>
        Policies:
            Readers:
                Type: Signature
                Rule: "OR('{0}MSP.member')"
            Writers:
                Type: Signature
                Rule: "OR('{0}MSP.member')"
            Admins:
                Type: Signature
                Rule: "OR('{0}MSP.admin')"
            """.format(self.orderer.organization.name, self.orderer.getDomain())

        section_capability = """
################################################################################
#
#   SECTION: Capabilities
#
#   - This section defines the capabilities of fabric network. This is a new
#   concept as of v1.1.0 and should not be utilized in mixed networks with
#   v1.0.x peers and orderers.  Capabilities define features which must be
#   present in a fabric binary for that binary to safely participate in the
#   fabric network.  For instance, if a new MSP type is added, newer binaries
#   might recognize and validate the signatures from this type, while older
#   binaries without this support would be unable to validate those
#   transactions.  This could lead to different versions of the fabric binaries
#   having different world states.  Instead, defining a capability for a channel
#   informs those binaries without this capability that they must cease
#   processing transactions until they have been upgraded.  For v1.0.x if any
#   capabilities are defined (including a map with all capabilities turned off)
#   then the v1.0.x peer will deliberately crash.
#
################################################################################
Capabilities:
        """

        list_capability_version = {
            "Channel": {
                "V1_4_3": True,
                "V1_3": False,
                "V1_1": False
            },
            "Orderer": {
                "V1_4_2": True,
                "V1_1": False
            },
            "Application": {
                "V1_4_2": True,
                "V1_3": False,
                "V1_2": False,
                "V1_1": False
            }
        }

        list_capability = ["Channel", "Orderer", "Application"]

        for capability in list_capability:

            section_capability += """
    # {0} capabilities apply to both the orderers and the peers and must be
    # supported by both.
    # Set the value of the capability to true to require it.
    {0}: &{0}Capabilities
          """.format(capability)

            for version, is_select in list_capability_version.get(capability).items():
                section_capability += """
        # {0} for {2} is a catchall flag for behavior which has been
        # determined to be desired for all orderers and peers running at the {0}
        # level, but which would be incompatible with orderers and peers from
        # prior releases.
        # Prior to enabling {0} {3} capabilities, ensure that all
        # orderers and peers on a {3} are at {0} or later.
        {0}: {1}
          """.format(version, str(is_select).lower(), capability, capability.lower())

        for org in self.getOrganization():

            if isinstance(org, Organization):

                list_org_name.append((org.name).lower())
                list_org_obj.append(org)
                anchor_peer = org.getAnchorPeer()

                if org.isAdmin():
                    section_org += """
    - &{0}
        # DefaultOrg defines the organization which is used in the sampleconfig
        # of the fabric.git development environment
        Name: {0}MSP

        # ID to load the MSP definition as
        ID: {0}MSP

        MSPDir: crypto-config/peerOrganizations/{3}/msp

        # Policies defines the set of policies at this level of the config tree
        # For organization policies, their canonical path is usually
        #   /Channel/<Application|Orderer>/<OrgName>/<PolicyName>
        Policies:
            Readers:
                Type: Signature
                Rule: "OR('{0}MSP.admin', '{0}MSP.peer', '{0}MSP.client')"
            Writers:
                Type: Signature
                Rule: "OR('{0}MSP.admin','{0}MSP.peer','{0}MSP.client')"
            Admins:
                Type: Signature
                Rule: "OR('{0}MSP.admin')"

        # leave this flag set to true.
        AnchorPeers:
            # AnchorPeers defines the location of peers which can be used
            # for cross org gossip communication.  Note, this value is only
            # encoded in the genesis block in the Application section context
            - Host: {1}
              Port: {2}
            """.format(
                        org.name,
                        anchor_peer.getHostname(),
                        anchor_peer.intern_port,
                        org.getDomain()
                    )

                else:
                    section_org += """
    - &{0}
        # DefaultOrg defines the organization which is used in the sampleconfig
        # of the fabric.git development environment
        Name: {0}MSP

        # ID to load the MSP definition as
        ID: {0}MSP

        MSPDir: crypto-config/peerOrganizations/{3}/msp

        # Policies defines the set of policies at this level of the config tree
        # For organization policies, their canonical path is usually
        #   /Channel/<Application|Orderer>/<OrgName>/<PolicyName>
        Policies:
            Readers:
                Type: Signature
                Rule: "OR('{0}MSP.admin', '{0}MSP.peer', '{0}MSP.client')"
            Writers:
                Type: Signature
                Rule: "OR('{0}MSP.admin', '{0}MSP.client')"
            Admins:
                Type: Signature
                Rule: "OR('{0}MSP.admin')"

        # leave this flag set to true.
        AnchorPeers:
            # AnchorPeers defines the location of peers which can be used
            # for cross org gossip communication.  Note, this value is only
            # encoded in the genesis block in the Application section context
            - Host: {1}
              Port: {2}
                    """.format(
                        org.name,
                        anchor_peer.getHostname(),
                        anchor_peer.intern_port,
                        org.getDomain())

        # with open(NetworkFileHandler.networkpath("configtx.yaml"), "w") as f:
        template = '''
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

---
################################################################################
#
#   Section: Organizations
#
#   - This section defines the different organizational identities which will
#   be referenced later in the configuration.
#
################################################################################
Organizations:
    # SampleOrg defines an MSP using the sampleconfig.  It should never be used
    # in production but may be used as a template for other definitions
    {0}

{1}

################################################################################
#
#   SECTION: Application
#
#   - This section defines the values to encode into a config transaction or
#   genesis block for application related parameters
#
################################################################################
Application: &ApplicationDefaults

    # Organizations is the list of orgs which are defined as participants on
    # the application side of the network
    Organizations:

    # Policies defines the set of policies at this level of the config tree
    # For Application policies, their canonical path is
    #   /Channel/Application/<PolicyName>
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

    Capabilities:
        <<: *ApplicationCapabilities
{2}

{3}

{4}

            '''.format(
            section_org,
            section_capability,
            self.orderer.dump_orderer(),
            self.channel().channel_dump(),
            self.create_profile()
        )

        #  template = file_begin

        # template += self.orderer.dump()
        # template += "\n\n"

        # f.write(file_begin)

        # f.write(self.orderer.dump())
        # f.write("\n\n")
        # template += org.dump()
        # template += "\n\n"
        # f.write(org.dump())
        # f.write("\n\n")

        # template += self.create_capability()
        # template += self.application.dump_application()
        # template += self.orderer.dump_orderer()
        # template += self.channel().channel_dump()
        # template += self.create_profile()

        # f.write(self.create_capability())
        # f.write(self.application.dump_application())
        # f.write(self.orderer.dump_orderer())
        # f.write(self.channel().channel_dump())
        # f.write(self.create_profile())
        NetworkFileHandler.create_fabric_file("configtx.yaml", template)

    def create_cryptoconfig_file(self):

        template = '''

  # Copyright IBM Corp. All Rights Reserved.
  #
  # SPDX-License-Identifier: Apache-2.0
  #

  # ---------------------------------------------------------------------------
  # "OrdererOrgs" - Definition of organizations managing orderer nodes
  # ---------------------------------------------------------------------------
  OrdererOrgs:
    # ---------------------------------------------------------------------------
    # Orderer
    # ---------------------------------------------------------------------------
    - Name: {0}
      Domain: {1}
      EnableNodeOUs: {3}
      # ---------------------------------------------------------------------------
      # "Specs" - See PeerOrgs below for complete description
      # ---------------------------------------------------------------------------
      Specs:
        {2}

  # ---------------------------------------------------------------------------
  # "PeerOrgs" - Definition of organizations managing peer nodes
  # ---------------------------------------------------------------------------
  PeerOrgs:
    {4}
'''.format(self.orderer.organization.name,
           self.orderer.organization.domain,
           self.orderer.getAllOrdererName(),
           self.orderer.getEnableNodeOUsAsStr(),
           self.getPeersConfigForAllOrgs()
           )

        NetworkFileHandler.create_fabric_file("crypto-config.yaml", template)

        # with open(NetworkFileHandler.networkpath("crypto-config.yaml"), "w") as f:
        #     f.write(template)

    def create_couchdb(self):
        template = ""

        for org in self.getOrganization():
            if isinstance(org, Organization):
                for peer in org.list_peer:
                    peer_host_name = peer.getHostname()
                    couchdb = peer.getCouchDb()

                    template += """
  {0}:
    container_name: {0}
    restart: always
    image: hyperledger/fabric-couchdb
    # Populate the COUCHDB_USER and COUCHDB_PASSWORD to set an admin user and password
    # for CouchDB.  This will prevent CouchDB from operating in an "Admin Party" mode.
    environment:
      - COUCHDB_USER=
      - COUCHDB_PASSWORD=
    # Comment/Uncomment the port mapping if you want to hide/expose the CouchDB service,
    # for example map it to utilize Fauxton User Interface in dev environments.
    ports:
      - "{2}:{3}"
    networks:
      - byfn

  {1}:
    environment:
      - CORE_LEDGER_STATE_STATEDATABASE=CouchDB
      - CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS={0}:5984
      # The CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME and CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD
      # provide the credentials for ledger to connect to CouchDB.  The username and password must
      # match the username and password set for the associated CouchDB.
      - CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=
      - CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=
    restart: always
    depends_on:
      - {0}
        """.format(couchdb.host, peer_host_name, couchdb.port, couchdb.intern_port)

        return template

    def create_couchdb_file(self):
        template = """
        # Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

networks:
  byfn:

services:
  {}

        """.format(self.create_couchdb())

        NetworkFileHandler.create_fabric_file(
            "docker-compose-couch.yaml", template)

        # self.create_file("docker-compose-couch.yaml", template)

    def create_file(self, file_name, template):
        with open(NetworkFileHandler.networkpath(file_name), "w") as f:
            f.write(template)

    def create_2e2(self):
        list_volumes = []
        list_service = []
        list_ca_certificate = []
        index = -1

        host_name = self.orderer.getHostname()
        list_service.append("""
  {0}:
    container_name: {0}
    restart: always
    extends:
      file:  base/docker-compose-base.yaml
      service: {0}
    networks:
      - byfn
                    """.format(host_name))

        for org in self.getOrganization():

            if isinstance(org, Organization):
                ca_name = "ca%d" % index

                if index < 0:
                    ca_name = "ca"
                list_ca_certificate += """
  {2}:
    image: hyperledger/fabric-ca:$IMAGE_TAG
    restart: always
    environment:
      - FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server
      - FABRIC_CA_SERVER_CA_NAME=ca-{1}
      - FABRIC_CA_SERVER_TLS_ENABLED=true
      - FABRIC_CA_SERVER_TLS_CERTFILE=/etc/hyperledger/fabric-ca-server-config/{1}-cert.pem
      - FABRIC_CA_SERVER_TLS_KEYFILE=/etc/hyperledger/fabric-ca-server-config/CA_PRIVATE_KEY
    ports:
      - "{3}:{4}"
    command: sh -c 'fabric-ca-server start --ca.certfile /etc/hyperledger/fabric-ca-server-config/{1}-cert.pem --ca.keyfile /etc/hyperledger/fabric-ca-server-config/CA_PRIVATE_KEY -b {5} -d'
    volumes:
      - ./crypto-config/peerOrganizations/{0}/ca/:/etc/hyperledger/fabric-ca-server-config
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    container_name: {1}
    networks:
      - byfn
                """.format(
                    org.getDomain(),
                    org.getCaCertificate().getCaName(),
                    ca_name,
                    org.getCaCertificate().getCaExternPortNumber(),
                    org.getCaCertificate().getCaInternPortNumber(),
                    self.networkLogin()
                )

                for peer in org.list_peer:
                    peer_host_name = peer.getHostname()
                    list_volumes.append("""
  {}: """.format(peer_host_name))

                    list_service.append("""
  {0}:
    container_name: {0}
    restart: always
    extends:
      file:  base/docker-compose-base.yaml
      service: {0}
    networks:
      - byfn
                    """.format(peer_host_name))
            index += 1

        return "".join(list_volumes), "".join(list_service), "".join(list_ca_certificate)

    def create_e2e_file(self):

        volumes, service, certificate = self.create_2e2()

        template = """
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

volumes:
{0}

networks:
  byfn:
services:

  {2}

  {1}

        """.format(volumes, service, certificate)
        NetworkFileHandler.create_fabric_file(
            "docker-compose-e2e-template.yaml", template)

        # self.create_file("docker-compose-e2e-template.yaml", template)

    def create_orderer(self):
        list_orderer = []
        list_orderer_host = []

        for orderer in self.orderer.getAllOrderer(1):
            list_orderer.append("""
  {}: """.format(orderer.host))

            list_orderer_host.append("""
  {orderer.host}:
    extends:
      file: base/peer-base.yaml
      service: orderer-base
    container_name: {orderer.host}
    restart: always
    networks:
    - byfn
    volumes:
        - ./channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block
        - ./crypto-config/ordererOrganizations/{domain_name}/orderers/{orderer.host}/msp:/var/hyperledger/orderer/msp
        - ./crypto-config/ordererOrganizations/{domain_name}/orderers/{orderer.host}/tls/:/var/hyperledger/orderer/tls
        - {orderer.host}:/var/hyperledger/production/orderer
        - /etc/localtime:/etc/localtime:ro
        - /etc/timezone:/etc/timezone:ro
    ports:
    - {orderer.port}:{orderer.intern_port}
  """.format(orderer=orderer, domain_name=self.orderer.getDomain()))

        return "".join(list_orderer), "".join(list_orderer_host)

    def create_orderer_file(self):
        orderer, service = self.create_orderer()
        template = """
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

volumes:
{}

networks:
  byfn:

services:

  {}

        """.format(orderer, service)

        # self.create_file("docker-compose-etcdraft2.yaml", template)
        NetworkFileHandler.create_fabric_file(
            "docker-compose-etcdraft2.yaml", template)

    def create_ccp_template(self):

        yaml_template_org_peers = []
        yaml_template_peers = []
        json_template_org_peers = []
        json_template_peers = []

        for peer_number in range(self.getNumberOfPeers()):
            yaml_template_org_peers.append("""
    - ${{PEER{0}}}
            """.format(peer_number))
            json_template_org_peers.append("""
    "${{PEER{0}}}"
            """.format(peer_number))

            yaml_template_peers.append("""
  ${{PEER{0}}}:
    url: grpcs://localhost:${{P{0}PORT}}
    tlsCACerts:
      pem: |
        ${{PEERPEM}}
    grpcOptions:
      ssl-target-name-override: ${{PEER{0}}}
      hostnameOverride: ${{PEER{0}}}
            """.format(peer_number))

            json_template_peers.append("""
        "${{PEER{0}}}": {{
            "url": "grpcs://${{PEER{0}}}:${{P{0}PORT}}",
            "tlsCACerts": {{
                "path": "${{PEERPEM}}"
            }},
            "grpcOptions": {{
                "ssl-target-name-override": "${{PEER{0}}}",
                "hostnameOverride": "${{PEER{0}}}"
            }}
        }}
            """.format(peer_number))

        return "".join(yaml_template_org_peers), "".join(yaml_template_peers), \
            ",".join(json_template_org_peers), ",".join(json_template_peers)

    def create_ccp_template_file(self):
        list_template = {}

        yaml_org_peer, yaml_peer, json_org_peer, json_peer = self.create_ccp_template()

        list_template["ccp-template.yaml"] = """

name: ${{ORG}}
version: 1.0.0
client:
  organization: ${{ORG}}
  connection:
    timeout:
      peer:
        endorser: '300'
organizations:
  ${{ORG}}:
    mspid: ${{MSP}}
    peers:
{0}
    certificateAuthorities:
    - ${{CA}}
peers:
{1}
certificateAuthorities:
  ${{CA}}:
    url: https://localhost:${{CAPORT}}
    caName: ${{CANAME}}
    tlsCACerts:
      pem: |
        ${{CAPEM}}
    httpOptions:
      verify: false

        """.format(yaml_org_peer, yaml_peer)

        list_template["ccp-template.json"] = """
{{
    "name": "${{ORG}}",
    "version": "1.0.0",
    "client": {{
        "organization": "${{ORG}}",
        "connection": {{
            "timeout": {{
                "peer": {{
                    "endorser": "300"
                }}
            }}
        }}
    }},
    "organizations": {{
        "${{ORG}}": {{
            "mspid": "${{MSP}}",
            "peers": [
                {0}
            ],
            "certificateAuthorities": [
                "${{CA}}"
            ]
        }}
    }},
    "peers": {{
        {1}
    }},
    "certificateAuthorities": {{
        "${{CA}}": {{
            "url": "https://${{CA}}:${{CAPORT}}",
            "tlsCACerts": {{
                "path": "${{CAPEM}}"
            }},
            "caName": "${{CANAME}}",
            "httpOptions": {{
                "verify": false
            }}
        }}
    }}
}}

        """.format(json_org_peer, json_peer)

        for file_name, template_data in list_template.items():
            # self.create_file(file_name, template_data)
            NetworkFileHandler.create_fabric_file(file_name, template_data)

    def create_env_file(self):
        image_tag = self.current_version.replace("_", ".").strip("V")

        ischaincode_exist, chaincode, chaincode_directory, chaincode_language = self.getInitialChainCode()

        template = """
COMPOSE_PROJECT_NAME={9}
IMAGE_TAG={0}
SYS_CHANNEL={1}
ORDERER_TYPE={6}
DATABASE_TYPE=
CHANNEL_NAME={1}
DELAY=
LANGUAGE={8}
TIMEOUT=
VERBOSE=
NO_CHAINCODE={3}
COUNTER=1
MAX_RETRY=10
CHAINCODE_DIR={7}
CHAINCODE_NAME={2}
EXPLORER_PORT={5}
RUN_EXPLORER={4}
COMPOSE_HTTP_TIMEOUT=200
        """.format(
            image_tag,
                   self.channel().name.lower(),
                   chaincode,
                   ischaincode_exist,
                   str(self.hy_composer.install).lower(),
                   self.hy_composer.port,
                   self.orderer.type,
                   chaincode_directory,
                   chaincode_language,
                   self.name

        )

        template_shell_exporter = """#!/bin/bash

source config/.env

main(){
echo $IMAGE_TAG
echo $COMPOSE_PROJECT_NAME
echo $LANGUAGE
echo $CHANNEL_NAME
echo $NO_CHAINCODE
echo $MAX_RETRY
echo $CHAINCODE_DIR
echo $CHAINCODE_NAME
}

main
        """

        # self.create_file(".env", template)
        # self.create_file("env.sh", template_shell_exporter)
        NetworkFileHandler.create_fabric_file(".env", template)
        NetworkFileHandler.create_fabric_file(
            "env.sh", template_shell_exporter)

    def create_ccp_generate_template(self):

        index = 1
        index_main = 2

        template_main = """
    ORG=${{{}}}""".format(index_main)

        template = """
    sed -e "s#\\${{ORG}}#${0}#" \\""".format(index)

        template_exec = ["$ORG"]

        index += 1
        index_main += 1

        for i in range(self.getNumberOfPeers()):
            template += """
        -e "s#\\${{P{0}PORT}}#${1}#" \\""".format(i, index)

            template_exec.append("$P{}PORT".format(i))

            template_main += """
    P{}PORT=${{{}}}""".format(i, index_main)
            index += 1
            index_main += 1

        list_holder = ["CAPORT", "PEERPEM",
                       "CAPEM", "MSP", "DOMAIN", "CA"]

        for value in list_holder:
            template += """
        -e "s#\\${{{}}}#${}#" \\""".format(value, index)

            template_exec.append("${}".format(value))

            template_main += """
    {}=${{{}}}""".format(value, index_main)
            index += 1
            index_main += 1

        for i in range(self.getNumberOfPeers()):

            template += """
        -e "s#\\${{PEER{0}}}#${{{1}}}#" \\""".format(i, index)

            template_exec.append("$PEER{}".format(i))

            template_main += """
    PEER{}=${{{}}}""".format(i, index_main)
            index += 1
            index_main += 1

        template += """
        -e "s#\\${{CANAME}}#${{{}}}#" \\""".format(index)

        template_exec.append("$CANAME")

        template_main += """
    CANAME=${{{}}}""".format(index_main)

        return template, template_main, " ".join(template_exec)

    def create_ccp_generate_file(self):

        template_json, template_main, template_args = self.create_ccp_generate_template()

        template = '''#!/bin/bash

FABRIC_DIR=$PWD

CONNECXION_PROFILE_DIR=${{FABRIC_PATH}}/connecxion-profile

one_line_pem() {{

   echo "`awk 'NF {{sub(/\\\\\\n/, ""); printf " % s\\\\\\n",$0;}}' $1`"
}}

json_ccp() {{

    # local PP=$(one_line_pem $5)
    # local CP=$(one_line_pem $6)

    {0}
        ${{FABRIC_DIR}}/ccp-template.json
}}

 yaml_ccp() {{
    # local PP=$(one_line_pem $5)
    # local CP=$(one_line_pem $6)
    {0}
        ${{FABRIC_DIR}}/ccp-template.yaml | sed -e $\'s/\\\\\\\\n/\\\\\\n        /g\'
}}


usage(){{

    echo "usages"
}}


main(){{

    {1}


    if [ ! -d "$FABRIC_PATH/connecxion-profile" ]; then

            mkdir - p $FABRIC_PATH/connecxion-profile
    fi



    case $1 in
        yaml)
             echo "$(yaml_ccp {2})" > ${{CONNECXION_PROFILE_DIR}}/${{DOMAIN}}.yaml
            exit 0;;

        json)
            echo "$(json_ccp {2})" > ${{CONNECXION_PROFILE_DIR}}/${{DOMAIN}}.json
        ;;
        all)
            echo "$(json_ccp {2})" > ${{CONNECXION_PROFILE_DIR}}/${{DOMAIN}}.json
            echo "$(yaml_ccp {2})" > ${{CONNECXION_PROFILE_DIR}}/${{DOMAIN}}.yaml
        ;;
        *)
            usage
        ;;
    esac
}}


main $@
'''.format(template_json, template_main, template_args)

        NetworkFileHandler.create_script_file("ccp-generate.sh", template)

    def create_utils_template_for_peer(self, org):

        list_peer_template = []
        list_peer = []
        list_peer_obj = []

        for peer_index in range(len(org.list_peer)):

            peer = org.list_peer[peer_index]

            list_peer.append(peer.getHostname())
            list_peer_obj.append(peer)

            if peer_index == 0:
                list_peer_template.append("""
    if [ $PEER -eq {0} ]; then
      CORE_PEER_ADDRESS={1} """.format(peer_index, peer.getinternal_address()))
                if len(org.list_peer) == 1:
                    list_peer_template.append("""
    fi """)

            elif peer_index < (len(org.list_peer)-1):
                list_peer_template.append("""
    elif [ $PEER -eq {0} ]; then
      CORE_PEER_ADDRESS={1}""".format(peer_index, peer.getinternal_address()))
            else:
                list_peer_template.append("""
    else
      CORE_PEER_ADDRESS={}
    fi
            """.format(peer.getinternal_address()))

        self.__cache_server.append_session("list_peer", list_peer)
        self.__cache_server.append_session("list_peer_obj", list_peer_obj)

        return "".join(list_peer_template)

    def create_utils_template(self):
        function_orderer_global = """
  CORE_PEER_LOCALMSPID="{0}"
  CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/{1}/orderers/{2}/msp/tlscacerts/tlsca.{1}-cert.pem
  CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/{1}/users/{3}/msp
        """.format(
            self.orderer.getOrdererMsp(),
            self.orderer.organization.domain,
            self.orderer.getHostname(),
            self.getAdminEmail()
        )

        function_update_anchor_peer = """
  if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
    set -x
    peer channel update -o {0} -c $CHANNEL_NAME -f ./channel-artifacts/${{CORE_PEER_LOCALMSPID}}anchors.tx >&log.txt
    res=$?
    set +x
  else
    set -x
    peer channel update -o {0} -c $CHANNEL_NAME -f ./channel-artifacts/${{CORE_PEER_LOCALMSPID}}anchors.tx --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA >&log.txt
    res=$?
    set +x
  fi
  cat log.txt
  verifyResult $res "Anchor peer update failed"
  echo "===================== Anchor peers updated for org '$CORE_PEER_LOCALMSPID' on channel '$CHANNEL_NAME' ===================== "
  sleep $DELAY
  echo
        """.format(self.orderer.getAnchorPeer())

        # TODO:In the below line of code replace all the  organization name

        function_instantiate_chaincode = """
  # while 'peer chaincode' command can get the orderer endpoint from the peer
  # (if join was successful), let's supply it directly as we know it using
  # the "-o" option
  if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
    set -x
    peer chaincode instantiate -o {0} -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} -l ${{LANGUAGE}} -v ${{VERSION}} -c '{{"function":"initLedger","Args":[]}}' -P "AND ('DCMSP.peer','DPMSP.peer')" >&log.txt
    res=$?
    set +x
  else
    set -x
    peer chaincode instantiate -o {0} --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} -l ${{LANGUAGE}} -v ${{VERSION}} -c '{{"function":"initLedger","Args":[]}}' -P "AND ('DCMSP.peer','DPMSP.peer')" >&log.txt
    res=$?
    set +x
  fi
  cat log.txt
  verifyResult $res "Chaincode instantiation on peer${{PEER}}.${{ORG}} on channel '$CHANNEL_NAME' failed"
  echo "===================== Chaincode is instantiated on peer${{PEER}}.${{ORG}} on channel '$CHANNEL_NAME' ===================== "
  echo
""".format(self.orderer.getAnchorPeer())

        function_upgrade_chaincode = """
  set -x
  peer chaincode upgrade -o {0} --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} -v 0.0.2 -c '{{"function":"initLedger","Args":[]}}' -P "AND ('DCMSP.peer','DPMSP.peer')"
  res=$?
  set +x
  cat log.txt
  verifyResult $res "Chaincode upgrade on peer${{PEER}}.${{ORG}} has failed"
  echo "===================== Chaincode is upgraded on peer${{PEER}}.${{ORG}} on channel '$CHANNEL_NAME' ===================== "
  echo
""".format(self.orderer.getAnchorPeer())

        index = 0

        list_org_condition = []
        list_org_condition_next = []
        list_anchor_peer = []

        ca_folder = """
ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/{0}/orderers/{1}/msp/tlscacerts/tlsca.{0}-cert.pem""".format(
            self.orderer.getDomain(),
            self.orderer.getHostname()
        )

        for org in self.getOrganization():
            if isinstance(org, Organization):
                list_anchor_peer.append(org.getAnchorPeer().getHostname())
                ca_folder += """
PEER0_{0}_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{1}/peers/peer0.{1}/tls/ca.crt""".format(org.name, org.getDomain())

                if index == 0:
                    list_org_condition.append("""
  if [ $ORG -eq {} ];then
    ORG="{}" """.format(index, org.getNotDomainName()))

                    list_org_condition_next.append("""
  if [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{5}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.getNotDomainName(),
                        org.getId(),
                        org.getDomain(),
                        org.getAdminEmail(),
                        self.create_utils_template_for_peer(org),
                        org.name
                    )
                    )

                elif index < (len(self.organization.keys()) - 1):
                    list_org_condition.append("""
  elif [ $ORG -eq {} ];then
    ORG="{}" """.format(index, org.getNotDomainName()))

                    list_org_condition_next.append("""
  elif [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{5}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.getNotDomainName(),
                        org.getId(),
                        org.getDomain(),
                        org.getAdminEmail(),
                        self.create_utils_template_for_peer(org),
                        org.name
                    ))
                else:
                    list_org_condition.append("""
  else
    ORG="{}" """.format(org.getNotDomainName()))
                    list_org_condition_next.append("""
  elif [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{5}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.getNotDomainName(),
                        org.getId(),
                        org.getDomain(),
                        org.getAdminEmail(),
                        self.create_utils_template_for_peer(org),
                        org.name
                    ))

            index += 1

        self.__cache_server.set_session("list_anchor_peer", list_anchor_peer)

        return function_orderer_global, \
            "".join(list_org_condition), \
            "".join(list_org_condition_next), \
            function_update_anchor_peer, \
            function_instantiate_chaincode, \
            function_upgrade_chaincode, \
            ca_folder

    def create_utils_file(self):

        function_orderer_global, \
            function_global, \
            function_global_next, \
            function_update_anchor_peer, \
            function_instantiate_chaincode, \
            function_upgrade_chaincode, \
            ca_folder = self.create_utils_template()

        template = """#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
# Modify by Evarist Fangnikoue
#

# This is a collection of bash functions used by different scripts

{7}

# verify the result of the end-to-end test
verifyResult() {{
  if [ $1 -ne 0 ]; then
    echo "!!!!!!!!!!!!!!! "$2" !!!!!!!!!!!!!!!!"
    echo "========= ERROR !!! FAILED to execute End-2-End Scenario ==========="
    echo
    exit 1
  fi
}}

# Set OrdererOrg.Admin globals
setOrdererGlobals() {{

{0}

}}

setGlobals() {{
  PEER=$1
  ORG=$2

if [[ $ORG =~ ^[0-9]+$ ]]; then
    {1}
  fi
fi

{2}
  else

    echo "================== ERROR !!! ORG Unknown '$ORG'=================="
  fi

  if [ "$VERBOSE" == "true" ]; then
    env | grep CORE
  fi
}}

updateAnchorPeers() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG

  {3}
}}

# Sometimes Join takes time hence RETRY at least 5 times
joinChannelWithRetry() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG

  set -x
  peer channel join -b $CHANNEL_NAME.block >&log.txt
  res=$?
  set +x
  cat log.txt
  if [ $res -ne 0 -a $COUNTER -lt $MAX_RETRY ]; then
    COUNTER=$(expr $COUNTER + 1)
    echo "peer${{PEER}}.${{ORG}} failed to join the channel, Retry after $DELAY seconds"
    sleep $DELAY
    joinChannelWithRetry $PEER $ORG
  else
    COUNTER=1
  fi
  verifyResult $res "After $MAX_RETRY attempts, peer${{PEER}}.${{ORG}} has failed to join channel '$CHANNEL_NAME' "
}}

installChaincode() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG
  VERSION=${{3:-0.0.1}}
  set -x
  peer chaincode install -n ${{CHAINCODE_NAME}} -v ${{VERSION}} -l ${{LANGUAGE}} -p ${{CC_SRC_PATH}} >&log.txt
  res=$?
  set +x
  cat log.txt
  verifyResult $res "Chaincode installation on peer${{PEER}}.${{ORG}} has failed"
  echo "===================== Chaincode is installed on peer${{PEER}}.${{ORG}} ===================== "
  echo
}}

instantiateChaincode() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG
  VERSION=${{3:-0.0.1}}

  {4}
}}

upgradeChaincode() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG

{5}
}}

chaincodeQuery() {{
  PEER=$1
  ORG=$2
  setGlobals $PEER $ORG
  EXPECTED_RESULT=$3
  echo "===================== Querying on peer${{PEER}}.${{ORG}} on channel '$CHANNEL_NAME'... ===================== "
  local rc=1
  local starttime=$(date +%s)

  # continue to poll
  # we either get a successful response, or reach TIMEOUT
  while
    test "$(($(date +%s) - starttime))" -lt "$TIMEOUT" -a $rc -ne 0
  do
    sleep $DELAY
    echo "Attempting to Query peer${{PEER}}.${{ORG}} ...$(($(date +%s) - starttime)) secs"
    set -x
    peer chaincode query -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} -c '{{"function":"getSaveEstateByDp","Args":["f363b02c-e1f1-42d4-9078-b4848c45fb42"]}}' >&log.txt
    res=$?
    set +x
    test $res -eq 0 && VALUE=$(cat log.txt)
    test "$VALUE" = "$EXPECTED_RESULT" && let rc=0
    # removed the string "Query Result" from peer chaincode query command
    # result. as a result, have to support both options until the change
    # is merged.
    test $rc -ne 0 && VALUE=$(cat log.txt)
    test "$VALUE" = "$EXPECTED_RESULT" && let rc=0
  done
  echo
  cat log.txt
  if test $rc -eq 0; then
    echo "===================== Query successful on peer${{PEER}}.${{ORG}} on channel '$CHANNEL_NAME' ===================== "
  else
    echo "!!!!!!!!!!!!!!! Query result on peer${{PEER}}.${{ORG}} is INVALID !!!!!!!!!!!!!!!!"
    echo "================== ERROR !!! FAILED to execute End-2-End Scenario =================="
    echo
    exit 1
  fi
}}

# fetchChannelConfig <channel_id> <output_json>
# Writes the current channel config for a given channel to a JSON file
fetchChannelConfig() {{
  CHANNEL=$1
  OUTPUT=$2

  setOrdererGlobals

  echo "Fetching the most recent configuration block for the channel"
  if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
    set -x
    peer channel fetch config config_block.pb -o {6} -c $CHANNEL --cafile $ORDERER_CA
    set +x
  else
    set -x
    peer channel fetch config config_block.pb -o {6} -c $CHANNEL --tls --cafile $ORDERER_CA
    set +x
  fi

  echo "Decoding config block to JSON and isolating config to ${{OUTPUT}}"
  set -x
  configtxlator proto_decode --input config_block.pb --type common.Block | jq .data.data[0].payload.data.config >"${{OUTPUT}}"
  set +x
}}

# signConfigtxAsPeerOrg <org> <configtx.pb>
# Set the peerOrg admin of an org and signing the config update
signConfigtxAsPeerOrg() {{
  PEERORG=$1
  TX=$2
  setGlobals 0 $PEERORG
  set -x
  peer channel signconfigtx -f "${{TX}}"
  set +x
}}

# createConfigUpdate <channel_id> <original_config.json> <modified_config.json> <output.pb>
# Takes an original and modified config, and produces the config update tx
# which transitions between the two
createConfigUpdate() {{
  CHANNEL=$1
  ORIGINAL=$2
  MODIFIED=$3
  OUTPUT=$4

  set -x
  configtxlator proto_encode --input "${{ORIGINAL}}" --type common.Config >original_config.pb
  configtxlator proto_encode --input "${{MODIFIED}}" --type common.Config >modified_config.pb
  configtxlator compute_update --channel_id "${{CHANNEL}}" --original original_config.pb --updated modified_config.pb >config_update.pb
  configtxlator proto_decode --input config_update.pb --type common.ConfigUpdate >config_update.json
  echo '{{"payload":{{"header":{{"channel_header":{{"channel_id":"'$CHANNEL'", "type":2}}}}}},"data":{{"config_update":'$(cat config_update.json)'}}}}' | jq . >config_update_in_envelope.json
  configtxlator proto_encode --input config_update_in_envelope.json --type common.Envelope >"${{OUTPUT}}"
  set +x
}}

# parsePeerConnectionParameters $@
# Helper function that takes the parameters from a chaincode operation
# (e.g. invoke, query, instantiate) and checks for an even number of
# peers and associated org, then sets $PEER_CONN_PARMS and $PEERS
parsePeerConnectionParameters() {{
  # check for uneven number of peer and org parameters
  if [ $(($# % 2)) -ne 0 ]; then
    exit 1
  fi

  PEER_CONN_PARMS=""
  PEERS=""
  while [ "$#" -gt 0 ]; do
    setGlobals $1 $2
    PEER="peer$1.$2"
    PEERS="$PEERS $PEER"
    PEER_CONN_PARMS="$PEER_CONN_PARMS --peerAddresses $CORE_PEER_ADDRESS"
    if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "true" ]; then
      TLSINFO=$(eval echo "--tlsRootCertFiles \\$PEER$1_ORG$2_CA")
      PEER_CONN_PARMS="$PEER_CONN_PARMS $TLSINFO"
    fi
    # shift by two to get the next pair of peer/org parameters
    shift
    shift
  done
  # remove leading space for output
  PEERS="$(echo -e "$PEERS" | sed -e 's/^[[:space:]]*//')"
}}

# chaincodeInvoke <peer> <org> ...
# Accepts as many peer/org pairs as desired and requests endorsement from each
chaincodeInvoke() {{
  parsePeerConnectionParameters $@
  res=$?
  verifyResult $res "Invoke transaction failed on channel '$CHANNEL_NAME' due to uneven number of peer and org parameters "

  # while 'peer chaincode' command can get the orderer endpoint from the
  # peer (if join was successful), let's supply it directly as we know
  # it using the "-o" option
  if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
    set -x
    peer chaincode invoke -o {6} -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} $PEER_CONN_PARMS -c '{{"function":"getSaveEstateByDp","Args":["f363b02c-e1f1-42d4-9078-b4848c45fb42"]}}' >&log.txt
    res=$?
    set +x
  else
    set -x
    peer chaincode invoke -o {6} --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA -C $CHANNEL_NAME -n ${{CHAINCODE_NAME}} $PEER_CONN_PARMS -c '{{"function":"getSaveEstateByDp","Args":["f363b02c-e1f1-42d4-9078-b4848c45fb42"]}}' >&log.txt
    res=$?
    set +x
  fi
  cat log.txt
  verifyResult $res "Invoke execution on $PEERS failed "
  echo "===================== Invoke transaction successful on $PEERS on channel '$CHANNEL_NAME' ===================== "
  echo
}} """.format(
            function_orderer_global,
            function_global,
            function_global_next,
            function_update_anchor_peer,
            function_instantiate_chaincode,
            function_upgrade_chaincode,
            self.orderer.getAnchorPeer(),
            ca_folder)

        NetworkFileHandler.create_script_file("utils.sh", template)

    def getCachedData(self, key):
        return self.__cache_server.get_session(key)

    def create_script_file(self):

        list_org_name = " ".join(
            self.__cache_server.get_session("list_org_not_domain_name"))
        chain_code = self.getInitialChainCode(object)

        org = self.getInitialOrganization()

        install_chain_code = """	# Instantiate chaincode on peer0 of every organization """
        intantiate_chain_code = ""
        querry_chaincode = """	# # Query chaincode"""
        invoke_chaincode = """  # chaincodeInvoke """

        index = 0

        is_chaincode_intantiate = chain_code.instantiate

        for org_obj in self.getCachedData("list_org_obj"):

            install_chain_code += """
	echo "Installing chaincode on peer0.{0}..."
	installChaincode 0  {1} """.format(org_obj.name.lower(), index)

            if is_chaincode_intantiate:
                intantiate_chain_code += """
	echo "Instantiating chaincode on peer0.{0}..."
	instantiateChaincode 0  {1} """.format(org_obj.name.lower(), index)

                querry_chaincode += """
	echo "Querying chaincode on peer0.{1}..."
	chaincodeQuery 0 {0} '{2}'
                """.format(org_obj.name.lower(), index, chain_code.query)

                invoke_chaincode += " 0  {}".format(index)

            index += 1

        chain_code_directory = ""
        chain_code_name = ""

        if self.hasChainCode():
            chain_code_directory = chain_code.directory
            chain_code_name = chain_code.name

        update_anchor_peer_for_each_org = ""

        index = 0
        for org_name in self.getCachedData("list_org"):
            update_anchor_peer_for_each_org += """
echo "Updating anchor peers for {1}..."
updateAnchorPeers 0 {0}
          """.format(index, org_name)
            index += 1

        template = """#!/bin/bash

echo
echo " ____    _____      _      ____    _____ "
echo "/ ___|  |_   _|    / \\    |  _ \\  |_   _|"
echo "\\___ \\    | |     / _ \\   | |_) |   | |  "
echo " ___) |   | |    / ___ \\  |  _ <    | |  "
echo "|____/    |_|   /_/   \\_\\ |_| \\_\\   |_|  "
echo
echo "Build {1} network "
echo
CHANNEL_NAME="$1"
DELAY="$2"
LANGUAGE="$3"
TIMEOUT="$4"
VERBOSE="$5"
NO_CHAINCODE="$6"
: ${{CHANNEL_NAME:="{0}"}}
: ${{DELAY:="3"}}
: ${{LANGUAGE:="node"}}
: ${{TIMEOUT:="10"}}
: ${{VERBOSE:="false"}}
: ${{NO_CHAINCODE:="false"}}
LANGUAGE=`echo "$LANGUAGE" | tr [:upper:] [:lower:]`
COUNTER=1
MAX_RETRY=10
CHAINCODE_DIR="{6}/{4}"
CHAINCODE_NAME="{4}"

CC_SRC_PATH="github.com/chaincode/${{CHAINCODE_DIR}}/go/"

if [ "$LANGUAGE" = "node" ] ||  [ "$LANGUAGE" = "javascript" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${{CHAINCODE_DIR}}/node/"
fi

if [ "$LANGUAGE" = "java" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${{CHAINCODE_DIR}}/java/"
fi

echo "Channel name : "$CHANNEL_NAME

# import utils
. scripts/utils.sh

createChannel() {{
	setGlobals 0 0

	if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
                set -x
		peer channel create -o {2} -c $CHANNEL_NAME -f ./channel-artifacts/channel.tx >&log.txt
		res=$?
                set +x
	else
				set -x
		peer channel create -o {2} -c $CHANNEL_NAME -f ./channel-artifacts/channel.tx --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA >&log.txt
		res=$?
				set +x
	fi
	cat log.txt
	verifyResult $res "Channel creation failed"
	echo "===================== Channel '$CHANNEL_NAME' created ===================== "
	echo
}}

joinChannel () {{
	for org in {3}; do
	    for peer in 0 ; do
		joinChannelWithRetry $peer $org
		echo "===================== peer${{peer}}.${{org}} joined channel '$CHANNEL_NAME' ===================== "
		sleep $DELAY
		echo
	    done
	done
}}

# Create channel
echo "Creating channel..."
createChannel

# Join all the peers to the channel
echo "Having all peers join the channel..."
joinChannel

# Set the anchor peers for each org in the channel
{5}

if [ "${{NO_CHAINCODE}}" != "true" ]; then

	# Install chaincode on peer0 of every organization

{7}


{8}


{9}

	# # Invoke chaincode
  
{10}

fi

if [ $? -ne 0 ]; then
	echo "ERROR !!!! Test failed"
    exit 1
fi
        """.format(
            self.consurtium.getInitialChannel().name.lower(),
            self.admin.organization_name,
            self.orderer.getAnchorPeer(),
            list_org_name,
            chain_code_name,
            update_anchor_peer_for_each_org,
            org.name.lower(),
            install_chain_code,
            intantiate_chain_code,
            querry_chaincode,
            invoke_chaincode
        )

        NetworkFileHandler.create_script_file("script.sh", template)

    def create_bbchain_template(self):

        export_private_key = ""
        function_update_private_key = ""
        anchor_peer = ""

        list_org = self.getCachedData("list_org_obj")

        list_ccp_generate_code = ""

        for org_index in range(len(list_org)):
            org = (list_org[org_index])
            ca_name = "CA"
            peer_port = ""
            peer_name = ""
            for peer_index in range(len(org.list_peer)):
                peer = org.list_peer[peer_index]

                peer_port += " {}".format(peer.port)
                peer_name += " {}".format(peer.getHostname())

            list_ccp_generate_code += """
  bash scripts/ccp-generate.sh json {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}
            """.format(
                org.name,
                peer_port,
                org.getCaCertificate().getCaInternPortNumber(),
                org.getPeerPem(),
                org.getCaPem(),
                org.getId(),
                org.getDomain(),
                "ca.{}".format(org.getDomain()),
                peer_name,
                "ca-{}".format(org.name)
            )

            if org_index > 0:
                ca_name += "%d" % org_index
            export_private_key += """
    export BYFN_{0}_PRIVATE_KEY=$(cd crypto-config/peerOrganizations/{1}/ca && ls *_sk) """.format(ca_name, org.getConfigurationPath())
            function_update_private_key += """
  cd crypto-config/peerOrganizations/{1}/ca/
  PRIV_KEY=$(ls *_sk)
  cd "$CURRENT_DIR"
  sed $OPTS "s/{0}_PRIVATE_KEY/${{PRIV_KEY}}/g" docker-compose-e2e.yaml
            """.format(ca_name, org.getConfigurationPath())

            anchor_peer += """

  echo
  echo "#################################################################"
  echo "#######    Generating anchor peer update for {0}   ##########"
  echo "#################################################################"
  set -x
  configtxgen -profile {1} -outputAnchorPeersUpdate \\
    ./channel-artifacts/{0}anchors.tx -channelID $CHANNEL_NAME -asOrg {0}
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo "Failed to generate anchor peer update for {0}..."
    exit 1
  fi
            """.format(org.getId(), self.channel().name)

        return export_private_key, function_update_private_key, anchor_peer, list_ccp_generate_code

    def create_bbchain_file(self):
        ca_orgname, function_update_private_key, anchor_peer, list_ccp_generate_code = self.create_bbchain_template()
        list_peer = self.getCachedData("list_peer")
        list_anchor_peer = "`` & ``".join(
            self.getCachedData("list_anchor_peer"))
        list_org_name = self.getCachedData("list_org")
        list_org = "`` & ``".join(list_org_name)
        list_org_for_ccp_file = ",".join(list_org_name)
        org = self.getInitialOrganization()

        template = """#!/bin/bash
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
#

# This script will orchestrate a sample end-to-end execution of the Hyperledger
# Fabric network.
#
# The end-to-end verification provisions a sample Fabric network consisting of
# two organizations, each maintaining two peers, and a “solo” ordering service.
#
# This verification makes use of two fundamental tools, which are necessary to
# create a functioning transactional network with digital signature validation
# and access control:
#
# * cryptogen - generates the x509 certificates used to identify and
#   authenticate the various components in the network.
# * configtxgen - generates the requisite configuration artifacts for orderer
#   bootstrap and channel creation.
#
# Each tool consumes a configuration yaml file, within which we specify the topology
# of our network (cryptogen) and the location of our certificates for various
# configuration operations (configtxgen).  Once the tools have been successfully run,
# we are able to launch our network.  More detail on the tools and the structure of
# the network will be provided later in this document.  For now, let's get going...

# prepending $PWD/../bin to PATH to ensure we are picking up the correct binaries
# this may be commented out to resolve installed version of tools if desired

source .env

export PATH=${{PWD}}/bin:${{PWD}}:$PATH
export FABRIC_CFG_PATH=${{PWD}}
export VERBOSE=false
export EXPLORER_DIR=${{PWD}}/../hyperledger-explorer
export RUN_EXPLORER={15}


# Print the usage message
function printHelp() {{
  echo "Usage: "
  echo "  byfn.sh <mode> [-c <channel name>] [-t <timeout>] [-d <delay>] [-f <docker-compose-file>] [-s <dbtype>] [-l <language>] [-o <consensus-type>] [-i <imagetag>] [-a] [-n] [-v]"
  echo "    <mode> - one of 'up', 'down', 'restart', 'generate' or 'upgrade'"
  echo "      - 'up' - bring up the network with docker-compose up"
  echo "      - 'down' - clear the network with docker-compose down"
  echo "      - 'restart' - restart the network"
  echo "      - 'generate' - generate required certificates and genesis block"
  echo "      - 'upgrade'  - upgrade the network from version 1.3.x to 1.4.0"
  echo "    -c <channel name> - channel name to use (defaults to \\"mychannel\\")"
  echo "    -t <timeout> - CLI timeout duration in seconds (defaults to 10)"
  echo "    -d <delay> - delay duration in seconds (defaults to 3)"
  echo "    -f <docker-compose-file> - specify which docker-compose file use (defaults to docker-compose-cli.yaml)"
  echo "    -s <dbtype> - the database backend to use: goleveldb (default) or couchdb"
  echo "    -l <language> - the chaincode language: golang (default) or node"
  echo "    -o <consensus-type> - the consensus-type of the ordering service: solo (default), kafka, or etcdraft"
  echo "    -i <imagetag> - the tag to be used to launch the network (defaults to \\"latest\\")"
  echo "    -a - launch certificate authorities (no certificate authorities are launched by default)"
  echo "    -n - do not deploy chaincode (abstore chaincode is deployed by default)"
  echo "    -v - verbose mode"
  echo "  byfn.sh -h (print this message)"
  echo
  echo "Typically, one would first generate the required certificates and "
  echo "genesis block, then bring up the network. e.g.:"
  echo
  echo "	byfn.sh generate -c mychannel"
  echo "	byfn.sh up -c mychannel -s couchdb"
  echo "        byfn.sh up -c mychannel -s couchdb -i 1.4.0"
  echo "	byfn.sh up -l node"
  echo "	byfn.sh down -c mychannel"
  echo "        byfn.sh upgrade -c mychannel"
  echo
  echo "Taking all defaults:"
  echo "	byfn.sh generate"
  echo "	byfn.sh up"
  echo "	byfn.sh down"
}}

# Ask user for confirmation to proceed
function askProceed() {{


  read -p "Continue? [Y/n] " ans

  case "$ans" in
  y | Y | "")
    echo "proceeding ..."
    ;;
  n | N)
    echo "exiting..."
    exit 1
    ;;
  *)
    echo "invalid response"
    askProceed
    ;;
  esac
}}

# Obtain CONTAINER_IDS and remove them
# TODO Might want to make this optional - could clear other containers
function clearContainers() {{
  CONTAINER_IDS=$(docker ps -a | awk '($2 ~ /dev-peer.*/) {{print $1}}')
  if [ -z "$CONTAINER_IDS" -o "$CONTAINER_IDS" == " " ]; then
    echo "---- No containers available for deletion ----"
  else
    docker rm -f $CONTAINER_IDS
  fi
}}

# Delete any images that were generated as a part of this setup
# specifically the following images are often left behind:
# TODO list generated image naming patterns
function removeUnwantedImages() {{
  DOCKER_IMAGE_IDS=$(docker images | awk '($1 ~ /dev-peer.*/) {{print $3}}')
  if [ -z "$DOCKER_IMAGE_IDS" -o "$DOCKER_IMAGE_IDS" == " " ]; then
    echo "---- No images available for deletion ----"
  else
    docker rmi -f $DOCKER_IMAGE_IDS
  fi
}}

# Versions of fabric known not to work with this release of first-network
BLACKLISTED_VERSIONS="^1\\.0\\. ^1\\.1\\.0-preview ^1\\.1\\.0-alpha"

# Do some basic sanity checking to make sure that the appropriate versions of fabric
# binaries/images are available.  In the future, additional checking for the presence
# of go or other items could be added.
function checkPrereqs() {{
  # Note, we check configtxlator externally because it does not require a config file, and peer in the
  # docker image because of FAB-8551 that makes configtxlator return 'development version' in docker
  LOCAL_VERSION=$(configtxlator version | sed -ne 's/ Version: //p')
  DOCKER_IMAGE_VERSION=$(docker run --rm hyperledger/fabric-tools:$IMAGETAG peer version | sed -ne 's/ Version: //p' | head -1)

  echo "LOCAL_VERSION=$LOCAL_VERSION"
  echo "DOCKER_IMAGE_VERSION=$DOCKER_IMAGE_VERSION"

  if [ "$LOCAL_VERSION" != "$DOCKER_IMAGE_VERSION" ]; then
    echo "=================== WARNING ==================="
    echo "  Local fabric binaries and docker images are  "
    echo "  out of  sync. This may cause problems.       "
    echo "==============================================="
  fi

  for UNSUPPORTED_VERSION in $BLACKLISTED_VERSIONS; do
    echo "$LOCAL_VERSION" | grep -q $UNSUPPORTED_VERSION
    if [ $? -eq 0 ]; then
      echo "ERROR! Local Fabric binary version of $LOCAL_VERSION does not match this newer version of BYFN and is unsupported. Either move to a later version of Fabric or checkout an earlier version of fabric-samples."
      exit 1
    fi

    echo "$DOCKER_IMAGE_VERSION" | grep -q $UNSUPPORTED_VERSION
    if [ $? -eq 0 ]; then
      echo "ERROR! Fabric Docker image version of $DOCKER_IMAGE_VERSION does not match this newer version of BYFN and is unsupported. Either move to a later version of Fabric or checkout an earlier version of fabric-samples."
      exit 1
    fi
  done
}}

# Generate the needed certificates, the genesis block and start the network.
function networkUp() {{
  checkPrereqs
  # generate artifacts if they don't exist
  if [ ! -d "crypto-config" ]; then
    generateCerts
    replacePrivateKey
    generateChannelArtifacts
  fi
  COMPOSE_FILES="-f ${{COMPOSE_FILE}}"
  if [ "${{CERTIFICATE_AUTHORITIES}}" == "true" ]; then
    COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_CA}}"
{0}
  fi
  if [ "${{CONSENSUS_TYPE}}" == "kafka" ]; then
    COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_KAFKA}}"
  elif [ "${{CONSENSUS_TYPE}}" == "etcdraft" ]; then
    COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_RAFT2}}"
  fi
  if [ "${{IF_COUCHDB}}" == "couchdb" ]; then
    COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_COUCH}}"
  fi
  IMAGE_TAG=$IMAGETAG docker-compose ${{COMPOSE_FILES}} up -d $(docker-compose ${{COMPOSE_FILES}} config --services | grep -v -e "explorer") 2>&1
  docker ps -a
  if [ $? -ne 0 ]; then
    echo "ERROR !!!! Unable to start network"
    exit 1
  fi

  if [ "$CONSENSUS_TYPE" == "kafka" ]; then
    sleep 1
    echo "Sleeping 10s to allow $CONSENSUS_TYPE cluster to complete booting"
    sleep 9
  fi

  if [ "$CONSENSUS_TYPE" == "etcdraft" ]; then
    sleep 1
    echo "Sleeping 15s to allow $CONSENSUS_TYPE cluster to complete booting"
    sleep 14
  fi

  # now run the end to end script
  docker exec cli scripts/script.sh $CHANNEL_NAME $CLI_DELAY $LANGUAGE $CLI_TIMEOUT $VERBOSE $NO_CHAINCODE


 if [ $?  -eq 0 ];then

    # run Hyperledger explorer ui

    if [ "$RUN_EXPLORER" != "false" ];then
      createExplorer
    fi

    exit 0
  else
      # networkDown
      exit 1
  fi
}}


createExplorer()
{{


sudo docker-compose -f docker-compose-cli.yaml up --build -d explorer 2>&1


if [ $? -eq 0 ]; then

  which xdg-open 1>/dev/null

  if [ $? -eq 0 ];then

        current_user=`whoami`

        if [ "$current_user"="root" ];then
           current_user=$USER
        fi

        explorer_port=`docker ps --filter "name=explorer" --format "{{{{.Ports}}}}" | awk -F/ '{{print $1}}'`

        if [ "$explorer_port"!="" ];then

            echo ""

            echo "Opening Hyperledger Fabric Explorer on port ${{EXPLORER_PORT}}"

            ./scripts/wait-for localhost:$EXPLORER_PORT -t 30

            explorer_port=$EXPLORER_PORT
            # explorer_port=`docker ps --filter "name=explorer" --format "{{{{.Ports}}}}" | awk -F/ '{{print $1}}'`
            sudo -H -u $current_user bash -c "python -mwebbrowser http://localhost:$explorer_port" 2> /dev/null

        fi
  fi

    exit 0

fi

}}

# Upgrade the network components which are at version 1.3.x to 1.4.x
# Stop the orderer and peers, backup the ledger for orderer and peers, cleanup chaincode containers and images
# and relaunch the orderer and peers with latest tag
function upgradeNetwork() {{
  if [[ "$IMAGETAG" == *"1.4"* ]] || [[ $IMAGETAG == "latest" ]]; then
    docker inspect -f '{{{{.Config.Volumes}}}}' {1} | grep -q '/var/hyperledger/production/orderer'
    if [ $? -ne 0 ]; then
      echo "ERROR !!!! This network does not appear to start with fabric-samples >= v1.3.x?"
      exit 1
    fi

    LEDGERS_BACKUP=./ledgers-backup

    # create ledger-backup directory
    mkdir -p $LEDGERS_BACKUP

    export IMAGE_TAG=$IMAGETAG
    COMPOSE_FILES="-f ${{COMPOSE_FILE}}"
    if [ "${{CERTIFICATE_AUTHORITIES}}" == "true" ]; then
      COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_CA}}"
{0}
    fi
    if [ "${{CONSENSUS_TYPE}}" == "kafka" ]; then
      COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_KAFKA}}"
    elif [ "${{CONSENSUS_TYPE}}" == "etcdraft" ]; then
      COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_RAFT2}}"
    fi
    if [ "${{IF_COUCHDB}}" == "couchdb" ]; then
      COMPOSE_FILES="${{COMPOSE_FILES}} -f ${{COMPOSE_FILE_COUCH}}"
    fi

    # removing the cli container
    docker-compose $COMPOSE_FILES stop cli
    docker-compose $COMPOSE_FILES up -d --no-deps cli

    echo "Upgrading orderer"
    docker-compose $COMPOSE_FILES stop {1}
    docker cp -a {1}:/var/hyperledger/production/orderer $LEDGERS_BACKUP/{1}
    docker-compose $COMPOSE_FILES up -d --no-deps {1}

    for PEER in {2}; do
      echo "Upgrading peer $PEER"

      # Stop the peer and backup its ledger
      docker-compose $COMPOSE_FILES stop $PEER
      docker cp -a $PEER:/var/hyperledger/production $LEDGERS_BACKUP/$PEER/

      # Remove any old containers and images for this peer
      CC_CONTAINERS=$(docker ps | grep dev-$PEER | awk '{{print $1}}')
      if [ -n "$CC_CONTAINERS" ]; then
        docker rm -f $CC_CONTAINERS
      fi
      CC_IMAGES=$(docker images | grep dev-$PEER | awk '{{print $1}}')
      if [ -n "$CC_IMAGES" ]; then
        docker rmi -f $CC_IMAGES
      fi

      # Start the peer again
      docker-compose $COMPOSE_FILES up -d --no-deps $PEER
    done

    docker exec cli sh -c "SYS_CHANNEL=$CH_NAME && scripts/upgrade_to_v14.sh $CHANNEL_NAME $CLI_DELAY $LANGUAGE $CLI_TIMEOUT $VERBOSE"
    if [ $? -ne 0 ]; then
      echo "ERROR !!!! Test failed"
      exit 1
    fi
  else
    echo "ERROR !!!! Pass the v1.4.x image tag"
  fi
}}

# Tear down running network
function networkDown() {{
  # stop org3 containers also in addition to dc and dp, in case we were running sample to add org3
  # stop kafka and zookeeper containers in case we're running with kafka consensus-type
  docker-compose -f $COMPOSE_FILE -f $COMPOSE_FILE_COUCH -f $COMPOSE_FILE_KAFKA -f $COMPOSE_FILE_RAFT2 -f $COMPOSE_FILE_CA down --volumes --remove-orphans

  # Don't remove the generated artifacts -- note, the ledgers are always removed
  if [ "$MODE" != "restart" ]; then
    # Bring down the network, deleting the volumes
    # Delete any ledger backups
    docker run -v $PWD:/tmp/first-network --rm hyperledger/fabric-tools:$IMAGETAG rm -Rf /tmp/first-network/ledgers-backup
    # Cleanup the chaincode containers
    clearContainers
    # Cleanup images
    removeUnwantedImages
    # remove orderer block and other channel configuration transactions and certs
    rm -rf channel-artifacts/*.block channel-artifacts/*.tx crypto-config
    # remove the docker-compose yaml file that was customized to the example
    rm -f docker-compose-e2e.yaml

    rm -rf connecxion-profile/*

    removeExplorerConfiguration

    removeWalletConfiguration

    docker volume prune -f 1>/dev/null

  fi
}}

function networkLog()
{{
  docker-compose -f $COMPOSE_FILE -f $COMPOSE_FILE_COUCH -f $COMPOSE_FILE_KAFKA -f $COMPOSE_FILE_RAFT2 -f $COMPOSE_FILE_CA logs -f --tail=10
}}

function networkStatus()
{{
 docker-compose -f $COMPOSE_FILE -f $COMPOSE_FILE_COUCH -f $COMPOSE_FILE_KAFKA -f $COMPOSE_FILE_RAFT2 -f $COMPOSE_FILE_CA ps
}}

function networkStart()
{{
  docker-compose -f $COMPOSE_FILE -f $COMPOSE_FILE_COUCH -f $COMPOSE_FILE_KAFKA -f $COMPOSE_FILE_RAFT2 -f $COMPOSE_FILE_CA start
}}

# Remove the explorer configuration
function removeExplorerConfiguration()
{{

  if [ -L "$EXPLORER_DIR/app/config/crypto-config" ];then
    # remove the certificate directory link
    unlink $EXPLORER_DIR/app/config/crypto-config

  fi

  # remove the network configuration file
  rm -rf $EXPLORER_DIR/app/config/connection-profile/{7}.json

}}

function removeWalletConfiguration()
{{

  rm -rf wallet/*

}}

# Using docker-compose-e2e-template.yaml, replace constants with private key file names
# generated by the cryptogen tool and output a docker-compose.yaml specific to this
# configuration
function replacePrivateKey() {{
  # sed on MacOSX does not support -i flag with a null extension. We will use
  # 't' for our back-up's extension and delete it at the end of the function
  ARCH=$(uname -s | grep Darwin)
  if [ "$ARCH" == "Darwin" ]; then
    OPTS="-it"
  else
    OPTS="-i"
  fi

  # Copy the template to the file that will be modified to add the private key
  cp docker-compose-e2e-template.yaml docker-compose-e2e.yaml

  # The next steps will replace the template's contents with the
  # actual values of the private key file names for the two CAs.
  CURRENT_DIR=$PWD
{3}
  # If MacOSX, remove the temporary backup of the docker-compose file
  if [ "$ARCH" == "Darwin" ]; then
    rm docker-compose-e2e.yamlt
  fi
}}

# We will use the cryptogen tool to generate the cryptographic material (x509 certs)
# for our various network entities.  The certificates are based on a standard PKI
# implementation where validation is achieved by reaching a common trust anchor.
#
# Cryptogen consumes a file - ``crypto-config.yaml`` - that contains the network
# topology and allows us to generate a library of certificates for both the
# Organizations and the components that belong to those Organizations.  Each
# Organization is provisioned a unique root certificate (``ca-cert``), that binds
# specific components (peers and orderers) to that Org.  Transactions and communications
# within Fabric are signed by an entity's private key (``keystore``), and then verified
# by means of a public key (``signcerts``).  You will notice a "count" variable within
# this file.  We use this to specify the number of peers per Organization; in our
# case it's two peers per Org.  The rest of this template is extremely
# self-explanatory.
#
# After we run the tool, the certs will be parked in a folder titled ``crypto-config``.

# Generates Org certs using cryptogen tool
function generateCerts() {{
  which cryptogen 1>/dev/null
  if [ "$?" -ne 0 ]; then
    echo "cryptogen tool not found. exiting"
    exit 1
  fi
  echo
  echo "##########################################################"
  echo "##### Generate certificates using cryptogen tool #########"
  echo "##########################################################"

  if [ -d "crypto-config" ]; then
    rm -Rf crypto-config
  fi
  set -x
  cryptogen generate --config=./crypto-config.yaml
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo "Failed to generate certificates..."
    exit 1
  fi
  echo
  echo "Generate CCP files for {10}"
{14}

}}

generateExplorerCertificate()
{{
     # Check whether the config directory exists
    if [ ! -d "${{EXPLORER_DIR}}/app/config/crypto-config" ];then
        ln -s ${{FABRIC_CFG_PATH}}/crypto-config ${{EXPLORER_DIR}}/app/config/crypto-config
    fi

    cwd=$PWD

    cp ${{EXPLORER_DIR}}/app/config/connection-profile/template.json ${{EXPLORER_DIR}}/app/config/connection-profile/{7}.json

    cd crypto-config/peerOrganizations/{11}/users/{6}/msp/keystore/

    admin_key=$(ls *_sk)

    cd $cwd

    sed -i "s/ADMIN_KEY/${{admin_key}}/g" ${{EXPLORER_DIR}}/app/config/connection-profile/{7}.json
}}

# The `configtxgen tool is used to create four artifacts: orderer **bootstrap
# block**, fabric **channel configuration transaction**, and two **anchor
# peer transactions** - one for each Peer Org.
#
# The orderer block is the genesis block for the ordering service, and the
# channel transaction file is broadcast to the orderer at channel creation
# time.  The anchor peer transactions, as the name might suggest, specify each
# Org's anchor peer on this channel.
#
# Configtxgen consumes a file - ``configtx.yaml`` - that contains the definitions
# for the sample network. There are three members - one Orderer Org (``OrdererOrg``)
# and two Peer Orgs (``{9}``) each managing and maintaining two peer nodes.
# This file also specifies a consortium - ``SampleConsortium`` - consisting of our
# two Peer Orgs.  Pay specific attention to the "Profiles" section at the top of
# this file.  You will notice that we have two unique headers. One for the orderer genesis
# block - ``TwoOrgsOrdererGenesis`` - and one for our channel - ``TwoOrgsChannel``.
# These headers are important, as we will pass them in as arguments when we create
# our artifacts.  This file also contains two additional specifications that are worth
# noting.  Firstly, we specify the anchor peers for each Peer Org
# (``{8}``).  Secondly, we point to
# the location of the MSP directory for each member, in turn allowing us to store the
# root certificates for each Org in the orderer genesis block.  This is a critical
# concept. Now any network entity communicating with the ordering service can have
# its digital signature verified.
#
# This function will generate the crypto material and our four configuration
# artifacts, and subsequently output these files into the ``channel-artifacts``
# folder.
#
# If you receive the following warning, it can be safely ignored:
#
# [bccsp] GetDefault -> WARN 001 Before using BCCSP, please call InitFactories(). Falling back to bootBCCSP.
#
# You can ignore the logs regarding intermediate certs, we are not using them in
# this crypto implementation.

# Generate orderer genesis block, channel configuration transaction and
# anchor peer update transactions
function generateChannelArtifacts() {{
  which configtxgen 1>/dev/null
  if [ "$?" -ne 0 ]; then
    echo "configtxgen tool not found. exiting"
    exit 1
  fi

  echo "##########################################################"
  echo "#########  Generating Orderer Genesis block ##############"
  echo "##########################################################"
  # Note: For some unknown reason (at least for now) the block file can't be
  # named orderer.genesis.block or the orderer will fail to launch!
  echo "CONSENSUS_TYPE="$CONSENSUS_TYPE
  set -x
  if [ "$CONSENSUS_TYPE" == "solo" ]; then
    configtxgen -profile TwoOrgsOrdererGenesis -channelID $SYS_CHANNEL -outputBlock ./channel-artifacts/genesis.block
  elif [ "$CONSENSUS_TYPE" == "kafka" ]; then
    configtxgen -profile SampleDevModeKafka -channelID $SYS_CHANNEL -outputBlock ./channel-artifacts/genesis.block
  elif [ "$CONSENSUS_TYPE" == "etcdraft" ]; then
    configtxgen -profile SampleMultiNodeEtcdRaft -channelID $SYS_CHANNEL -outputBlock ./channel-artifacts/genesis.block
  else
    set +x
    echo "unrecognized CONSESUS_TYPE='$CONSENSUS_TYPE'. exiting"
    exit 1
  fi
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo "Failed to generate orderer genesis block..."
    exit 1
  fi
  echo
  echo "#################################################################"
  echo "### Generating channel configuration transaction 'channel.tx' ###"
  echo "#################################################################"
  set -x
  configtxgen -profile {4} -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID $CHANNEL_NAME
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo "Failed to generate channel configuration transaction..."
    exit 1
  fi


  {5}
  echo

  generateExplorerCertificate
}}

# Obtain the OS and Architecture string that will be used to select the correct
# native binaries for your platform, e.g., darwin-amd64 or linux-amd64
OS_ARCH=$(echo "$(uname -s | tr '[:upper:]' '[:lower:]' | sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')" | awk '{{print tolower($0)}}')
# timeout duration - the duration the CLI should wait for a response from
# another container before giving up
CLI_TIMEOUT=10
# default for delay between commands
CLI_DELAY=3
# system channel name defaults to "byfn-sys-channel"
SYS_CHANNEL="byfn-sys-channel"
# channel name defaults to "mychannel"
CHANNEL_NAME={4}
# use this as the default docker-compose yaml definition
COMPOSE_FILE=docker-compose-cli.yaml
#
COMPOSE_FILE_COUCH=docker-compose-couch.yaml

# kafka and zookeeper compose file
COMPOSE_FILE_KAFKA=docker-compose-kafka.yaml
# two additional etcd/raft orderers
COMPOSE_FILE_RAFT2=docker-compose-etcdraft2.yaml
# certificate authorities compose file
COMPOSE_FILE_CA=docker-compose-ca.yaml
#
# use golang as the default language for chaincode
LANGUAGE=node
# default image tag
IMAGETAG="{12}"
# default consensus type
CONSENSUS_TYPE="{13}"

# Parse commandline args
if [ "$1" = "-m" ]; then # supports old usage, muscle memory is powerful!
  shift
fi
MODE=$1
shift
# Determine whether starting, stopping, restarting, generating or upgrading
if [ "$MODE" == "up" ]; then
  EXPMODE="Starting"
elif [ "$MODE" == "down" ]; then
  EXPMODE="Stopping"
elif [ "$MODE" == "restart" ]; then
  EXPMODE="Restarting"
elif [ "$MODE" == "generate" ]; then
  EXPMODE="Generating certs and genesis block"
elif [ "$MODE" == "upgrade" ]; then
  EXPMODE="Upgrading the network"
elif [ "$MODE" == "explorer" ]; then
  EXPMODE="Building explorer ui"
elif [ "$MODE" == "log" ];then
  EXMODE="Displaying the running container"
elif [ "$MODE" == "status" ];then
  EXMODE="Displaying the status of  container running on the network"
elif [ "$MODE" == "start" ];then
  EXMODE="Displaying the running container"

else
  printHelp
  exit 1
fi

while getopts "h?c:p:t:d:f:s:l:i:o:y:anv" opt; do
  case "$opt" in
  h | \\?)
    printHelp
    exit 0
    ;;
  c)
    CHANNEL_NAME=$OPTARG
    ;;

  p)
    EXPLORER_PORT=$OPTARG
    ;;
  t)
    CLI_TIMEOUT=$OPTARG
    ;;
  d)
    CLI_DELAY=$OPTARG
    ;;
  f)
    COMPOSE_FILE=$OPTARG
    ;;
  s)
    IF_COUCHDB=$OPTARG
    ;;
  l)
    LANGUAGE=$OPTARG
    ;;
  i)
    IMAGETAG=$(go env GOARCH)"-"$OPTARG
    ;;
  o)
    CONSENSUS_TYPE=$OPTARG
    ;;
  a)
    CERTIFICATE_AUTHORITIES=true
    ;;
  n)
    NO_CHAINCODE=true
    ;;
  v)
    VERBOSE=true
    ;;
  esac
done


# Announce what was requested

if [ "${{IF_COUCHDB}}" == "couchdb" ]; then
  echo
  echo "${{EXPMODE}} for channel '${{CHANNEL_NAME}}' with CLI timeout of '${{CLI_TIMEOUT}}' seconds and CLI delay of '${{CLI_DELAY}}' seconds and using database '${{IF_COUCHDB}}'"
else
  echo "${{EXPMODE}} for channel '${{CHANNEL_NAME}}' with CLI timeout of '${{CLI_TIMEOUT}}' seconds and CLI delay of '${{CLI_DELAY}}' seconds"
fi
# ask for confirmation to proceed
# askProceed

# Create the network using docker compose
if [ "${{MODE}}" == "up" ]; then
  networkUp
elif [ "${{MODE}}" == "down" ]; then ## Clear the network
  networkDown
elif [ "${{MODE}}" == "generate" ]; then ## Generate Artifacts
  generateCerts
  replacePrivateKey
  generateChannelArtifacts
elif [ "${{MODE}}" == "restart" ]; then ## Restart the network
  networkDown
  networkUp
# Upgrade the network from version 1.2.x to 1.3.x
elif [ "${{MODE}}" == "upgrade" ]; then
  upgradeNetwork
elif [ "${{MODE}}" == "explorer" ]; then
    createExplorer
elif [ "$MODE" == "log" ];then
    networkLog
elif [ "$MODE" == "start" ];then
  networkStart
elif [ "$MODE" == "status" ];then
  networkStatus
else
  printHelp
  exit 1
fi
      """.format(
            ca_orgname,
            self.orderer.getHostname(),
            " ".join(list_peer),
            function_update_private_key,
            self.channel().name,
            anchor_peer,
            self.getAdminEmail(),
            self.admin.organization_name.lower(),
            list_anchor_peer,
            list_org,
            list_org_for_ccp_file,
            org.getDomain(),
            self.getCurrentVersion(),
            self.orderer.type,
            list_ccp_generate_code,
            str(self.hy_composer.install).lower()
        )

        NetworkFileHandler.create_fabric_file("bbchain.sh", template)

    def create_peer_base_template(self):
        template = ""

        template += """
  {0}:
    container_name: {0}
    extends:
      file: peer-base.yaml
      service: orderer-base
    volumes:
        - ../channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block
        - ../crypto-config/ordererOrganizations/{3}/orderers/{0}/msp:/var/hyperledger/orderer/msp
        - ../crypto-config/ordererOrganizations/{3}/orderers/{0}/tls/:/var/hyperledger/orderer/tls
        - {0}:/var/hyperledger/production/orderer
        - /etc/localtime:/etc/localtime:ro
        - /etc/timezone:/etc/timezone:ro
    ports:
      - {1}:{2}
            """.format(
            self.orderer.getHostname(),
            self.orderer.getHostport(),
            self.orderer.server.intern_port,
            self.orderer.getDomain()
        )

        for peer in self.getCachedData("list_peer_obj"):
            # peer_gossip_address = self.getOrgByDomain(
            #     peer.domain).getGossipPeer().getinternal_address()
            org = self.getOrgByDomain(
                peer.domain)
            peer_gossip_address = org.getGossipPeerBootstrapByPeerId(
                peer.peer_id).getinternal_address()

            mspid = org.getId()

            template += """
  {0}:
    container_name: {0}
    extends:
      file: peer-base.yaml
      service: peer-base
    environment:
      - CORE_PEER_ID={0}
      - CORE_PEER_ADDRESS={0}:{2}
      - CORE_PEER_LISTENADDRESS=0.0.0.0:{2}
      - CORE_PEER_CHAINCODEADDRESS={4}
      - CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:{5}
      - CORE_PEER_GOSSIP_BOOTSTRAP={7}
      - CORE_PEER_GOSSIP_EXTERNALENDPOINT={1}
      - CORE_PEER_LOCALMSPID={8}
    volumes:
        - /var/run/:/host/var/run/
        - ../crypto-config/peerOrganizations/{6}/peers/{0}/msp:/etc/hyperledger/fabric/msp
        - ../crypto-config/peerOrganizations/{6}/peers/{0}/tls:/etc/hyperledger/fabric/tls
        - {0}:/var/hyperledger/production
        - /etc/localtime:/etc/localtime:ro
        - /etc/timezone:/etc/timezone:ro

    ports:
      - {3}:{2}
                """.format(
                peer.getHostname(),
                peer.getinternal_address(),
                peer.intern_port,
                peer.port,
                peer.getChainCodeAddress(),
                peer.getChainCodeInternPort(),
                peer.domain,
                peer_gossip_address,
                mspid
            )

        return template

    def create_peer_base_file(self):
        template_data = self.create_peer_base_template()
        template = """
# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

version: '2'

services:

{}

      """.format(template_data)

        NetworkFileHandler.create_base_file(
            "docker-compose-base.yaml", template)

    def create_explorer_profile_file(self):

        org = self.getInitialOrganization()

        list_orderer = []

        for orderer in self.orderer.getAllOrderer():
            list_orderer.append("""
		"{0}":{{
			"url": "grpc://{1}"
		}}
          """.format(orderer.host, orderer.getinternal_address()))

        peer_template = []
        peer_name_template = []

        for peer in org.list_peer:

            peer_name_template.append("""
"{}": {{}}
            """.format(peer.getHostname()))

            peer_template.append("""
		"{0}": {{
            "url": "grpcs://{1}",
			"tlsCACerts": {{
				"path": "/tmp/crypto/peerOrganizations/{2}/peers/{0}/tls/ca.crt"
			}},
			"requests": "grpcs://{1}",
			"grpcOptions": {{
				"ssl-target-name-override": "{0}"
			}}
		}}
        """.format(
                peer.getHostname(),
                peer.getinternal_address(),
                org.getDomain()
            ))

        template = """
{{

	"version": "1.0.0",
	"client": {{
		"tlsEnable": true,
		"adminUser": "{6}",
		"adminPassword": "{7}",
		"enableAuthentication": false,
		"organization": "{3}",
		"connection": {{
			"timeout": {{
				"peer": {{
					"endorser": "300"
				}},
				"orderer": "300"
			}}
		}}
	}},
	"channels": {{
		"{2}": {{
			"orderer":[
				"{1}"
			],
			"peers": {{
				{9}
			}},
			"connection": {{
				"timeout": {{
					"peer": {{
						"endorser": "6000",
						"eventHub": "6000",
						"eventReg": "6000"
					}}
				}}
			}}
		}}
	}},
	"orderers":{{
		{10}
	}},
	"organizations": {{
		"{3}": {{
			"mspid": "{4}",
			"fullpath": true,
			"adminPrivateKey": {{
				"path": "/tmp/crypto/peerOrganizations/{5}/users/{0}/msp/keystore/ADMIN_KEY"
			}},
			"signedCert": {{
				"path": "/tmp/crypto/peerOrganizations/{5}/users/{0}/msp/signcerts/{0}-cert.pem"
			}}
		}}
	}},
	"peers": {{
		{8}
	}}
}}
      """.format(
            org.getAdminEmail(),
            self.orderer.getHostname(),
            self.channel().name,
            org.name,
            org.getId(),
            org.getDomain(),
            self.admin.login_username,
            self.admin.login_password,
            ",".join(peer_template),
            ",".join(peer_name_template),
            ",".join(list_orderer)
        )

        NetworkFileHandler.create_explorer_file(
            "app/config/connection-profile/template.json", template)

    def create_explorer_config_file(self):
        template = """
{{
	"network-configs": {{
	"{0}": {{
		"name": "{0}",
		"profile": "./connection-profile/{0}.json"
	}}
}},

"license": "Apache-2.0"
}}
      """.format(self.admin.organization_name.lower())

        NetworkFileHandler.create_explorer_file("config/config.json", template)

    def create_network_script_file(self):
        template = """#!/bin/bash

BLACKCREEK_BLOCKCHAIN_DIR=$PWD

FABRIC_DIR=$PWD/hyperledger-fabric/

EXPLORER_DIR=$PWD/hyperledger-explorer/

COMMAND=""

EXPLORER_PORT="{0}"

BLOCKCHAIN_GATEWAY_HOST='localhost:8088'

CREATE_WALLET=""

CREATE_CONNEXION_PROFILE=""

USER_ANSWER=""

source $FABRIC_DIR/.env

# #import blackcreek block chain script
# . hyperledger-fabric/bbchain.sh

help()
{{

  echo "Usage: "
  echo "  ./network [<mode>] [-c <connexion profile>] [-w <wallet>] [-a <connexion profile and wallet>] [-p <explorer port>] [-y <yes>]"
  echo "    <mode> - one of 'up', 'down', 'restart', 'gen-cw', 'start', 'log' or 'status' "
  echo "      - 'up' - bring up the network with docker-compose up"
  echo "      - 'down' - clear the network with docker-compose down"
  echo "      - 'restart' - restart the network"
  echo "      - 'start' - start the network"
  echo "      - 'log' - view the network log in real time"
  echo "      - 'status' - list all the containers status either up or down"
  echo "      - 'gen-cw' - generate connexion profile and wallet"
  echo "    -c <connexion profile> - generate connexion profile"
  echo "    -w <wallet> - generate wallet for all the organizations"
  echo "    -a <all> - generate connexion profile and wallet. This option need to be run with up or restart mode"
  echo "    -p <explorer port> - specify the explorer port to use."
  echo "    -y <yes> Do not ask any question, just run the script."
  echo
  echo "    Example: "
  echo "        - 'restart' - Will destroy all the previous network configurations and generate new connexion profile with new Org wallet."
  echo "            $> ./network restart -a -y"
  echo
  echo "        - 'help' - Getting help or print this help message."
  echo "            $> ./network -h "
  echo

}}

prerequisite()
{{
    which docker 1>/dev/null

    if [ $? -ne 0 ];then

        echo "No docker installation found."
        read -p "Do you want to install it?. [Y\\n]" ans

        case $ans in
            y | Y | "")

                sudo apt update -y && sudo apt-get install -y docker.io && \\
                sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \\
                sudo chmod +x /usr/local/bin/docker-compose
            ;;
            n | N)

                exit 1
            ;;

        esac

    fi

    if [ ! -d "${{FABRIC_DIR}}/channel-artifacts/" ];then
            mkdir -p ${{FABRIC_DIR}}/channel-artifacts
    fi

}}

change_explorer_port()
{{

    check_port

    cp ${{EXPLORER_DIR}}/template/docker-compose-explorer.yml ${{EXPLORER_DIR}}/docker-compose-explorer.yml

    sed -i "s/EXPLORER_PORT/${{EXPLORER_PORT}}/g" ${{EXPLORER_DIR}}/docker-compose-explorer.yml

    export EXPLORER_PORT=$EXPLORER_PORT

}}

networkUp(){{

        prerequisite
        change_explorer_port
        export NETADMIN=$PWD
        cd $FABRIC_DIR
        sudo bash bbchain.sh up -p $EXPLORER_PORT -c {2} -s couchdb -o {1} -a

        sleep 100
        # Generate connecxion profile
        generatingConnecxionProfile


}}

networkDown(){{

    ans=$USER_ANSWER

    if [ "$USER_ANSWER" != "y" ];then

        read -p "Are you sure , you want to destroy the network configuration. [Y\\n] : " ans

    fi

    case $ans in
        y | Y )

            cd $FABRIC_DIR
            sudo ./bbchain.sh down
        ;;

    esac

}}

# Check if the requested explorer port is already in use
check_port()
{{

    sudo lsof -i:$EXPLORER_PORT 1>/dev/null

    if [ $? -eq 0 ];then
        echo "The requested port '$EXPLORER_PORT' for Hyperldger Explorer is already in use."
        exit 1
    fi

}}


generatingConnecxionProfile(){{

    if [ "$PWD"!="$FABRIC_DIR" ];then
        cd $FABRIC_DIR
    fi

  which python3 1>/dev/null

  if [ $? -eq 0 ];then

  # check if the user request to create a connexion profile
  if [ "$CREATE_CONNEXION_PROFILE" = "c" ] || [ "$CREATE_CONNEXION_PROFILE" = "all" ];then

      echo ""
      echo "################# Generating organizations connecxion profile #####################"
      echo ""

      ./scripts/bbcmanager -c

    fi


if [ "$CREATE_WALLET" = "w" ] || [ "$CREATE_WALLET" = "all" ];then

        # Check whether the blockchain gateway server is on
        ./scripts/wait-for $BLOCKCHAIN_GATEWAY_HOST

        if [ $? -eq 0 ];then
            echo ""
            echo "################# Creating network organization wallets #####################"
            echo ""

            sleep 14

            ./scripts/bbcmanager -w

        else

            echo "Cannot connected to the server '$BLOCKCHAIN_GATEWAY_HOST'"

            exit 1

        fi

        if [ $? -eq 0 ];then

	   sleep 60

            sudo docker restart blockchain_network_service > /dev/null 2>&1

        fi
fi

        echo
        echo "========= All GOOD, BCN execution completed =========== "
        echo

        echo
        echo " _____   _   _   ____   "
        echo "| ____| | \\ | | |  _ \\  "
        echo "|  _|   |  \\| | | | | | "
        echo "| |___  | |\\  | | |_| | "
        echo "|_____| |_| \\_| |____/  "
        echo


  fi
}}

COMMAND=$1

if [ $# -gt 1 ];then

shift

fi

while getopts "h?p:nwacy" opt; do

  case "$opt" in
  h | \\?)
    help
    exit 0
    ;;
  p)
    EXPLORER_PORT=$OPTARG
    ;;
  w)
    CREATE_WALLET="w"
    if [ $# -lt 2 ];then
        COMMAND="gen-cw"
    fi
   ;;
  c)
    CREATE_CONNEXION_PROFILE="c"
    if [ $# -lt 2 ];then
        COMMAND="gen-cw"
    fi
   ;;
   a)
        CREATE_WALLET="all"
        CREATE_CONNEXION_PROFILE="all"
   ;;
   y)
        USER_ANSWER="y"
   ;;
  esac
done


main(){{

    case $COMMAND in

        up)
            networkUp
        ;;

        down)

            networkDown

        ;;

        log)
            cd $FABRIC_DIR
            sudo ./bbchain.sh log
        ;;
        status)
            cd $FABRIC_DIR
            sudo ./bbchain.sh status
        ;;
        start)
            cd $FABRIC_DIR
            sudo ./bbchain.sh $COMMAND
        ;;

        restart)

            networkDown
            networkUp

        ;;

        gen-cw)
            # Generate connecxion profile
            generatingConnecxionProfile
        ;;

        *)
            help
        ;;


    esac
}}

main
      """.format(
            self.hy_composer.port,
            self.orderer.type,
            self.channel().name.lower()
        )

        NetworkFileHandler.create_file("network.sh", template)

    def create_wait_for_script(self):

        template = """
#!/bin/sh

# Obtained on 07-Oct-2018 from https://github.com/eficode/wait-for

TIMEOUT=15
QUIET=0

echoerr() {
  if [ "$QUIET" -ne 1 ]; then printf "%s\n" "$*" 1>&2; fi
}

usage() {
  exitcode="$1"
  cat << USAGE >&2
Usage:
  $cmdname host:port [-t timeout] [-- command args]
  -q | --quiet                        Do not output any status messages
  -t TIMEOUT | --timeout=timeout      Timeout in seconds, zero for no timeout
  -- COMMAND ARGS                     Execute command with args after the test finishes
USAGE
  exit "$exitcode"
}

wait_for() {
  for i in `seq $TIMEOUT` ; do
    nc -z "$HOST" "$PORT" > /dev/null 2>&1
    
    result=$?
    if [ $result -eq 0 ] ; then
      if [ $# -gt 0 ] ; then
        exec "$@"
      fi
      exit 0
    fi
    sleep 1
  done
  echo "Operation timed out" >&2
  exit 1
}

while [ $# -gt 0 ]
do
  case "$1" in
    *:* )
    HOST=$(printf "%s\n" "$1"| cut -d : -f 1)
    PORT=$(printf "%s\n" "$1"| cut -d : -f 2)
    shift 1
    ;;
    -q | --quiet)
    QUIET=1
    shift 1
    ;;
    -t)
    TIMEOUT="$2"
    if [ "$TIMEOUT" = "" ]; then break; fi
    shift 2
    ;;
    --timeout=*)
    TIMEOUT="${1#*=}"
    shift 1
    ;;
    --)
    shift
    break
    ;;
    --help)
    usage 0
    ;;
    *)
    echoerr "Unknown argument: $1"
    usage 1
    ;;
  esac
done

if [ "$HOST" = "" -o "$PORT" = "" ]; then
  echoerr "Error: you need to provide a host and port to test."
  usage 2
fi

wait_for "$@"
      """

        NetworkFileHandler.create_script_file("wait-for", template)

    def create_executable_file(self):
        template = """

#!/bin/bash

executable_file=$PWD/$0

cd $PWD/config

FABRIC_PATH=$PWD/hyperledger-fabric/ ./network.sh up -c -y

rm -rf $executable_file
      
      """
        NetworkFileHandler.create_file(
            "exec.sh", template, use_network_path=False)

    def generate(self):

        try:
            list_org_name = []
            list_org_obj = []
            list_org_not_domain_name = []
            for org in self.getOrganization():
                if isinstance(org, Organization):
                    list_org_name.append(org.name.lower())
                    list_org_obj.append(org)
                    list_org_not_domain_name.append(
                        org.getNotDomainName().lower())
            self.__cache_server.set_session("list_org", list_org_name)
            self.__cache_server.set_session("list_org_obj", list_org_obj)
            self.__cache_server.set_session(
                "list_org_not_domain_name", list_org_not_domain_name)

            self.create_configtx_file()
            self.create_cryptoconfig_file()
            self.create_ca_certificate()
            self.create_cli()
            self.create_couchdb_file()
            self.create_e2e_file()
            self.create_orderer_file()
            self.create_ccp_template_file()
            self.create_env_file()
            self.create_ccp_generate_file()
            self.create_utils_file()
            self.create_script_file()
            self.create_bbchain_file()
            self.create_peer_base_file()
            self.create_explorer_profile_file()
            self.create_explorer_config_file()
            self.create_network_script_file()
            self.create_wait_for_script()
            self.create_executable_file()
            return 1
        except Exception:
            return 0
