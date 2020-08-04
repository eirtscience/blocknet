from .server import Server


class AnchorPeer:

    def __init__(self, name, org_name=None):

        self.name = name
        self.org_name = org_name
        self.server = Server()

    def dump(self):
        if self.org_name.lower() not in self.server.host:
            self.server.host = "{}.{}".format(
                self.org_name.lower(), self.server.host)

        return "\n\n\n\t\t\t- Host: {}.{}\n\t\t\t  Port: {}".format(self.name, self.server.host, self.server.port)

    def test_unit(self):
        '''
         @apiReturn {  Number }
        '''
        print("hi there ")
        return

    def test_unit_1(self, test1, test2):
        '''
         @apiParam {String} [firstname]

         @apiParam {String} [lastname]

         @apiReturn {Boolean} [True]
        '''
        pass

    def test_unit_2(self, test1, test2):
        '''
         @apiReturn {Number} [5]
        '''
        pass
