import pathlib
import os.path
import json
import time

import requests

# TODO: 2024-02-01 (jps): Add cache expiration after say 1 week.

# Defaults for handling HTTP 429 (Too Many Requests) responses.
MAX_RETRIES = 5
DEFAULT_BACKOFF = 2.0  # seconds, doubled each retry when no Retry-After header


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
        backoff = DEFAULT_BACKOFF
        for attempt in range(MAX_RETRIES):
            response = requests.get(source)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else backoff
                if attempt == MAX_RETRIES - 1:
                    break
                print(
                    f"429 Too Many Requests for {source}; "
                    f"retrying in {delay:.0f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
                backoff *= 2
                continue
            response.raise_for_status()
            return response.content
        raise RuntimeError(
            f"Giving up on {source} after {MAX_RETRIES} attempts (HTTP 429)"
        )
