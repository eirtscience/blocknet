import re
from os import system, path
import subprocess


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

    # @staticmethod
    # def get_bool(label, default=True, must_suply=False, choice_range=None):

    #     def bool_value(input_value):
    #         if input_value.lower()["yes", "true"]:
    #             return True
    #         elif input_value.lower() in ["no", "false"]:
    #             return False

    #     if default:
    #         input_int = input("{} [{}]: ".format(label, default))
    #         if input_int:
    #             return default
    #         return bool_value(input_int)

    #     input_bool = bool_value(input("{}: ".format(label)))

    #     if choice_range:
    #         while input_bool not in choice_range:
    #             input_bool = (input("{}: ".format(label)))
    #         return bool_value(input_bool)

    #     while not isinstance(input_bool, bool):
    #         input_bool = (input("{}: ".format(label)))
    #     return bool_value(input_bool)

    @classmethod
    def get_int(self, label, default=None, must_supply=False):
        input_int = None
        try:
            if default:
                input_int = input("{} [{}]: ".format(label, default))
                if not input_int:
                    return default
                return int(input_int)

            return int(input("{}: ".format(label)))
        except ValueError:
            return 0

    @classmethod
    def get_bool(self, label):
        list_choice = ["YES", "NO", "N", "Y", "TRUE", "FALSE"]
        bool_input = input("{} {}:".format(label, list_choice))

        if bool_input.upper() in list_choice:
            bool_input = bool_input.lower()
            if bool_input in ["yes", "y", "true"]:
                return True
            return False
        else:
            return self.get_bool(label)

    @classmethod
    def get_file(self, label):
        path_to_file = Console.get_string(label)

        if path.isfile(path_to_file):
            file_content = ""
            with open(path_to_file) as f:
                file_content = f.read()
            return file_content
        self.get_file(label)

    @classmethod
    def choice(self, label, list_choice=None, default_choice=0, choice_pos=False):

        choice = self.get_int("{} {}".format(label, list_choice),
                              default=list_choice[default_choice])

        if isinstance(choice, str):
            if (choice.upper() in list_choice):
                return choice.upper()
            elif (choice.lower() in list_choice):
                return choice.lower()

        if choice_pos:
            choice -= 1
            if choice <= 0 or choice > len(list_choice):
                choice = 0
            return list_choice[choice]

        if isinstance(choice, int):
            choice -= 1
            if choice <= 0 or choice > len(list_choice):
                choice = 0
            return list_choice[choice]

    @classmethod
    def get_list_input(self, list_label, type_input="str"):

        list_label_input = {}

        if isinstance(list_label, list):
            while list_label:
                input_label = list_label.pop(0)

                input_data = Console.get_string(
                    input_label, must_supply=True)

                input_label = input_label.lower().replace(' ', '_').strip()

                list_label_input[input_label] = input_data

        if isinstance(list_label, dict):
            for input_label, value in list_label.items():
                input_label = (input_label.replace(
                    '_', ' ').strip()).capitalize()
                input_data = Console.get_string(
                    input_label, must_supply=True, default=value)
                input_label = input_label.lower().replace(' ', '_').strip()
                list_label_input[input_label] = input_data

        return list_label_input

    @classmethod
    def run(self, script):
        try:
            subprocess.call(script, shell=True)
        except FileNotFoundError:
            system(script)

    @classmethod
    def error(self, value):
        print("[Error]: {}".format(value))
