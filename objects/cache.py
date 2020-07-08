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
