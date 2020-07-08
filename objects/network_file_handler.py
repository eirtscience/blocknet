
from os import path


class NetworkFileHandler:

    @staticmethod
    def networkpath(file_name):
        return path.join("config/", file_name)

    @staticmethod
    def create_script_file(file_name, template):
        NetworkFileHandler.create_file("scripts/"+file_name, template)

    @staticmethod
    def create_file(file_name, template):
        with open(NetworkFileHandler.networkpath(file_name), "w") as f:
            f.write(template)
