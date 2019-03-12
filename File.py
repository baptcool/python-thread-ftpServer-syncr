import os


class File:
    def __init__(self, path):
        self.path = path
        self.creation_time = os.path.getctime(path)
        self.last_modification_time = os.path.getmtime(path)

    def update_instance(self):
        if os.path.exists(self.path) is False:
            return 0

        modification_time = os.path.getmtime(self.path)
        if modification_time == self.last_modification_time:
            return 0
        else:
            self.last_modification_time = modification_time
            return 1
