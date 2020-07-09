import pickle


class CacheServer:
    session = {}

    def set_session(self, key, data):
        if key and not self.is_session_exist(key):
            self.session[key] = pickle.dumps(data)

    def get_session(self, key):
        return pickle.loads(self.session.get(key))

    def is_session_exist(self, key):
        return (self.session.get(key) is not None)

    def append_session(self, key, data):
        if key and not self.is_session_exist(key):
            self.session[key] = pickle.dumps(data)
        else:
            old_data = self.get_session(key)
            if isinstance(old_data, list):
                old_data.extend(data)
                new_data = old_data
            elif isinstance(old_data, dict):
                old_data.update(data)
                new_data = old_data
            else:
                new_data = [old_data]
                new_data.append(data)
            self.session[key] = pickle.dumps(new_data)
