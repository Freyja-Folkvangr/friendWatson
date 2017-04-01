from time import gmtime, strftime
class Database:
    def __init__(self, databasePath):
        self.databasePath = databasePath
        #cargo los datos si existen
        import os.path
        if (os.path.exists(self.databasePath)):
            db = self.getDatabase()
            self.knownUsers = db['knownUsers']
            self.user_dict = db['user_dict']
        else:
            self.new()

    def new(self):
        # creo los datos si no existen
        self.knownUsers = []
        self.user_dict = {}
        return self.save()

    def load(self):
        import pickle
        data = pickle.load(open(self.databasePath, "rb"))
        self.knownUsers = data['knownUsers']
        self.user_dict = data['user_dict']
        return True

    def save(self):
        import pickle
        data = {'knownUsers': self.knownUsers, 'user_dict': self.user_dict}
        pickle.dump(data, open(self.databasePath, "wb"))
        return True

    def getDatabase(self):
        import pickle
        return pickle.load(open(self.databasePath, "rb"))

    def refresh(self):
        self.save()
        self.load()

    def __repr__(self):
        parts = []
        blacklist = ['load', 'save', 'getDatabase', 'refresh', 'new', 'refreshTime', 'toCSV']
        for item in dir(self):
            if not item.startswith('__') and item not in blacklist:
                parts.append(str("[DB]> {} = {}".format(item, getattr(self, item))))
            else:
                pass
        return '\n'.join(parts)
