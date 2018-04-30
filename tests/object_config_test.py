import unittest
from unittest.mock import patch
import itertools
import six
import logging

import mock

from user_sync.config import ObjectConfig
from user_sync.error import AssertionException


class ObjectConfigTest(unittest.TestCase):
    def assert_eq(self, result, expected, error_message):
        """
        compares the result against the expected value, and outputs an error
        message if they don't match. Also outputs the expected and result
        values.
        """
        self.assertEqual(result, expected, error_message + '\nexpected: %s, got: %s' % (expected, result))

    def setUp(self):
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

        self.assert_eq(self.test_object_primary.parent, None,
                       "On init, parent should be None")
        self.assert_eq(self.test_object_primary.child_configs, {},
                       "On init, child_configs should be an empty dictionary")
        self.assert_eq(self.test_object_primary.scope, self.primary_scope,
                       "On init, passed scope should not change")

    def test_set_parent(self):
        self.test_object_primary.set_parent(self.test_object_secondary)
        self.assert_eq(self.test_object_primary.parent, self.test_object_secondary,
                       "Object added as parent should not change")

    def test_add_child(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.assert_eq(self.test_object_primary.child_configs[self.secondary_scope], self.test_object_secondary,
                       "Object added as child should not change")
        self.assert_eq(self.test_object_secondary.parent, self.test_object_primary,
                       "Child object should contain unchanged parent object")

    def test_find_child_config(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.assert_eq(self.test_object_primary.find_child_config(self.secondary_scope), self.test_object_secondary,
                       "Object added as child should be findable in child_configs attribute")

        self.test_object_primary.add_child(self.test_object_secondary)

        self.assert_eq(self.test_object_primary.find_child_config(self.secondary_scope), self.test_object_secondary,
                       "find_child_configs should only return one object even if there are more than one valid children")

    def test_iter_configs(self):
        for object_config in self.test_object_primary.iter_configs():
            self.assert_eq(object_config, self.test_object_primary,
                           "iter_configs() of an object config with no hierarchy should only return itself")

        self.test_object_primary.add_child(self.test_object_secondary)
        self.test_object_primary.add_child(self.test_object_secondary)

        for object_config in itertools.islice(self.test_object_primary.iter_configs(), 1):
            self.assert_eq(object_config, self.test_object_primary,
                           "iter_configs() of an object config with children should return itself in first position")

        for object_config in itertools.islice(self.test_object_primary.iter_configs(), 1, 3):
            self.assert_eq(object_config, self.test_object_secondary,
                           "iter_configs() of an object config with children should contain those children")

    def test_get_full_scope(self):
        self.test_object_primary.add_child(self.test_object_secondary)

        self.assert_eq(self.test_object_secondary.get_full_scope(), "primary.secondary",
                       "child object's full scope should include parent and child")
        self.assert_eq(self.test_object_primary.get_full_scope(), "primary",
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
            self.assert_eq(self.test_object_primary.describe_types(str), ['str'],
                           'python 3 should describe strings as str')
            self.assert_eq(self.test_object_primary.describe_types(six.string_types), ['str'],
                           'python 3 should describe six.string_types as str')
            self.assert_eq(self.test_object_primary.describe_types(dict), ['dict'],
                           'python 3 should describe dictionaries as dict')
            self.assert_eq(self.test_object_primary.describe_types(list), ['list'],
                           'python 3 should describe lists as list')
            self.assert_eq(self.test_object_primary.describe_types((int, bool, tuple)), ['int', 'bool', 'tuple'],
                           'python 3 should describe multiple types in an ordered list')

    @patch.object(ObjectConfig, "describe_unused_values")
    @patch.object(ObjectConfig, "iter_configs")
    def test_report_unused_values(self, iter_configs_mock, describe_unused_values_mock):
        return_configs = {self.test_object_secondary}
        iter_configs_mock.return_value = return_configs
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
            self.test_object_primary.report_unused_values(m_logger, [self.test_object_secondary])
        except AssertionException:
            self.fail("An AssertionException should not be raised if an unused key is present in optional configs")
        else:
            m_logger.log.assert_called_with(logging.WARNING, 'key_in_optional_configs')
            pass

    def test_describe_unused_values(self):
        self.assert_eq(self.test_object_primary.describe_unused_values(), [],
                       "This method should return an empty list")








