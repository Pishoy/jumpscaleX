from Jumpscale import j

builder_method = j.builder.system.builder_method


class BuilderTraefik(j.builder.system._BaseClass):
    NAME = "traefik"
    VERSION = "1.7.9"  # latest
    URL = "https://github.com/containous/traefik/releases/download/v{version}/traefik_{platform}-{arch}"

    def _init(self):

        self.go_runtime = j.builder.runtimes.golang

    @builder_method()
    def install(self, reset=True):
        """

        kosmos 'j.builder.web.traefik.install()'

        """
        version = tuple(map(int, self.go_runtime.STABLE_VERSION.split(".")))
        if version < (1, 9):
            raise j.exceptions.RuntimeError("%s requires go version >= 1.9")

        # get the prebuilt binary, as the building needs docker...etc
        # only check for linux for now
        arch = self.go_runtime.current_arch
        if j.core.platformtype.myplatform.isLinux:
            download_url = self.URL.format(version=self.VERSION, platform="linux", arch=arch)
        else:
            raise j.exceptions.RuntimeError("platform not supported")

        dest = self.tools.joinpaths("{DIR_BIN}", self.NAME)
        self.tools.file_download(download_url, dest, overwrite=True, retry=3, timeout=0)
        self.tools.file_attribs(dest, mode=0o770)

        self._done_set("install")

    def start(self, config_file=None, args=None):
        """Starts traefik with the configuration file provided

        :param config_file: config file path e.g. ~/traefik.toml
        :type config_file: str, optional
        :param args: any additional arguments to be passed to traefik
        :type args: dict, optional (e.g. {'api': '', 'api.dashboard': 'true'})
        :raises j.exceptions.RuntimeError: in case config file does not exist
        :return: tmux pane
        :rtype: tmux.Pane
        """
        self.install()
        cmd = self.tools.joinpaths(j.core.dirs.BINDIR, self.NAME)
        if config_file and self.tools.file_exists(config_file):
            cmd += " --configFile=%s" % config_file

        args = args or {}
        for arg, value in args.items():
            cmd += " --%s" % arg
            if value:
                cmd += "=%s" % value

        p = j.tools.tmux.execute(cmd, window=self.NAME, pane=self.NAME, reset=True)
        return p

    def stop(self, pid=None, sig=None):
        """Stops traefik process

        :param pid: pid of the process, if not given, will kill by name
        :type pid: long, defaults to None
        :param sig: signal, if not given, SIGKILL will be used
        :type sig: int, defaults to None
        """
        if pid:
            j.sal.process.kill(pid, sig)
        else:
            j.sal.process.killProcessByName(self.NAME, sig)

    def test(self):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self.install()
        self.start()
        self.stop()
        print("TEST OK")

    @builder_method()
    def sandbox(self):

        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        self.install()
        bin_dest = j.sal.fs.joinPaths("/sandbox/var/build", "{}/sandbox".format(self.DIR_SANDBOX))
        self.tools.dir_ensure(bin_dest)
        traefik_bin_path = self.tools.joinpaths("{DIR_BIN}", self.NAME)
        self.tools.file_copy(traefik_bin_path, bin_dest)
