import pathlib
import os.path
import json
import requests

# TODO: 2024-02-01 (jps): Add cache expiration after say 1 week.


class FileCache:
    def __init__(self, prefix, method=json):
        self.prefix = prefix
        self.method = method
        pathlib.Path(self.__cache_dir()).mkdir(parents=True, exist_ok=True)

    def cached(self, key, source):
        filename = self.__cache_key(key)
        if os.path.isfile(filename):
            content = open(filename).read()
            return self.method.loads(content)
        else:
            content = self.method.loads(self.__retrieve(source))
            self.write_cache(key, content)
            return content

    def write_cache(self, key, value):
        filename = self.__cache_key(key)
        with open(filename, "w") as f:
            f.write(self.method.dumps(value))

    def __cache_key(self, key):
        return f"{self.__cache_dir()}/{key}.{self.method.__name__}"

    def __cache_dir(self):
        return f"cache/{self.prefix}"

    def __retrieve(self, source):
        return requests.get(source).content
