from Jumpscale import j
builder_method = j.builder.system.builder_method

class BuilderCaddy(j.builder.system._BaseClass):
    NAME = "caddy"
    PLUGINS = ['iyo']

    def _init(self):
        self.go_runtime = j.builder.runtimes.golang
        

    def clean(self):
        self.stop()
        self._init()
        j.builder.tools.dir_remove("{DIR_BIN}/caddy")

    @builder_method()
    def build(self, plugins=None):
        """
        Get/Build the binaries of caddy itself.

        :param reset: reset the build process, defaults to False
        :type reset: bool, optional
        :param plugins: list of plugins names to be installed, defaults to None
        :type plugins: list, optional
        :raises j.exceptions.RuntimeError: if platform is not supported
        """
        if not j.core.platformtype.myplatform.isUbuntu:
            raise j.exceptions.RuntimeError("only ubuntu supported")

        self.go_runtime.install()

        # build caddy from source using our caddyman
        j.clients.git.pullGitRepo("https://github.com/incubaid/caddyman", dest="/tmp/caddyman")
        self.go_runtime._execute("cd /tmp/caddyman && chmod u+x caddyman.sh")
        if not plugins:
            plugins = self.PLUGINS
        cmd = "/tmp/caddyman/caddyman.sh install {plugins}".format(plugins=" ".join(plugins))
        self.go_runtime._execute(cmd, timeout=60*60)
        self._done_set('build')

    @builder_method()
    def install(self, plugins=None):
        """
        will build if required & then install binary on right location

        :param plugins: plugins to build with if not build already, defaults to None

        kosmos 'j.builder.web.caddy.install()'

        """
        caddy_bin_path = self.tools.joinpaths(self.go_runtime.DIR_GO_PATH_BIN, self.NAME)
        j.builder.tools.file_copy(caddy_bin_path, '{DIR_BIN}/caddy')

    # def start(self, config_file=None, agree=True):
    #     """start caddy
    #
    #     :param config_file: config file path (will use ./Caddyfile if not provided), defaults to None
    #     :type config_file: str, optional
    #     :param agree: agree to Let's Encrypt Subscriber Agreement, defaults to True
    #     :type agree: bool, optional
    #     :raises RuntimeError: if config file doesn't exist
    #     """
    #     cmd = j.core.tools.text_replace("{DIR_BIN}/caddy")
    #
    #     if config_file:
    #         configpath = j.core.tools.text_replace(config_file)
    #         if not j.builder.tools.exists(configpath):
    #             raise RuntimeError('config file does not exist: %s' % configpath)
    #         cmd += ' -conf=%s' % configpath
    #
    #     if agree:
    #         cmd += ' -agree'
    #
    #     cmd = 'ulimit -n 8192; %s' % cmd
    #     return j.tools.tmux.execute(cmd, window=self.NAME, pane=self.NAME, reset=True)
    #


    def sandbox(self, zhub_client):

        bin_dest = j.sal.fs.joinPaths(dest_path, 'sandbox', 'bin')
        self.tools.dir_ensure(bin_dest)
        caddy_bin_path = self.tools.joinpaths(self.go_runtime.DIR_GO_PATH_BIN, self.NAME)
        self.tools.file_copy(caddy_bin_path, bin_dest)
        if create_flist:
            print(self.flist_create(sandbox_dir=dest_path, hub_instance=zhub_instance))
        self._done_set('sandbox')
    
    def _test(self, name=""):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self._test_run(name=name, obj_key='test_main')
