
from .channel import Channel
from .orderer import Orderer
from .application import Application


class Capability:
    def __init__(self, list_version):
        self.channel = Channel(list_version)
        self.orderer = Orderer(list_version)
        self.application = Application(list_version)

