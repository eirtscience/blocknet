

class PoliciesSet:
    def __init__(self, name=None, mspid=None, role=None, rule_type=None):
        self.name = name
        self.type = rule_type
        self.mspid = mspid
        self.role = role
        self.rule = ""

    def dump(self):
        rule = None

        if ("ANY Readers" in self.role) or \
            ("ANY Writers" in self.role) or \
                ("MAJORITY Admins" in self.role):
            self.rule = '"{}"'.format(self.role)
        else:
            rule = []
            if "ADMIN" in self.role:
                rule.append("'{0}.admin'".format(
                    self.mspid))
            if "PEER" in self.role:
                rule.append("'{0}.peer'".format(
                    self.mspid))
            if "CLIENT" in self.role:
                rule.append("'{0}.client'".format(
                    self.mspid))
            if "MEMBER" in self.role:
                rule.append("'{0}.member'".format(
                    self.mspid))

            self.rule = "\"OR("

            self.rule += ",".join(rule)

            self.rule += ")\""

        return "     {}:\n\t\t\t\t   Type: {}\n\t\t\t\t   Rule: {}".format(self.name, self.type, self.rule)


class Policies:
    def __init__(self, name=None, mspid=None, org_type=None, role=None, rule_type="Signature"):
        self.role = role
        self.policieset = PoliciesSet(name, mspid, role, rule_type=rule_type)

    def dump(self):
        str_policies = "\n \t{}".format(self.policieset.dump())
        return str_policies
