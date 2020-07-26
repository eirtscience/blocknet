
from os import path, makedirs, walk
import subprocess


class NetworkFileHandler:

    INSTALL_DIR = "./"

    @staticmethod
    def networkpath(file_name):
        path_file = path.join(NetworkFileHandler.INSTALL_DIR, file_name)
        directory_path = path.dirname(path_file)
        if not path.isdir(directory_path):
            NetworkFileHandler.__create_dir(directory_path)
        return path_file

    @staticmethod
    def create_script_file(file_name, template):

        file_name = NetworkFileHandler.create_file(
            "hyperledger-fabric/scripts/" + file_name, template)

        subprocess.call("sudo chmod +x {} ".format(file_name), shell=True)

    @staticmethod
    def create_file(file_name, template, use_network_path=True):

        if use_network_path:
            file_name = NetworkFileHandler.networkpath(file_name)
        with open(file_name, "w") as f:
            f.write(template)

        if ".sh" in file_name:
            subprocess.call("sudo chmod +x {} ".format(file_name), shell=True)
        return file_name

    @staticmethod
    def create_base_file(file_name, template):
        NetworkFileHandler.create_file(
            "hyperledger-fabric/base/" + file_name, template)

    @staticmethod
    def create_explorer_file(file_name, template):
        NetworkFileHandler.create_file(
            "hyperledger-explorer/" + file_name, template)

    @staticmethod
    def create_fabric_file(file_name, template):
        NetworkFileHandler.create_file(
            "hyperledger-fabric/" + file_name, template)

    @staticmethod
    def create_directory():

        config_path = NetworkFileHandler.INSTALL_DIR

        list_dir = ["hyperledger-fabric/", "hyperledger-explorer/", "hyperledger-fabric/base/", "hyperledger-fabric/scripts/",
                    "hyperledger-explorer/config/"]

        for directory in list_dir:
            dir_path = path.join(config_path, directory)
            if not path.isdir(dir_path):
                makedirs(dir_path, exist_ok=True)

    @staticmethod
    def __create_dir(dir_path):
        makedirs(dir_path, exist_ok=True)
