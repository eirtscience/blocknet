

class ChainCode:

    def __init__(self, name, language, directory, instantiate_chaincode=False, function=None, querry_chaincode=None):
        self.name = name
        self.language = language
        self.directory = directory
        self.instantiate = instantiate_chaincode
        self.function = function
        self.querry = querry_chaincode
