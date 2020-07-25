
from .capabilities_handler import CapabilitiesHandler


class Channel(CapabilitiesHandler):
    def __init__(self, name=None, list_version=None):
        self.capability_name = "ChannelCapabilities"
        self.version = list_version
        self.name = name
        self.default_name = "ChannelDefaults"

    def list_version(self):
        channel_str = ""

        for version_name, is_enable in self.version.items():
            channel_str += "\n\n\t\t  {}: {}".format(
                version_name, str(is_enable).lower())

        return channel_str

    def channel_dump(self):

        app_str = '''

################################################################################
#
#   CHANNEL
#
#   This section defines the values to encode into a config transaction or
#   genesis block for channel related parameters.
#
################################################################################
Channel: &{}
    # Policies defines the set of policies at this level of the config tree
    # For Channel policies, their canonical path is
    #   /Channel/<PolicyName>
    Policies:
        # Who may invoke the 'Deliver' API
        Readers:
            Type: ImplicitMeta
            Rule: "ANY Readers"
        # Who may invoke the 'Broadcast' API
        Writers:
            Type: ImplicitMeta
            Rule: "ANY Writers"
        # By default, who may modify elements at this config level
        Admins:
            Type: ImplicitMeta
            Rule: "MAJORITY Admins"

    # Capabilities describes the channel level capabilities, see the
    # dedicated Capabilities section elsewhere in this file for a full
    # description
    Capabilities:
        <<: *{}
'''.format(self.default_name, self.capability_name)

        return app_str
