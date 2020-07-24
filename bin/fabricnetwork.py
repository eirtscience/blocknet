#!/env/python

from objects.network import Network
from objects.organization import Organization
from .console import Console
from objects.fabric_repo import FabricRepo
from objects.network_file_handler import NetworkFileHandler
from os import walk, path, makedirs
import subprocess
from sys import exit
import json


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

    # number_of_peer = Console.get_int("Number of peers", default=1)

    # list_admin_info["number_of_peer"] = number_of_peer

    network.addnetwork_admin(list_admin_info)


def add_composer_explorer():
    print('''
################################################################################
#
#   SECTION: Composer Explorer
#
#   - This section will create a Hyperledger Explorer UI to view the blockchain
#     transaction and configuration.
#
################################################################################
    ''')
    data = {}
    create_composer = Console.get_bool(
        "Do you want to install Hyperledger composer?")

    port_number = 8092

    if create_composer:
        port_number = Console.get_int(
            "Enter the port number", default=port_number)

    data["port"] = port_number
    data["install"] = create_composer

    network.add_hy_composer(data)


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

    list_type = ["etcdraft", "solo", "kafka"]

    orderer_type = Console.choice("Type", list_type)

    number_of_orderer = Console.get_int(
        "Total Number of Orderer", default=5)

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

    name = Console.get_string("Name", default=(
        network.admin.domain.split(".")[0].capitalize())+"Network")

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


def add_chaincode():
    print('''
################################################################################
#
#  
#  SECTION: ChainCode
#
#
################################################################################

    ''')

    generate_chaincode = Console.choice(label="Do you want to generate a chaincode?",
                                        list_choice=["YES", "NO"]).lower()

    if generate_chaincode == "yes":
        data = {}
        network.orderer.generate_chainecode = True
        chaincode_name = Console.get_string("Name", must_supply=True)
        data["language"] = Console.choice("Language", list_choice=[
            "go", "node", "java"])
        data["directory"] = Console.get_string(
            "Directory (Use the absolute path)", must_supply=True)

        data["chaincode_org"] = []

        for org in network.getOrganization():
            is_select = Console.get_bool(
                "Do you want to run this chaincode for organization '{}' ".format(org.name))
            if is_select:
                data["chaincode_org"].append("'{}.peer'".format(org.getId()))
                org.has_chain_code = True

        can_instantiate_chaincode = False

        if not path.isdir(data["directory"]):

            Console.run("sudo mkdir -p {}".format(data["directory"]))

        else:

            init_json_file = path.join(data["directory"], "init.json")

            if path.isfile(init_json_file):
                with open(path.join(data["directory"], "init.json")) as json_file:
                    init_json_data = json.load(json_file)

                data["directory"] += "/{}".format(chaincode_name)

                chaincode_data = init_json_data[chaincode_name]

                if chaincode_data.get("instantiate") is not None:
                    can_instantiate_chaincode = True

                data["function"] = chaincode_data.get(
                    "instantiate")

                data["querry_chaincode"] = chaincode_data.get("query")

            else:
                Console.error("Cannot find the chaincode init file")

                can_instantiate_chaincode = Console.get_bool(
                    "Do you want to instantiate the chaincode ?")

                data["instantiate_chaincode"] = can_instantiate_chaincode

                if can_instantiate_chaincode:
                    chaincode_function = Console.get_file("Please input a json file with the init function of your chaincode \n Example: \
                        {\"function\":\"initLedger\",\"Args\":[]}")
                    data["function"] = chaincode_function

                    querry_chaincode = Console.get_file(
                        "Please input a json file with the response data to verify the querry result")

                    data["querry_chaincode"] = querry_chaincode

        data["name"] = chaincode_name
        data["instantiate_chaincode"] = can_instantiate_chaincode

        network.addChainCode(data["name"], data)

        # print(network.orderer.getInitialChainCode().getIntantiate())

    else:
        network.orderer.generate_chainecode = False


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
        organization = Organization(has_anchor=True, index=(index-1))
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

        network.addorg(organization=organization, index=(index-1))
        index += 1


def run_network():

    fa_repo = FabricRepo(network.current_version)

    fa_repo.getRepoByVersion()

    NetworkFileHandler.create_directory()

    bin_path = "config/hyperledger-fabric/bin/"

    list_dir = walk(bin_path)

    for _, __, list_file in list_dir:

        for bin_file in list_file:
            subprocess.call(
                "sudo chmod +x {} ".format(path.join(bin_path, bin_file)), shell=True)

    is_conifg_file_generate = network.generate()

    if is_conifg_file_generate:
        print("Now run the file ./exec.sh to start the network")


def start():
    add_admin()
    add_network()
    add_consurtium()
    add_orderer()
    get_org()
    add_chaincode()
    add_composer_explorer()
    run_network()
