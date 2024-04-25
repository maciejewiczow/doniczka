import ujson as json

class FileSyncedDict():
    def __init__(self, target_file: str, content):
        self.fileName = target_file
        self.content = content

        try:
            with open(target_file, 'r') as f:
                self.content.update(json.load(f))
        except OSError:
            with open(target_file, 'w') as f:
                json.dump(self.content, f)

    def _saveToFile(self):
        with open(self.fileName, 'w') as f:
            json.dump(self.content, f)

    def __setitem__(self, __key, __value) -> None:
        val = self.content.__setitem__(__key, __value)
        self._saveToFile()
        return val

    def __getitem__(self, name):
        return self.content.__getitem__(name)

    def update(self, other):
        val = self.content.update(other)
        self._saveToFile()
        return val

    def __delitem__(self, __key) -> None:
        val = self.content.__delitem__(__key)
        self._saveToFile()
        return val

    def pop(self, *args, **kwargs):
        val = self.content.pop(*args, **kwargs)
        self._saveToFile()
        return val
