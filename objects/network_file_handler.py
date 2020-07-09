
from os import path


class NetworkFileHandler:

    @staticmethod
    def networkpath(file_name):
        return path.join("config/fabric", file_name)

    @staticmethod
    def create_script_file(file_name, template):
        NetworkFileHandler.create_file("scripts/"+file_name, template)

    @staticmethod
    def create_file(file_name, template):
        with open(NetworkFileHandler.networkpath(file_name), "w") as f:
            f.write(template)

    @staticmethod
    def create_base_file(file_name, template):
        NetworkFileHandler.create_file("base/" + file_name, template)

    @staticmethod
    def create_explorer_file(file_name, template):
        NetworkFileHandler.create_file("explorer/"+file_name, template)
