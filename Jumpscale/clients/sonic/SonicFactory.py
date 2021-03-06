from Jumpscale import j
from .SonicClient import SonicClient

JSConfigs = j.application.JSBaseConfigsClass


class SonicFactory(JSConfigs):

    """
    Sonic Client factory
    """

    __jslocation__ = "j.clients.sonic"
    _CHILDCLASS = SonicClient

    def test(self):
        data = {
            "post:1": "this is some test text hello",
            "post:2": "this is a hello world post",
            "post:3": "hello how is it going?",
            "post:4": "for the love of god?",
            "post:5": "for the love lorde?",
        }
        client = self.get("test", host="127.0.0.1", port=1491, password="dmdm")
        for articleid, content in data.items():
            client.push("forum", "posts", articleid, content)
        assert client.query("forum", "posts", "love") == ["post:5", "post:4"]
        assert client.suggest("forum", "posts", "lo") == ["lorde", "love"]

        print("TEST OK")
