
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


class NetworkAdministrator(Organization):
    def __init__(self, data):
        self.first_name = data.get("first_name")
        self.domain = data.get("domain")
        self.last_name = data.get("last_name")
        self.email_address = data.get("email_address")
        self.organization_name = data.get("organization_name")
        self.login_username = data.get("login_name")
        self.login_password = data.get("login_password")
        self.organization = None


class Network:
    def __init__(self):
        self.list_version = {"V1_4_4": True, "V1_4_2": False,
                             "V1_3": False, "V1_2": False, "V1_1": False}
        self.name = None
        self.organization = []
        self.capabilities = None
        self.orderer = None
        self.admin = None
        self.application = Application(self.list_version)
        self.current_version = None
        self.consurtium = None
        self.list_org_name = []
        self.genesis = None
        self.total_number_of_peer_per_organization = 0
        self.__cache_server = CacheServer()

    def addconsurtium(self, name=None, channelname=None):
        self.consurtium = Consurtium(name, list_version=self.list_version)
        self.consurtium.addChannel(channelname)

    def getNumberOfPeers(self):
        return self.total_number_of_peer_per_organization

    def channel(self):
        if (self.consurtium.numberOfChannel() == 1):
            return self.consurtium.getInitialChannel()

    def addorg(self, name=None, domain=None, organization=None):
        if name and organization == None:
            self.organization.append(Organization(
                name, domain=domain, has_anchor=True))
        else:
            self.organization.append(organization)

    def addnetwork_admin(self, data):
        self.admin = NetworkAdministrator(data)
        self.genesis = Genesis(
            (self.admin.organization_name.lower()).capitalize())

        organization = Organization(
            self.admin.organization_name, domain=self.admin.domain, type_org="admin", has_anchor=True)

        organization.addAllPeers(data.get("number_of_peer"))

        self.addorg(organization=organization)

        self.admin.organization = organization

    def getAdminOrg(self):
        '''
        return: Organization
        '''
        return self.admin.organization

    def addnetwork_orderer(self, data):
        if data["org"].get("name"):
            self.orderer = Orderer(data=data, list_version=self.list_version)
            self.orderer.create_orderer()
            self.organization.append(self.orderer)

    def getListOrg(self, padding_left=""):
        list_org = ""
        list_org_name = []
        for org in self.organization:
            if isinstance(org, Organization):
                list_org += """
                {} - * {} """.format(padding_left, org.name.upper())
                list_org_name.append(org.name.lower())
        self.__cache_server.set_session("list_org", list_org_name)
        return list_org

    def getPeersConfigForAllOrgs(self):
        peers_config = ""

        for org in self.organization:

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

        for org in self.organization:
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
          - ./crypto-config/peerOrganizations/blackcreek.tech/ca/:/etc/hyperledger/fabric-ca-server-config
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

        with open(NetworkFileHandler.networkpath("docker-compose-ca.yaml"), "w") as f:
            f.write(template)

    def create_profile(self):

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
""".format(self.channel().default_name,
           self.orderer.name,
           self.orderer.organization.name,
           self.orderer.capability_name,
           self.name,
           self.getListOrg(padding_left="\t"*2),
           self.application.name,
           self.application.capability_name,
           self.channel().capability_name,
           self.orderer.type,
           self.orderer.create_consenter(padding_left="\t"*2),
           self.orderer.dump_all_addresses(),
           self.genesis.getName(),
           self.channel().name,
           self.getListOrg()
           )

        return app_str

    def create_cli_services(self):

        list_volumes = []
        list_service = []
        list_depend = []

        for org in self.organization:
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

            elif isinstance(org, Orderer):
                host_name = org.getHostname()
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

        return "".join(list_volumes), "".join(list_service), "".join(list_depend)

    def create_cli(self):

        volumes, services, depends_on = self.create_cli_services()

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
        - ../../blackcreek-chaincode/blackcreek/estate/javascript/:/opt/gopath/src/github.com/chaincode/{7}/node/
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

        """.format(volumes,
                   services,
                   self.getAdminOrg().getAnchorPeer().getHostname(),
                   self.getAdminOrg().id,
                   depends_on,
                   self.admin.email_address,
                   self.admin.domain,
                   self.admin.organization_name.lower()
                   )

        with open(NetworkFileHandler.networkpath("docker-compose-cli.yaml"), "w") as f:
            f.write(template)

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
        with open(NetworkFileHandler.networkpath("configtx.yaml"), "w") as f:
            file_begin = '''
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

            '''

            f.write(file_begin)

            for org in self.organization:
                f.write(org.dump())
                f.write("\n\n")

            f.write(self.create_capability())
            f.write(self.application.dump_application())
            f.write(self.orderer.dump_orderer())
            f.write(self.channel().channel_dump())
            f.write(self.create_profile())

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

        with open(NetworkFileHandler.networkpath("crypto-config.yaml"), "w") as f:
            f.write(template)

    def create_couchdb(self):
        template = ""

        for org in self.organization:
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

        self.create_file("docker-compose-couch.yaml", template)

    def create_file(self, file_name, template):
        with open(NetworkFileHandler.networkpath(file_name), "w") as f:
            f.write(template)

    def create_2e2(self):
        list_volumes = []
        list_service = []
        list_ca_certificate = []
        index = -1

        for org in self.organization:

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

            elif isinstance(org, Orderer):
                host_name = org.getHostname()
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

        self.create_file("docker-compose-e2e-template.yaml", template)

    def create_orderer(self):
        list_orderer = []
        list_orderer_host = []

        for orderer in self.orderer.getAllOrderer(2):
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
        - ./crypto-config/ordererOrganizations/blackcreek.tech/orderers/{orderer.host}/msp:/var/hyperledger/orderer/msp
        - ./crypto-config/ordererOrganizations/blackcreek.tech/orderers/{orderer.host}/tls/:/var/hyperledger/orderer/tls
        - {orderer.host}:/var/hyperledger/production/orderer
        - /etc/localtime:/etc/localtime:ro
        - /etc/timezone:/etc/timezone:ro
    ports:
    - {orderer.port}:{orderer.intern_port}
  """.format(orderer=orderer))

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

        self.create_file("docker-compose-etcdraft2.yaml", template)

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
            self.create_file(file_name, template_data)

    def create_env_file(self):
        template = """
COMPOSE_PROJECT_NAME=net
IMAGE_TAG={}
SYS_CHANNEL=byfn-sys-channel
        """.format(self.current_version.replace("_", ".").strip("V"))

        self.create_file(".env", template)

    def create_ccp_generate_template(self):

        index = 1
        index_main = 2

        template_main = """
    ORG =${{{}}}""".format(index_main)

        template = """
    sed - e 's/\\${{ORG}}/${0}/' \\""".format(index)

        template_exec = ["$ORG"]

        index += 1
        index_main += 1

        for i in range(self.getNumberOfPeers()):
            template += """
        - e 's/\\${{P{0}PORT}}/${1}/' \\""".format(i, index)

            template_exec.append("$P{}PORT".format(i))

            template_main += """
    P{}PORT =${{{}}}""".format(i, index_main)
            index += 1
            index_main += 1

        list_holder = ["CAPORT", "PEERPEM",
                       "CAPEM", "MSP", "DOMAIN", "CA"]

        for value in list_holder:
            template += """
        - e "s#\\${{{}}}/${}/" \\""".format(value, index)

            template_exec.append("${}".format(value))

            template_main += """
    {} =${{{}}}""".format(value, index_main)
            index += 1
            index_main += 1

        for i in range(self.getNumberOfPeers()):

            template += """
        - e "s#\\${{PEER{0}}}#${{{1}}}#" \\""".format(i, index)

            template_exec.append("$PEER{}".format(i))

            template_main += """
    PEER{} =${{{}}}""".format(i, index_main)
            index += 1
            index_main += 1

        template += """
        - e "s#\\${{CANAME}}#${{{}}}#" \\""".format(index)

        template_exec.append("$CANAME")

        template_main += """
    CANAME =${{{}}}""".format(index_main)

        return template, template_main, " ".join(template_exec)

    def create_ccp_generate_file(self):

        template_json, template_main, template_args = self.create_ccp_generate_template()

        template = '''
#!/bin/bash


FABRIC_DIR =$PWD

CONNECXION_PROFILE_DIR =${{FABRIC_PATH}}/connecxion-profile

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
        ${{FABRIC_DIR}}/ccp-template.yaml | sed - e $\'s/\\\\n/\\\n        /g\'
}}


usage(){{

    echo "usages"
}}


main(){{

    {1}


    if [! -d "$FABRIC_PATH/connecxion-profile"]; then

            mkdir - p $FABRIC_PATH/connecxion-profile
    fi



    case $1 in
        yaml)
             echo "$(yaml_ccp {2})" > ${{CONNECXION_PROFILE_DIR}} /${{DOMAIN}}.yaml
            exit 0;;

        json)
            echo "$(json_ccp {2})" > ${{CONNECXION_PROFILE_DIR}} /${{DOMAIN}}.json
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

        for peer_index in range(len(org.list_peer)):

            peer = org.list_peer[peer_index]

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
            self.admin.email_address
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

        for org in self.organization:
            if isinstance(org, Organization):
                if index == 0:
                    list_org_condition.append("""
  if [ $ORG -eq {} ];then
    ORG="{}" """.format(index, org.name))

                    list_org_condition_next.append("""
  if [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{0}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.name,
                        org.id,
                        org.getDomain(),
                        self.admin.email_address,
                        self.create_utils_template_for_peer(org)))

                elif index < (len(self.organization) - 2):
                    list_org_condition.append("""
  elif [ $ORG -eq {} ];then
    ORG="{}" """.format(index, org.name))

                    list_org_condition_next.append("""
  elif [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{0}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.name,
                        org.id,
                        org.getDomain(),
                        self.admin.email_address,
                        self.create_utils_template_for_peer(org)))
                else:
                    list_org_condition.append("""
  else
    ORG="{}" """.format(org.name))
                    list_org_condition_next.append("""
  elif [ $ORG = '{0}' ]; then
    CORE_PEER_LOCALMSPID="{1}"
    CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_{0}_CA
    CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/{2}/users/{3}/msp
    {4} """.format(
                        org.name,
                        org.id,
                        org.getDomain(),
                        self.admin.email_address,
                        self.create_utils_template_for_peer(org)
                    ))

                index += 1

        return function_orderer_global, \
            "".join(list_org_condition), \
            "".join(list_org_condition_next), \
            function_update_anchor_peer, \
            function_instantiate_chaincode, \
            function_upgrade_chaincode

    def create_utils_file(self):

        function_orderer_global, \
            function_global, \
            function_global_next, \
            function_update_anchor_peer, \
            function_instantiate_chaincode, \
            function_upgrade_chaincode = self.create_utils_template()

        template = """
#
# Copyright IBM Corp All Rights Reserved
#
# SPDX-License-Identifier: Apache-2.0
# Modify by Evarist Fangnikoue
#

# This is a collection of bash functions used by different scripts

ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/blackcreek.tech/orderers/orderer.blackcreek.tech/msp/tlscacerts/tlsca.blackcreek.tech-cert.pem
PEER0_BLACKCREEK_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/blackcreek.tech/peers/peer0.blackcreek.tech/tls/ca.crt
PEER0_DC_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/dc.blackcreek.tech/peers/peer0.dc.blackcreek.tech/tls/ca.crt
PEER0_DP_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/dp.blackcreek.tech/peers/peer0.dp.blackcreek.tech/tls/ca.crt

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
            self.orderer.getAnchorPeer())

        NetworkFileHandler.create_script_file("utils.sh", template)

    def create_script_file(self):

        list_org_name = " ".join(self.__cache_server.get_session("list_org"))

        template = """
#!/bin/bash

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
CHAINCODE_DIR="blackcreek"
CHAINCODE_NAME="blackcreek_estate"

CC_SRC_PATH="github.com/chaincode/${{CHAINCODE_DIR}}/go/"
if [ "$LANGUAGE" = "node" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${{CHAINCODE_DIR}}/node/"
fi

if [ "$LANGUAGE" = "java" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${{CHAINCODE_DIR}}/java/"
fi

echo "Channel name : "$CHANNEL_NAME

# import utils
. scripts/utils.sh

createChannel() {{
	setGlobals 0 1

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

## Create channel
echo "Creating channel..."
createChannel

## Join all the peers to the channel
echo "Having all peers join the channel..."
joinChannel

## Set the anchor peers for each org in the channel
echo "Updating anchor peers for dc..."
updateAnchorPeers 0 0
## Set the anchor peers for each org in the channel
echo "Updating anchor peers for dc..."
updateAnchorPeers 0 1

echo "Updating anchor peers for dp..."
updateAnchorPeers 0 2

if [ "${{NO_CHAINCODE}}" != "true" ]; then

	## Install chaincode on peer0.dc and peer0.dp
	echo "Installing chaincode on peer0.dc..."
	installChaincode 0 0
	## Install chaincode on peer0.dc and peer0.dp
	echo "Installing chaincode on peer1.dc..."
	installChaincode 0 1

	echo "Installing chaincode on peer2.dp..."
	installChaincode 0 2


	# Instantiate chaincode on peer0.dp
	echo "Instantiating chaincode on peer2.dp..."
	instantiateChaincode 0 2
	# # Query chaincode on peer0.dc
	echo "Querying chaincode on peer2.dc..."
	chaincodeQuery 0 2 '{{"estate_id":"HglTE3ABymlcWnsiy9b1","estate_name":"Marriot","provider_id":"f363b02c-e1f1-42d4-9078-b4848c45fb42","region":"Guangcheng Hui","staff_id":"e47c659e-a81e-4759-af9e-b42110002b09","street_address":"123 Argyle"}}'

	# # Invoke chaincode on peer0.dc and peer0.dp
	#echo "Sending invoke transaction on peer0.dc peer0.dp..."
	#chaincodeInvoke 0 1 0 2
	
	# ## Install chaincode on peer1.dp
	echo "Installing chaincode on peer1.dp..."
	installChaincode 1 2

	# # Query on chaincode on peer1.dp, check if the result is 90
	echo "Querying chaincode on peer1.dp..."
	#chaincodeQuery 1 2 90
	
fi
  
if [ $? -ne 0 ]; then
	echo "ERROR !!!! Test failed"
    exit 1
fix
        """.format(
            self.consurtium.getInitialChannel().name,
            self.admin.organization_name,
            self.orderer.getAnchorPeer(),
            list_org_name
        )

        NetworkFileHandler.create_script_file("script.sh", template)

    def generate(self):

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
