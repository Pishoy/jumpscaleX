from Jumpscale import j

from .BCDB import BCDB
import os
import sys
import redis


class BCDBFactory(j.application.JSBaseClass):

    __jslocation__ = "j.data.bcdb"

    def _init(self):

        self._log_debug("bcdb starts")
        self.bcdb_instances = {}  # key is the name
        self._path = j.sal.fs.getDirName(os.path.abspath(__file__))

        self._code_generation_dir = None
        self.latest = None

        j.clients.redis.core_get()  # just to make sure the redis got started

    def new(self, name, zdbclient=None, reset=False):

        if reset==False and name in self.bcdb_instances:
            return self.bcdb_instances[name]

        self._log_debug("new bcdb:%s" % name)
        if zdbclient != None and j.data.types.string.check(zdbclient):
            raise RuntimeError("zdbclient cannot be str")

        self.bcdb_instances[name] = BCDB(zdbclient=zdbclient, name=name, reset=reset)
        return self.bcdb_instances[name]

    def get(self, name, die=True):
        if name not in self.bcdb_instances:
            if die:
                raise RuntimeError("did not find bcdb with name:%s" % name)
            return None
        return self.bcdb_instances[name]

    def bcdb_test_get(self, reset=True):
        bcdb = j.data.bcdb.new(name="test", zdbclient=None, reset=reset)
        assert j.data.bcdb.latest.zdbclient == None
        return bcdb

    def redis_server_start(
        self,
        name="test",
        ipaddr="localhost",
        port=6380,
        background=False,
        secret="123456",
        zdbclient_addr="localhost",
        zdbclient_port=9900,
        zdbclient_namespace="test",
        zdbclient_secret="1234",
        zdbclient_mode="seq",
    ):

        """
        start a redis server on port 6380 on localhost only

        you need to feed it with schema's

        if zdbclient_addr is None, will use sqlite embedded backend

        trick: use RDM to investigate (Redis Desktop Manager) to investigate DB.

        js_shell "j.data.bcdb.redis_server_start(background=True)"

        js_shell "j.data.bcdb.redis_server_start(background=False,zdbclient_addr=None)"


        :return:
        """

        if background:

            args = 'ipaddr="%s", ' % ipaddr
            args += 'name="%s", ' % name
            args += "port=%s, " % port
            args += 'secret="%s", ' % secret
            args += 'zdbclient_addr="%s", ' % zdbclient_addr
            args += "zdbclient_port=%s, " % zdbclient_port
            args += 'zdbclient_namespace="%s", ' % zdbclient_namespace
            args += 'zdbclient_secret="%s", ' % zdbclient_secret
            args += 'zdbclient_mode="%s"' % zdbclient_mode

            cmd = "kosmos 'j.data.bcdb.redis_server_start(%s)'" % args

            cmdcmd = j.tools.startupcmd.get(
                name="bcdbredis_%s" % port, cmd=cmd, ports=[port]
            )

            cmdcmd.start()

            j.sal.nettools.waitConnectionTest(ipaddr=ipaddr, port=port, timeoutTotal=5)
            r = j.clients.redis.get(ipaddr=ipaddr, port=port, password=secret)
            assert r.ping()

        else:
            if zdbclient_addr not in ["None", None]:
                zdbclient = j.clients.zdb.client_get(
                    nsname=zdbclient_namespace,
                    addr=zdbclient_addr,
                    port=zdbclient_port,
                    secret=zdbclient_secret,
                    mode=zdbclient_mode,
                )
            else:
                zdbclient = None
            bcdb = self.new(name, zdbclient=zdbclient)
            bcdb.redis_server_start(port=port)

    @property
    def code_generation_dir(self):
        if not self._code_generation_dir:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "models")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self._log_debug("codegendir:%s" % path)
            self._code_generation_dir = path
        return self._code_generation_dir

    def _load_test_model(self, reset=True, sqlitestor=False):

        schema = """
        @url = despiegk.test
        llist2 = "" (LS)
        name** = ""
        email** = ""
        nr** = 0
        date_start** = 0 (D)
        description = ""
        token_price** = "10 USD" (N)
        hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        llist5 = "1,2,3" (LI)
        U = 0.0
        pool_type = "managed,unmanaged" (E)
        """

        if self.latest != None:
            self.latest.stop()

        if sqlitestor:
            bcdb = j.data.bcdb.new(name="test", zdbclient=None)
            assert j.data.bcdb.latest.zdbclient == None
            if reset:
                bcdb.reset()  # empty
        else:
            zdbclient_admin = j.servers.zdb.start_test_instance(destroydata=reset)
            zdbclient = zdbclient_admin.namespace_new("test", secret="1234")
            bcdb = j.data.bcdb.new(name="test", zdbclient=zdbclient)

        schemaobj = j.data.schema.get(schema)
        bcdb.model_get_from_schema(schemaobj)

        self._log_debug("bcdb already exists")

        model = bcdb.model_get("despiegk.test")

        return bcdb, model

    def migrate(self, base_url, second_url, bcdb="system", **kwargs):
        bcdb_instance = self.get(bcdb)
        j.data.bcdb.latest.get_all()
        base_model = bcdb_instance.model_get(base_url)
        second_model = bcdb_instance.model_get(second_url)
        # create new meta with new migration

        for model_s in second_model.get_all():
            overwrite = False
            for model_b in base_model.get_all():
                if model_b.name == model_s.name:
                    overwrite = True
                    if kwargs.items():
                        for key, val in kwargs.items():
                            second = getattr(model_s, "{}".format(val))
                            setattr(model_b, key, second)

                    model_b.save()
                    model_s.delete()
                    # overwtite
            if not overwrite:
                m = base_model.new()
                for prop in base_model.schema.properties:

                    if hasattr(model_s, "{}".format(prop.name)):
                        setattr(m, prop.name, getattr(model_s, "{}".format(prop.name)))
                m.save()
                model_s.delete()
                # create new one

    def test(self, name=""):
        """
        following will run all tests

        js_shell 'j.data.bcdb.test()'


        """
        cla = j.servers.zdb.start_test_instance(destroydata=True, namespaces=["test"])
        cl = cla.namespace_get("test", "1234")
        assert cla.ping()
        assert cl.ping()

        bcdb = j.data.bcdb.new("test", zdbclient=cl)

        bcdb.reset()

        self._test_run(name=name)

        j.servers.zdb.stop()
        redis = j.tools.tmux.cmd_get("bcdbredis_6380")
        redis.stop()
        self._log_info("All TESTS DONE")
        return "OK"
