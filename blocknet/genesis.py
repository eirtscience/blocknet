

class Genesis:

    def __init__(self, name=None):
        self.name = name
        self.channel = None
        self.orderer = None

    def getName(self):
        if self.name:
            return self.name+"Genesis"
