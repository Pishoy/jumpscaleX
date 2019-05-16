# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.

"""
Auto-generated class for DeleteEmailOption
"""
from six import string_types

from . import client_support


class DeleteEmailOption(object):
    """
    auto-generated. don't touch.
    """

    @staticmethod
    def create(**kwargs):
        """
        :type emails: list[string_types]
        :rtype: DeleteEmailOption
        """

        return DeleteEmailOption(**kwargs)

    def __init__(self, json=None, **kwargs):
        pass
        if json is None and not kwargs:
            raise ValueError("No data or kwargs present")

        class_name = "DeleteEmailOption"
        data = json or kwargs

        # set attributes
        data_types = [string_types]
        self.emails = client_support.set_property("emails", data, data_types, False, [], True, False, class_name)

    def __str__(self):
        return self.as_json(indent=4)

    def as_json(self, indent=0):
        return client_support.to_json(self, indent=indent)

    def as_dict(self):
        return client_support.to_dict(self)
