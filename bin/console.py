import re


class Console:

    @classmethod
    def get_string(self, label, default=None, must_supply=False):
        if default:
            input_str = str(input("{} [{}]: ".format(label, default)))
            if not input_str:
                return default
            return input_str

        input_str = str(input("{}: ".format(label)))

        while must_supply and not input_str:

            input_str = str(input("{}: ".format(label)))

        return input_str

    @classmethod
    def get_int(self, label, default=None, must_supply=False):
        if default:
            input_int = input("{} [{}]: ".format(label, default))
            if not input_int:
                return default
            return int(input_int)

        return int(input("{}: ".format(label)))

    @classmethod
    def choice(self, label, list_choice=None, default_choice=0, choice_pos=False):

        choice = self.get_int("{} {}".format(label, list_choice),
                              default=list_choice[default_choice])

        if choice_pos:
            choice -= 1
            if choice <= 0 or choice > len(list_choice):
                choice = 0
            return choice

        if isinstance(choice, int):
            choice -= 1
            if choice <= 0 or choice > len(list_choice):
                choice = 0
            return list_choice[choice]
        return choice

    @classmethod
    def get_list_input(self, list_label, type_input="str"):

        list_label_input = {}
        while list_label:
            input_label = list_label.pop(0)

            input_data = Console.get_string(
                input_label, must_supply=True)

            input_label = input_label.lower().replace(' ', '_').strip()

            list_label_input[input_label] = input_data
        return list_label_input
