import pathlib
import os.path
import json

# TODO: 2024-02-01 (jps): Add cache expiration after say 1 week.


class FileCache:
    def __init__(self, prefix, method=json):
        self.prefix = prefix
        self.method = method
        pathlib.Path(self.__cache_dir()).mkdir(parents=True, exist_ok=True)

    def cached(self, key):
        filename = self.__cache_key(key)
        print(f"lookup {filename}")
        if os.path.isfile(filename):
            return self.method.load(open(filename))
        else:
            return None

    def write_cache(self, key, value):
        filename = self.__cache_key(key)
        print(f"write {filename}, {value}")
        with open(filename, "wt") as f:
            self.method.dump(value, f)

    def __cache_key(self, key):
        return f"{self.__cache_dir()}/{key}.{self.method.__name__}"

    def __cache_dir(self):
        return f"cache/{self.prefix}"
