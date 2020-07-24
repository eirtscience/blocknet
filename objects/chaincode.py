
import json


class ChainCode:

    def __init__(self, name, language, directory, instantiate_chaincode=False, function=None, querry_chaincode=None, chaincode_org=None):
        self.name = name
        self.language = language
        self.directory = directory
        self.instantiate = instantiate_chaincode
        self.instantiate_function = function
        self.querry = querry_chaincode
        self.chaincode_org = chaincode_org

    def getIntantiate(self):
        if self.instantiate:
            return self.__getFunctionData(self.instantiate_function)

    def getChainCodeOrg(self):
        return ",".join(self.chaincode_org)

    def __replace_quote(self, value):
        return '"{}"'.format(value).replace("'", '"')

    def __getFunctionData(self, value):
        return '{}'.format(json.dumps(value, separators=(',', ':')))
        # value = value.get("function")
        # args = value.get("args")
        # if len(args) > 0:
        #     args = list(map(self.__replace_quote, value.get("args")))
        # return '{{"function":"{0}","Args":{1}}}'.format(value.get("name"), args).replace("'", ' ')

    def getChainCodeQueryRequest(self):
        return self.__getFunctionData(self.querry.get("request"))

    def getChainCodeQueryResponse(self):
        # return "{}".format(self.querry.get("response").get("must_match"))
        return '{}'.format(json.dumps(self.querry.get("response").get("must_match"), separators=(',', ':')))
