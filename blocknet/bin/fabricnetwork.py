#!/env/python

from ..network import Network
from ..organization import Organization
from .console import Console
from ..fabric_repo import FabricRepo
from ..network_file_handler import NetworkFileHandler
from os import walk, path, makedirs
import subprocess
from sys import exit
import json
import argparse


IS_NETWORKFILE_EXIST = False

network = Network()


def add_admin(list_admin_info=None, info=True):

    if info:
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

    if list_admin_info is None:
        list_admin_info = {"First Name": None, "Last Name": None,
                           "Domain": None, "Login name": "admin", "Login password": "adminpw"}

        list_admin_info = Console.get_list_input(list_admin_info)

        domain = list_admin_info["domain"]
        login_name = list_admin_info["login_name"]

        other_admin_info = {
            "Organization Name": (domain.split(".")[0]).upper(),
            "Email Address": login_name.lower()+"@"+domain.lower()
        }

        other_admin_info = Console.get_list_input(other_admin_info)

        list_admin_info.update(other_admin_info)

    network.addnetwork_admin(list_admin_info)


def add_composer_explorer(file_data=None, info=True):

    if info:
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
    data = file_data

    if file_data == None:
        data = {}
        create_composer = Console.get_bool(
            "Do you want to install Hyperledger composer?")

        if create_composer:
            port_number = Console.get_int(
                "Enter the port number", default=8092)

            data["port"] = port_number
        data["install"] = create_composer

    network.add_hy_composer(data)


def add_orderer(file_data=None, info=True):
    if info:
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

    if file_data == None:
        orderer_name = Console.get_string(
            "Network Orderer name", default="Orderer")

        list_type = ["etcdraft", "solo", "kafka"]

        orderer_type = Console.choice("Type", list_type)

        number_of_orderer = Console.get_int(
            "Total Number of Orderer", default=5)

        batchtimeout = Console.get_int("BatchTimeout", default=2)
        maxmessagecount = Console.get_int("MaxMessageCount", default=10)
        absolutemaxbytes = Console.get_int("AbsoluteMaxBytes", default="99 MB")
        preferredmaxbytes = Console.get_int(
            "PreferredMaxBytes", default="512 KB")

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
    else:
        orderer_data = {
            "org": {
                "name": "Orderer",
                "type_org": file_data.get("type"),
                "domain": network.admin.domain
            },
            "batchtimeout": 2,
            "orderer_type": file_data.get("type"),
            "number_of_orderer": file_data.get("number"),
            "batchsize": {
                "maxmessagecount": 10,
                "absolutemaxbytes": "99 MB",
                "preferredmaxbytes": "512 KB"
            }
        }

        network.addnetwork_orderer(orderer_data)


def add_network(file_data=None, info=True):

    if info:
        print('''
################################################################################
#
#
#  SECTION: Network
#
#
################################################################################

        ''')

    if file_data == None:

        list_version = list(network.list_version.keys())

        select_version = Console.choice(
            "Select Network version", list_version)

        name = Console.get_string("Name", default=(
            network.admin.domain.split(".")[0].capitalize())+"Network")

        network.list_version[list_version[0]] = False
        network.list_version[select_version] = True
        network.current_version = select_version
    else:
        name = file_data.get("name")

    network.name = name


def add_consurtium(file_data=None, info=True):

    if info:
        print('''
################################################################################
#
#
#  SECTION: Consurtium
#
#
################################################################################

        ''')

    if file_data == None:
        channelname = Console.get_string("Channel Name", default=(
            network.admin.organization_name).capitalize() + "Channel")
    else:
        channelname = file_data.get("name")

    network.addconsurtium(channelname=channelname)


def add_chaincode(file_data=None, info=True):
    if info:
        print('''
################################################################################
#
#
#  SECTION: ChainCode
#
#
################################################################################

        ''')
    data = {}
    network.orderer.generate_chainecode = False

    if file_data == None:

        generate_chaincode = Console.choice(label="Do you want to generate a chaincode?",
                                            list_choice=["YES", "NO"]).lower()

        if generate_chaincode == "yes":
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
                    data["chaincode_org"].append(
                        "'{}.peer'".format(org.getId()))
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

        data = file_data

        if data.get("name"):
            chaincode_name = data.get("name")
            network.orderer.generate_chainecode = True
            can_instantiate_chaincode = False

            init_json_file = path.join(
                data["directory"], "init.json")

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
                data["instantiate_chaincode"] = can_instantiate_chaincode

            network.addChainCode(data["name"], data)


def get_org(file_data=None, info=True):

    if info:
        print('''
################################################################################
#
#  
#  SECTION: Organizations
#
#
################################################################################

        ''')

    data = {}

    if file_data == None:
        nbr_of_orgs = Console.get_int(
            "How many organizations do you want to create?", default=2)
        index = 1
        while index <= nbr_of_orgs:
            print("\n\tOrg {} ".format(index))
            organization = Organization(has_anchor=True, index=(index-1))
            organization.name = Console.get_string(
                "\t\tName", must_supply=True)
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
    else:
        index = 0
        data["chaincode_org"] = []
        while file_data:
            org_dict = file_data.pop(0)
            organization = Organization(has_anchor=True, index=index)
            organization.name = org_dict.get("name")
            organization.domain = org_dict.get("domain")
            has_chaincode = org_dict.get("has_chaincode")
            organization.has_chain_code = False
            if has_chaincode:
                data["chaincode_org"].append(
                    "'{}.peer'".format(organization.getId()))
                organization.has_chain_code = True

            number_of_peer = org_dict.get("number_of_peer")

            network.total_number_of_peer_per_organization = number_of_peer

            organization.addAllPeers(number_of_peer)

            organization.create_certificate()

            network.addorg(organization=organization, index=index)
    return data


def run_network():

    bin_path = NetworkFileHandler.INSTALL_DIR+"hyperledger-fabric/bin/"

    fa_repo = FabricRepo(network.current_version)

    fa_repo.getRepoByVersion()

    NetworkFileHandler.create_directory()

    list_dir = walk(bin_path)

    for _, __, list_file in list_dir:

        for bin_file in list_file:
            subprocess.call(
                "sudo chmod +x {} ".format(path.join(bin_path, bin_file)), shell=True)

    is_conifg_file_generate = network.generate()

    if is_conifg_file_generate:
        print("Now run the file ./exec.sh to start the network")


def manual_installation():
    if not IS_NETWORKFILE_EXIST:
        add_admin()
        add_network()
        add_consurtium()
        add_orderer()
        get_org()
        add_chaincode()
        add_composer_explorer()


def file_installation(network_file="network.json"):
    if path.isfile(network_file):
        global IS_NETWORKFILE_EXIST
        IS_NETWORKFILE_EXIST = True
        with open(network_file) as json_file:
            data = json.load(json_file)

        add_admin(data.get("network").get("admin"), not IS_NETWORKFILE_EXIST)
        add_network(data.get("network"), not IS_NETWORKFILE_EXIST)
        add_consurtium(data.get("network").get(
            "channel"), not IS_NETWORKFILE_EXIST)
        add_orderer(data.get("network").get(
            "orderer"), not IS_NETWORKFILE_EXIST)
        chaincode_data = get_org(data.get("org"), not IS_NETWORKFILE_EXIST)
        chaincode_data.update(data.get("chaincode"))
        data["chaincode"] = chaincode_data
        add_chaincode(data["chaincode"], not IS_NETWORKFILE_EXIST)
        add_composer_explorer(data.get("explorer"), not IS_NETWORKFILE_EXIST)


def main():
    file_installation()
    manual_installation()
    run_network()


def start():
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument('init', nargs='?')
        args = parser.parse_args()

        if args.init:
            network.create_network_init_file()
        else:
            main()
    except KeyboardInterrupt:
        pass
