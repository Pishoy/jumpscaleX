from Jumpscale import j

from .NACL import NACL
import nacl.secret
import nacl.utils
import base64
import hashlib
from nacl.public import PrivateKey, SealedBox
import fakeredis

JSBASE = j.application.JSBaseClass


class NACLFactory(j.application.JSBaseClass):
    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.data.nacl"
        self._default = None

        # check there is core redis
        if isinstance(j.core.db, fakeredis.FakeStrictRedis):
            j.clients.redis.core_get()

    def configure(
        self, name="default", privkey_words=None, secret=None, sshagent_use=None, interactive=False, generate=False
    ):
        """
        secret is used to encrypt/decrypt the private key when stored on local filesystem
        privkey_words is used to put the private key back

        will ask for the details of the configuration
        :param: sshagent_use is True, will derive the secret from the private key of the ssh-agent if only 1 ssh key loaded
                                secret needs to be None at that point
        :param: secret only used when sshagent not used, will be stored encrypted in redis
                sha256 is used on the secret as specified above before storing/encrypting/decrypting the private key

        :param: generate if True and interactive is False then will autogenerate a key

        :return: None

        """
        n = self.get(name=name, load=False)
        n.configure(
            privkey_words=privkey_words,
            secret=secret,
            sshagent_use=sshagent_use,
            interactive=interactive,
            generate=generate,
        )
        return n

    def get(self, name="default", load=True):
        """
        """
        n = NACL(name=name)
        if load:
            n.load()
        return n

    @property
    def default(self):
        if self._default is None:
            self._default = self.get()
        return self._default

    def test(self):
        """
        js_shell 'j.data.nacl.test()'
        """

        cl = self.default  # get's the default location & generate's keys

        data = b"something"
        r = cl.sign(data)

        assert cl.verify(data, r)
        assert cl.verify(b"a", r) == False

        pubsignkey32 = cl.signingkey_pub.encode()

        assert cl.verify(data, r, pubsignkey32)

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)

        assert b == b"something"

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        a = cl.encryptSymmetric("something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        a = cl.encryptSymmetric(b"something")
        b = cl.decryptSymmetric(a)
        assert b == b"something"

        # now with hex
        a = cl.encryptSymmetric(b"something", hex=True)
        b = cl.decryptSymmetric(a, hex=True)
        assert b == b"something"

        a = cl.encrypt(b"something")
        b = cl.decrypt(a)

        assert b == b"something"

        a = cl.encrypt("something")  # non binary start
        b = cl.decrypt(a)

        # now with hex
        a = cl.encrypt("something", hex=True)  # non binary start
        b = cl.decrypt(a, hex=True)
        assert b == b"something"

        self._log_info("TEST OK")

    def test_perf(self):
        """
        js_shell 'j.data.nacl.test_perf()'
        """

        cl = self.default  # get's the default location & generate's keys
        data = b"something"

        nr = 10000
        j.tools.timer.start("signing")
        for i in range(nr):
            p = str(i).encode()
            r = cl.sign(data + p)
        j.tools.timer.stop(i)

        nr = 10000
        j.tools.timer.start("encode and verify")
        for i in range(nr):
            p = str(i).encode()
            r = cl.sign(data + p)
            assert cl.verify(data + p, r)
        j.tools.timer.stop(i)

        nr = 10000
        data2 = data * 20
        j.tools.timer.start("encryption/decryption assymetric")
        for i in range(nr):
            a = cl.encrypt(data2)
            b = cl.decrypt(a)
            assert data2 == b
        j.tools.timer.stop(i)

        nr = 40000
        secret = b"something111"
        data2 = data * 20
        j.tools.timer.start("encryption/decryption symmetric")
        for i in range(nr):
            a = cl.encryptSymmetric(data2, secret=secret)
            b = cl.decryptSymmetric(a, secret=secret)
            assert data2 == b
        j.tools.timer.stop(i)
