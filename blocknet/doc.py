from .blocknet import BlockNet


class BlocknetDoc:

    @staticmethod
    def version():
        print('''blocknet version {}'''.format(BlockNet.version))
