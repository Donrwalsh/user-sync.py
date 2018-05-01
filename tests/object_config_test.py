# Copyright (c) 2016-2017 Adobe Systems Incorporated.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import unittest
from unittest.mock import patch
import itertools
import six
import logging

import mock

from user_sync.config import ObjectConfig, ListConfig
from user_sync.error import AssertionException


class TestUtility(unittest.TestCase):

    def assert_isSubclass(self, child, parent, error_message):
        self.assertTrue(issubclass(child, parent), error_message)

    def assert_eq(self, result, expected, error_message):
        """
        compares the result against the expected value, and outputs an error
        message if they don't match. Also outputs the expected and result
        values.
        """
        self.assertEqual(result, expected, error_message + '\nexpected: %s, got: %s' % (expected, result))


class ListConfigTest(unittest.TestCase):
    def setUp(self):
        self.util = TestUtility()
        self.primary_scope = "primary"
        self.secondary_scope = "secondary"
        self.primary_values = ["one", "two", "three"]
        self.secondary_values = ["four", "five", "six"]
        self.test_object_primary = ListConfig(self.primary_scope, self.primary_values)
        self.test_object_secondary = ListConfig(self.secondary_scope, self.secondary_values)

    def test_init(self):
        try:
            ListConfig()
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail("TypeError not raised when required arguments are omitted")

        self.util.assert_eq(self.test_object_primary.value, self.primary_values,
                            "On init, passed value should not change")
        self.util.assert_isSubclass(self.test_object_primary.__class__, ObjectConfig,
                                    "ListConfig objects should be children of ObjectConfig")


class ObjectConfigTest(unittest.TestCase):

    def setUp(self):
        self.util = TestUtility()
        self.primary_scope = "primary"
        self.secondary_scope = "secondary"
        self.test_object_primary = ObjectConfig(self.primary_scope)
        self.test_object_secondary = ObjectConfig(self.secondary_scope)

    def test_init(self):
        try:
            ObjectConfig()
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail("TypeError not raised when scope is omitted")

        self.util.assert_eq(self.test_object_primary.parent, None,
                            "On init, ObjectConfig.parent should be None")
        self.util.assert_eq(self.test_object_primary.child_configs, {},
                            "On init, child_configs should be an empty dictionary")
        self.util.assert_eq(self.test_object_primary.scope, self.primary_scope,
                            "On init, passed scope should not change")

    def test_set_parent(self):
        self.test_object_primary.set_parent(self.test_object_secondary)
        self.util.assert_eq(self.test_object_primary.parent, self.test_object_secondary,
                            "Object added as parent should not change")

    def test_add_child(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.util.assert_eq(self.test_object_primary.child_configs[self.secondary_scope], self.test_object_secondary,
                            "Object added as child should not change")
        self.util.assert_eq(self.test_object_secondary.parent, self.test_object_primary,
                            "Child object should contain unchanged parent object")

    def test_find_child_config(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.util.assert_eq(self.test_object_primary.find_child_config(self.secondary_scope), self.test_object_secondary,
                            "Object added as child should be findable in child_configs attribute")

        self.test_object_primary.add_child(self.test_object_secondary)

        self.util.assert_eq(self.test_object_primary.find_child_config(self.secondary_scope), self.test_object_secondary,
                            "find_child_configs should only return one object even if there are multiple valid children")

    def test_iter_configs(self):
        for object_config in self.test_object_primary.iter_configs():
            self.util.assert_eq(object_config, self.test_object_primary,
                                "iter_configs() of an object config with no hierarchy should only return itself")

        self.test_object_primary.add_child(self.test_object_secondary)
        self.test_object_primary.add_child(self.test_object_secondary)

        for object_config in itertools.islice(self.test_object_primary.iter_configs(), 1):
            self.util.assert_eq(object_config, self.test_object_primary,
                                "iter_configs() of an object config with children should return itself in 1st position")

        for object_config in itertools.islice(self.test_object_primary.iter_configs(), 1, 3):
            self.util.assert_eq(object_config, self.test_object_secondary,
                                "iter_configs() of an object config with children should contain those children")

    def test_get_full_scope(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.util.assert_eq(self.test_object_secondary.get_full_scope(), "primary.secondary",
                            "child object's full scope should include parent and child")
        self.util.assert_eq(self.test_object_primary.get_full_scope(), "primary",
                            "parent object's full scope should only include self")

    def test_create_assertion_error(self):
        try:
            raise self.test_object_primary.create_assertion_error('Something went wrong')
        except AssertionException:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)

    def test_describe_types(self):
        if six.PY3:
            self.util.assert_eq(self.test_object_primary.describe_types(str), ['str'],
                                'python 3 should describe strings as str')
            self.util.assert_eq(self.test_object_primary.describe_types(six.string_types), ['str'],
                                'python 3 should describe six.string_types as str')
            self.util.assert_eq(self.test_object_primary.describe_types(dict), ['dict'],
                                'python 3 should describe dictionaries as dict')
            self.util.assert_eq(self.test_object_primary.describe_types(list), ['list'],
                                'python 3 should describe lists as list')
            self.util.assert_eq(self.test_object_primary.describe_types((int, bool, tuple)), ['int', 'bool', 'tuple'],
                                'python 3 should describe multiple types in an ordered list')

    @patch.object(ObjectConfig, "describe_unused_values")
    def test_report_unused_values(self, describe_unused_values_mock):
        self.test_object_primary.add_child(self.test_object_secondary)
        m_logger = mock.Mock()

        # The core ObjectConfig should never log with this method as describe_unused_values returns nothing
        self.test_object_primary.report_unused_values(m_logger)
        m_logger.assert_not_called()

        describe_unused_values_mock.return_value = "key_not_in_optional_configs"
        try:
            self.test_object_primary.report_unused_values(m_logger)
        except AssertionException:
            m_logger.log.assert_called_with(logging.ERROR, 'key_not_in_optional_configs')
            pass
        else:
            self.fail("An AssertionException should be raised if an unused key is not present in optional_configs")

        describe_unused_values_mock.return_value = "key_in_optional_configs"
        try:
            self.test_object_primary.report_unused_values(m_logger,
                                                          [self.test_object_primary, self.test_object_secondary])
        except AssertionException:
            self.fail("An AssertionException should not be raised if an unused key is present in optional configs")
        else:
            m_logger.log.assert_called_with(logging.WARNING, 'key_in_optional_configs')
            pass

    def test_describe_unused_values(self):
        self.util.assert_eq(self.test_object_primary.describe_unused_values(), [],
                            "This method should return an empty list")

