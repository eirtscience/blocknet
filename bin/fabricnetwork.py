
from objects.network import Network
from objects.organization import Organization
from .console import Console
from sys import exit


network = Network()


def add_admin():

    print('''
################################################################################
#
#   
# SECTION: Network Admin
#
#   
#
################################################################################

    ''')

    list_admin_info = ["First Name", "Last Name"]

    list_admin_info = Console.get_list_input(list_admin_info)

    domain = Console.get_string("Domain", must_supply=True)

    list_admin_info["domain"] = domain

    list_admin_info["organization_name"] = Console.get_string(
        "Organization Name", default=(domain.split(".")[0]).upper())

    login_name = Console.get_string(
        "Login name", default="admin")

    list_admin_info["login_name"] = login_name

    list_admin_info["login_password"] = Console.get_string(
        "Login password", default="adminpw")

    list_admin_info["email_address"] = Console.get_string(
        "Email Address", default=login_name.lower()+"@"+domain.lower())

    number_of_peer = Console.get_int("Number of peers", default=1)

    list_admin_info["number_of_peer"] = number_of_peer

    network.addnetwork_admin(list_admin_info)


def add_orderer():
    print('''
################################################################################
#
#   SECTION: Orderer
#
#   - This section defines the values to encode into a config transaction or
#   genesis block for orderer related parameters
#
################################################################################

    ''')

    orderer_name = Console.get_string(
        "Network Orderer name", default="Orderer")

    number_of_orderer = Console.get_int(
        "Total Number of Orderer", default=5)

    list_type = ["etcdraft", "solo", "kafka"]

    orderer_type = Console.choice("Type", list_type)

    batchtimeout = Console.get_int("BatchTimeout", default=2)
    maxmessagecount = Console.get_int("MaxMessageCount", default=10)
    absolutemaxbytes = Console.get_int("AbsoluteMaxBytes", default="99 MB")
    preferredmaxbytes = Console.get_int("PreferredMaxBytes", default="512 KB")

    network.addnetwork_orderer({
        "org": {
            "name": orderer_name,
            "type_org": orderer_type,
            "domain": network.admin.domain
        },
        "batchtimeout": batchtimeout,
        "orderer_type": orderer_type,
        "number_of_orderer": number_of_orderer,
        "batchsize": {
            "maxmessagecount": maxmessagecount,
            "absolutemaxbytes": absolutemaxbytes,
            "preferredmaxbytes": preferredmaxbytes
        }
    })


def add_network():

    print('''
################################################################################
#
#
#  SECTION: Network
#
#
################################################################################

    ''')

    list_version = list(network.list_version.keys())

    select_version = Console.choice(
        "Select Network version", list_version)

    name = Console.get_string("Name", must_supply=True)

    network.list_version[list_version[0]] = False
    network.list_version[select_version] = True
    network.current_version = select_version
    network.name = name


def add_consurtium():
    print('''
################################################################################
#
#  
#  SECTION: Consurtium
#
#
################################################################################

    ''')
    channelname = Console.get_string("Channel Name", default=(
        network.admin.organization_name).capitalize() + "Channel")

    network.addconsurtium(channelname=channelname)


def get_org():

    print('''
################################################################################
#
#  
#  SECTION: Organizations
#
#
################################################################################

    ''')

    nbr_of_orgs = Console.get_int(
        "How many organizations do you want to create?", default=2)
    index = 1
    while index <= nbr_of_orgs:
        print("\n\tOrg {} ".format(index))
        organization = Organization(has_anchor=True)
        organization.name = Console.get_string("\t\tName", must_supply=True)
        organization.domain = Console.get_string(
            "\t\tDomain", default="{}.com".format(organization.name.lower()))

        mspid_folder = organization.getmspdir()

        organization.mspdirfolder = Console.get_string(
            "\t\tMSPDIR", default=mspid_folder)

        number_of_peer = Console.get_int("\t\tNumber of peers", default=2)

        network.total_number_of_peer_per_organization = number_of_peer

        organization.addAllPeers(number_of_peer)

        organization.create_certificate()

        network.addorg(organization=organization)
        index += 1
    network.generate()


def start():
    add_network()
    add_admin()
    add_consurtium()
    add_orderer()
    get_org()
