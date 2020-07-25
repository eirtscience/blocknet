
import wget
import tarfile
from wget import download as wget_download, bar_thermometer
import subprocess
from os import sys, path

import zipfile
from .network_file_handler import NetworkFileHandler


class FabricRepo:

    def __init__(self, version_number):
        self.version = version_number

    def getRepoByVersion(self):

        installation_folder = NetworkFileHandler.INSTALL_DIR

        if not path.isdir(path.join(installation_folder, "hyperledger-fabric/")):

            version_num = (self.version.replace("_", ".")).lower()

            plaform_repo = "https://github.com/hyperledger-fabric/file/archive/master.zip"

            download_file = wget_download(
                plaform_repo, out="/tmp/master.zip", bar=bar_thermometer)

            zip_file = zipfile.ZipFile(download_file)

            zip_file.extractall(path="/tmp/master")

            zip_file.close()

            subprocess.call(
                "mv /tmp/master/file-master/* {}".format(installation_folder), shell=True)

            repo = "https://github.com/hyperledger/fabric-samples/archive/{}.tar.gz".format(
                version_num)

            download_file = wget_download(
                repo, out="/tmp/fabric-{}.tar.gz".format(version_num), bar=bar_thermometer)

            tar = tarfile.open(download_file)

            tar.extractall(path="/tmp/fabric-repo/")
            tar.close()

            tmp_download = "/tmp/fabric-repo/fabric-samples-{}/".format(
                version_num.strip("v"))

            fabric_first_network = "{}/first-network".format(tmp_download)

            subprocess.call(
                "mv {}/* {}hyperledger-fabric".format(fabric_first_network, installation_folder), shell=True)

            print()
