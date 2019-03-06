import toml
import re
import copy

from urllib.parse import urlparse
from Jumpscale import j

JSBASE = j.application.JSBaseClass


# Some links that needs to be skipped from verifying because the crawling is forbidden
SKIPPED_LINKS = ['t.me', 'chat.grid.tf', 'linkedin.com', 'docs.grid.tf', 'btc-alpha',
                 'kraken.com', 'bitoasis.net', 'cex.io',  'itsyou.online', 'skype:',
                 'medium.com', "mailto:"]


class CustomLink:
    """A link with custom format of `account:repo(branch):path`

    account, repo and branch are optional, examples:

    threefoldtech:jumpscaleX(development):docs/readme.md
    jumpscaleX(development):docs/readme.md
    jumpscaleX:docs/readme.md
    jumpscaleX:#123
    docs/readme.md
    #124
    http://github.com/account/repo/tree/master/docs/readme.md
    """

    URL_RE = re.compile(r'^(http|https)\:\/\/', re.IGNORECASE)
    REFERENCE_RE = re.compile(r'^\#(\d+)$')
    REPO_PATH_RE = re.compile(r'''
        ^                   # start of the line/string
        (?:                 # non-capturing group
            (.*?)           # match any char -> repo
            (?:             # non-capturing group
                \(          # anything between (...)
                    (.*?)   # in a group -> branch
                \)
            )?              # optional
            \:              # match literal :
        )?                  # optional
        (.*?)$              # anything at the end after that -> path
    ''', re.X)

    def __init__(self, link):
        self.link = link.strip()
        self.account = None
        self.repo = None
        self.branch = None

        if self.is_url:
            self.path = link
        else:
            self.account, other_part = self.get_account()
            self.repo, branch, self.path = self.parse_repo_and_path(other_part)
            self.branch = branch or self.branch

    def get_account(self):
        """get the account and other part

        :return: a tuple of (account, other_part), account can be None
        :rtype: tuple
        """
        if self.link.count(':') == 2:
            account, _, other_part = self.link.partition(':')
            return account, other_part
        return None, self.link

    def parse_repo_and_path(self, repo_and_path):
        """parse the repo and path part, repo(branch):path
        possible examples, `repo(branch):path`, `repo:path` and `path`.

        :param repo_and_path: containing possible format
        :type repo_and_path: str
        :return: a tuple of (repo, branch, path), repo and branch can be None
        :rtype: tuple
        """
        return self.REPO_PATH_RE.match(repo_and_path).groups()

    @property
    def is_url(self):
        """check if the given links is a url

        :return: True if a url, False otherwise
        :rtype: bool
        """
        return bool(self.URL_RE.match(self.link))

    @property
    def reference(self):
        """return the reference id of the given link

        :return: id or None
        :rtype: str
        """
        id_match = self.REFERENCE_RE.match(self.path)
        if id_match:
            return id_match.group(1)

    @property
    def is_reference(self):
        """check if the given link is a reference (e.g. #124)

        :return: True if a reference, False otherwise
        :rtype: bool
        """
        return bool(self.reference)

    @classmethod
    def test(cls):
        l = CustomLink('threefoldtech:jumpscaleX(dev):#124')
        assert l.account == 'threefoldtech'
        assert l.repo == 'jumpscaleX'
        assert l.branch == 'dev'
        assert l.path == '#124'

        l = CustomLink('jumpscaleX(dev):docs/test.md')
        assert l.repo == 'jumpscaleX'
        assert l.branch == 'dev'
        assert l.path == 'docs/test.md'

        l = CustomLink('docs/test.md')
        assert not l.account
        assert not l.repo
        assert l.path == 'docs/test.md'


class Linker:
    HOST = None
    ISSUE = None
    PULL_REQUEST = None
    TREE = None

    def remove_slash(self, arg):
        return arg.lstrip('/')

    def join(self, *args):
        if self.HOST:
            args = (self.HOST, *args)

        args = [self.remove_slash(arg) for arg in args]
        return j.sal.fs.joinPaths(*args)

    def issue(self, _id):
        raise NotImplementedError

    def pull_request(self, _id):
        raise NotImplementedError

    def tree(self, path, branch='master'):
        pass


class GithubLinker(Linker):
    HOST = 'http://github.com'
    ISSUE = 'issues/{id}'
    PULL_REQUEST = 'pull/{id}'
    TREE = 'tree/{branch}'

    def __init__(self, account, repo):
        self.account = account
        self.repo = repo

    def join(self, *args):
        return super(GithubLinker, self).join(self.account, self.repo, *args)

    def issue(self, _id):
        return self.join(self.ISSUE.format(id=_id))

    def pull_request(self, _id):
        return self.join(self.PULL_REQUEST.format(id=_id))

    def tree(self, path, branch=None):
        if not branch:
            branch = 'master'
        return self.join(self.TREE.format(branch=branch), path)


class Link(j.application.JSBaseClass):
    LINK_MARKDOWN_PATTERN = r'''
        \!?                         # match optiona !
        \[                          # start of descirption [
            (
                [^\]\(]+            # match anything other than ] or ( -> description text
            )?                      # optional
        \]                          # end of description
        \(                          # start of link
            (                       # -> full link text
                [^\(\)]*?           # anything other than ( or )
                (?:                 # possible one non-capturing group of (...) for the branch
                    \(              # match literal (
                        [^\(\)]*?   # match anything other than ( or )
                    \)              # match literal )
                )?
                [^\(\)]*?           # anything other than ( or )
            )??                     # optional
        \)                          # end of link
    '''
    LINK_MARKDOWN_RE = re.compile(LINK_MARKDOWN_PATTERN, re.X)

    def __init__(self, doc, source):
        JSBASE.__init__(self)
        self.docsite = doc.docsite
        self.doc = doc
        self.extension = ""
        self.source = source  # original text
        self.cat = ""  # category in image,doc,link,officedoc, imagelink  #doc is markdown
        self.link_source = ""  # text to replace when rewrite is needed
        self.link_source_original = ""  # original link
        self.error_msg = ""
        self.filename = ""
        self.filepath = ""
        self.link_descr = ""  # whats inside the []
        self.link_to_doc = None
        self._process()

    def _clean(self, name):
        return j.core.text.convert_to_snake_case(name)

    def error(self, msg):
        self.error_msg = msg
        msg = "**ERROR:** problem with link:%s\n%s" % (self.source, msg)
        # self._log_error(msg)
        self.docsite.error_raise(msg, doc=self.doc)
        self.doc._content = self.doc._content.replace(self.source, msg)
        return msg

    def remove_quotes(self, s):
        if s:
            return s.replace('"', '').replace("'", '')
        return ''

    def parse_markdown(self, link_markdown):
        match = self.LINK_MARKDOWN_RE.match(link_markdown)
        if match:
            match = match.groups()
            return map(self.remove_quotes, match)
        raise ValueError('not a link markdown')

    @property
    def account(self):
        return self.docsite.git.account

    @property
    def repo(self):
        return self.docsite.git.name

    @property
    def branch(self):
        return self.docsite.git.branchName

    def is_different_source(self, custom_link):
        """check if account, repo or branch are differnt from current docsite

        :param custom_link: instanc of CustomLink
        :type custom_link: CustomLink
        :return: True if different, False if the same
        :rtype: bool
        """
        return custom_link.account and custom_link.account != self.account or \
            custom_link.repo and custom_link.repo != self.repo or \
            custom_link.branch and custom_link.branch != self.branch

    def get_real_source(self, custom_link, linker=None):
        if custom_link.is_url or not self.docsite.git:
            # as-is
            return custom_link.path

        # check for docsite.git.remoteUrl hostname (urlparse)
        account = custom_link.account or self.account
        repo = custom_link.repo or self.repo
        if not linker:
            linker = GithubLinker(account, repo)

        if custom_link.reference:
            return linker.issue(custom_link.reference)

        same_repo = account == self.account and repo == self.repo
        if same_repo:
            # the same docsite, the same internal link
            # also, custom link branch is ignored here
            return custom_link.path

        branch = custom_link.branch
        return linker.tree(custom_link.path, branch=branch)

    def get_docsite(self, external_link, name):
        url = urlparse(external_link)
        path = url.path

        if not j.sal.fs.getFileExtension(path):
            parent_dir = external_link
        else:
            parent_path = j.sal.fs.getDirName(path)
            parent_dir = Linker().join('https://', url.hostname, parent_path)

        new_docsite = j.tools.markdowndocs.load(parent_dir, name=name)
        new_docsite.write()
        return new_docsite

    def _process(self):
        self.link_descr, self.link_source = self.parse_markdown(self.source)
        if self.link_source.strip() == "":
            return self.error("link is empty, but url is:%s" % self.source)

        if "@" in self.link_descr:
            self.link_source_original = self.link_descr.split("@")[1].strip()  # was link to original source
            self.link_descr = self.link_descr.split("@")[0].strip()

        custom_link = CustomLink(self.link_source)
        self.link_source = self.get_real_source(custom_link)

        if "?" in self.link_source:
            lsource = self.link_source.split("?", 1)[0]
        else:
            lsource = self.link_source

        self.extension = j.sal.fs.getFileExtension(lsource)

        if "http" in self.link_source or "https" in self.link_source:
            self.link_source_original = self.link_source
            if self.source.startswith("!"):
                if "?" in self.link_source:
                    link_source = self.link_source.split("?", 1)[0]
                else:
                    link_source = self.link_source
                self.filename = self._clean(j.sal.fs.getBaseName(link_source))

                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4", "mp3", "docx"]:
                    self.extension = "jpeg"  # to support url's like https://images.unsplash.com/photo-1533157961145-8cb586c448e1?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=4e252bcd55caa8958985866ad15ec954&auto=format&fit=crop&w=1534&q=80
                    self.filename = self.filename + '.jpeg'

                if j.sal.fs.getFileExtension(self.filename) != self.extension:
                    j.shell()
            else:
                # check link exists
                self.cat = "link"
                if self.docsite.links_verify:
                    self.link_verify()

                if not custom_link.is_url:
                    # a custom link that wasn't a full url originally, get it's docsite
                    self.get_docsite(self.link_source, name=custom_link.repo)
                    self.filename = self._clean(Linker().join(custom_link.repo, custom_link.path))
                else:
                    self.filename = None  # because is e.g. other site

        else:
            if self.link_source.strip() == "/":
                self.link_source = ""
                return
            if "#" in self.link_source:
                self.link_source = ""
                return

            if "?" in self.link_source:
                self.link_source = self.link_source.split("?", 1)[0]

            if self.link_source.find("/") != -1 and self.extension != "md":
                name = self.link_source.split("/")[-1]
            else:
                name = self.link_source

            self.filename = self._clean(name)  # cleanly normalized name but extension still part of it
            #e.g. balance_inspiration_motivation_life_scene_wander_big.jpg
            if self.filename.strip() == "":
                return self.error("filename is empty")

            # only possible for images (video, image)
            if self.source.startswith("!"):
                self.cat = "image"
                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    return self.error("found unsupported image file: extension:%s" % self.extension)

            if self.cat == "":
                if self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    self.cat = "imagelink"
                elif self.extension in ["doc", "docx", "pdf", "xls", "xlsx", "pdf"]:
                    self.cat = "officedoc"
                elif self.extension in ["md", "", None]:
                    self.cat = "doc"  # link to a markdown document
                    try:
                        self.link_to_doc = self.docsite.doc_get(self.link_source, die=True)
                    except Exception as e:
                        if "Cannot find doc" in str(e):
                            return self.error(str(e))
                        raise e
                else:
                    # j.shell()
                    return self.error("found unsupported extension")

            self.filepath = self.doc.docsite.file_get(self.filename, die=False)

    @property
    def markdown(self):
        if self.source.startswith("!"):
            c = "!"
            if self.link_source_original is not "":
                descr = "%s@%s" % (self.link_descr, self.link_source_original)
            else:
                descr = self.link_descr
        else:
            c = ""
            descr = self.link_descr
        c += "[%s](%s)" % (descr, self.link_source)
        return c

    def download(self, dest):
        if not "http" in self.link_source:
            return
        self._log_info("download:%s\n%s" % (self.link_source_original, dest))
        ddir = j.sal.fs.getDirName(dest)
        if not j.sal.fs.exists(dest):
            # cannot use primitive something wrong sometimes with ssl verification
            cmd = "cd %s;rm -f %s;curl '%s' -o '%s'" % (ddir, dest, self.link_source_original, dest)
            j.sal.process.execute(cmd, die=False)

    def link_verify(self):
        def do():
            if any(link in self.link_source for link in SKIPPED_LINKS):
                return True
            self._log_info("check link exists:%s" % self.link_source)
            if not j.clients.http.ping(self.link_source_original):
                self.error("link not alive:%s" % self.link_source_original)
                return False
            return True
        res = self._cache.get(self.link_source, method=do, expire=3600)
        if res is not True:
            self.error(res)
            return False

    def replace_in_txt(self, txt):
        if len(self.source) < 4:
            j.shell()
            raise RuntimeError("something wrong with original source")
        txt = txt.replace(self.source, self.markdown)
        # self.source = self.markdown #there is a new source now
        return txt

    def __repr__(self):
        if self.cat == "link":
            return "link:%s:%s" % (self.cat, self.link_source)
        else:
            return "link:%s:%s" % (self.cat, self.filename)

    __str__ = __repr__
