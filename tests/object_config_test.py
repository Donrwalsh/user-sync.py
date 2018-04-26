import unittest

from user_sync.config import ObjectConfig


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
