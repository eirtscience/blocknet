
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

    def create_installer_script(self):
        template = """#!/bin/bash

BLOCKNET_PATH=""

prerequisite(){

  can_run=0

  which docker 1> /dev/null

  if [ ! $? -eq 0 ];then
      sudo apt-get install -y docker.io 
  fi

  which docker-compose 1> /dev/null

  if [ ! $? -eq 0 ];then

    sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

  fi

  which git 1> /dev/null

  if [ ! $? -eq 0 ];then
    sudo apt-get install -y git
  fi

}

download(){

  git clone https://github.com/hyperledger-fabric/file.git

  mv file/* .
  rm -rf file/
  rm -rf .git/
  rm -rf images/
  rm -rf README.md

  install_python_package

  export BLOCKNET_PATH=`pwd`
}

install_python_package(){

    echo '''
certifi==2020.6.20
chardet==3.0.4
console==0.990
ezenv==0.91
idna==2.10
pyaml==20.4.0
python-git==2018.2.1
PyYAML==5.3.1
requests==2.24.0
Send2Trash==1.5.0
urllib3==1.25.9
wget==3.2
zipfile36==0.1.3
blocknet==0.0.1
    ''' > packages.txt

    pip install -r packages.txt
}

clean(){
    rm -rf installer.sh
    rm -rf packages.txt
}

install(){

    prerequisite
    download
    sudo touch ~/.blocknet
    clean
}

main(){
  case $1 in
    check-env)
        prerequisite
    ;;
    install)
        install $@
    ;;
  esac


  
}

main $@
        """

        NetworkFileHandler.create_file("installer.sh", template)

    def getRepoByVersion(self):

        if not path.isfile("~/.blocknet"):
            self.create_installer_script()
            subprocess.call("./installer.sh install", shell=True)
