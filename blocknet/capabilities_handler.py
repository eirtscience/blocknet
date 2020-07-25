
from .policies import Policies


class CapabilitiesHandler:
    """
    @deprecated
    """

    def __init__(self):
        self.name = None
        self.organization = None
        self.policies = Policies()
        self.enablenodeous = True

    def getEnableNodeOUsAsStr(self):
        return str(self.enablenodeous).lower()

    def getPolicies(self, data=None):

        if data:
            list_policies = data
        else:
            list_policies = {
                "Readers": "ANY Readers",
                "Writers": "ANY Writers",
                "Admins": "MAJORITY Admins"
            }

        policies = ""

        for name, role in list_policies.items():
            policies += Policies(name,
                                 rule_type="ImplicitMeta", role=role).dump()

        return policies

    def getAdminRolePolicies(self):
        return self.getPolicies()
