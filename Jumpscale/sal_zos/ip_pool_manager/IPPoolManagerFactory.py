from Jumpscale import j

JSBASE = j.application.JSBaseClass

from .IPPoolManager import IPPoolsManager


class IPPoolManagerFactory(JSBASE):
    __jslocation__ = "j.sal_zos.ippoolmanager"

    def get(self, pools):
        """
        Get sal for ippoolmanager

        Returns:
            the sal layer 
        """
        return IPPoolsManager(pools)
