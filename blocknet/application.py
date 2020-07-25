from .policies import Policies
from .capabilities_handler import CapabilitiesHandler


class Application(CapabilitiesHandler):

    def __init__(self, list_version=None):
        self.version = list_version
        self.capability_name = "ApplicationCapabilities"
        self.name = "ApplicationDefaults"

    def list_version(self):
        data_str = ""

        for version_name, is_enable in self.version.items():
            data_str += "\n\n\t\t  {}: {}".format(
                version_name, str(is_enable).lower())

        return data_str

    def dump_application(self):
        app_str = '''

################################################################################
#
#   SECTION: Application
#
#   - This section defines the values to encode into a config transaction or
#   genesis block for application related parameters
#
################################################################################
Application: &{}

    # Organizations is the list of orgs which are defined as participants on
    # the application side of the network
    Organizations:

    # Policies defines the set of policies at this level of the config tree
    # For Application policies, their canonical path is
    #   /Channel/Application/<PolicyName>
    Policies:
        {}

    Capabilities:
        <<: *{}
        '''.format(self.name, self.getPolicies(), self.capability_name)

        return app_str
