import json
import requests

from models.exceptions import LoadConfigException

file_path = "res/key.json"


def get_api_data():
    with open(file_path) as file:
        return json.load(file)


class Config(object):

    def __init__(self):
        self.api_data = get_api_data()
        self.url = self.api_data["url"]
        self.key = self.api_data["key"]
        self.data = self.__load__()
        self.roles = self.data["roles"]
        self.channels = self.data["channels"]
        self.vanity_roles = self.data["vanity_roles"]

    def __load__(self):
        headers = {"secret-key": self.key,
                   "Content-Type": "application/json"}
        req = requests.get(self.url, headers=headers)
        resp = req.json()
        if "config" not in resp:
            raise LoadConfigException(resp)
        else:
            return resp["config"]

    def reload(self):
        self.data = self.__load__()

    def save(self):
        headers = {"secret-key": self.key,
                   "Content-Type": "application/json",
                   "versioning": False}
        req = requests.put(self.url, json=self.data, headers=headers)
        print(req)
