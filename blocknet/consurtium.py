
from .channel import Channel


class Consurtium:
    def __init__(self, name=None, list_version=None):
        self.name = name
        self.organization = None
        self.channel = []
        self.list_version = list_version

    def addChannel(self, name=None):
        self.channel.append(
            Channel(name=name, list_version=self.list_version))

    def numberOfChannel(self):
        return len(self.channel)

    def getInitialChannel(self):
        if len(self.channel) > 0:
            return self.channel[0]
        return
