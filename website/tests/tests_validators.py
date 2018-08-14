"""Unit tests for libs/validators.py"""

import unittest.mock
from django.core.exceptions import ValidationError

from website.libs import validators
from worker.models import Route, Stop

class TestValidateBoolean(unittest.TestCase):
    """Tests for the validate_boolean function."""

    def test_true_returned_for_values_of_true(self):
        """Test that True is returned when the provided value is the boolean True, the string
        "True", "T" or the integer 1."""

        self.assertTrue(validators.validate_boolean(True))
        self.assertTrue(validators.validate_boolean('True'))
        self.assertTrue(validators.validate_boolean('true'))
        self.assertTrue(validators.validate_boolean('TRUE'))
        self.assertTrue(validators.validate_boolean('T'))
        self.assertTrue(validators.validate_boolean('t'))
        self.assertTrue(validators.validate_boolean('1'))
        self.assertTrue(validators.validate_boolean(1))

    def test_false_returned_for_values_of_true(self):
        """Test that False is returned when the provided value is the boolean False, the string
        "False", "f" or the integer 0."""

        self.assertFalse(validators.validate_boolean(False))
        self.assertFalse(validators.validate_boolean('False'))
        self.assertFalse(validators.validate_boolean('false'))
        self.assertFalse(validators.validate_boolean('False'))
        self.assertFalse(validators.validate_boolean('F'))
        self.assertFalse(validators.validate_boolean('f'))
        self.assertFalse(validators.validate_boolean('0'))
        self.assertFalse(validators.validate_boolean(0))

    def test_validation_error_raised_for_invalid_values(self):
        """Test that a ValidationError exception is raised when the provided value is not a valid
        boolean."""

        self.assertRaises(ValidationError, validators.validate_boolean, value='foo')
        self.assertRaises(ValidationError, validators.validate_boolean, value=None)
        self.assertRaises(ValidationError, validators.validate_boolean, value=-1)
        self.assertRaises(ValidationError, validators.validate_boolean, value='-1')
        self.assertRaises(ValidationError, validators.validate_boolean, value=2)

class TestValidateChoice(unittest.TestCase):
    """Tests for the validate_choice function."""

    def test_value_returned_if_value_in_choices(self):
        """Test that the provided value is returned when it is in the provided list of choices."""

        value = 'foo'
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[value]), value)
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[value, 'bar']), value)
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[None, value]), value)

        value = 3
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[1, 2, 3, 4, 5]), value)

        value = None
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[1, 'foo', value]), value)

        value = ['A', 'B']
        self.assertEquals(validators.validate_choice(value=value, valid_choices=[value, ['C', 'D']]), value)

    def test_validation_error_raised_if_value_not_in_choices(self):
        """Test that a ValidationError is raised when the provided value is not in the provided list
        of choices."""

        self.assertRaises(ValidationError, validators.validate_choice, value='foo', valid_choices=['bar'])
        self.assertRaises(ValidationError, validators.validate_choice, value='foo', valid_choices=['bar', 'baz'])
        self.assertRaises(ValidationError, validators.validate_choice, value=5, valid_choices=[1, 2, 3])
        self.assertRaises(ValidationError, validators.validate_choice, value=None, valid_choices=[1, 2, 3])
        self.assertRaises(ValidationError, validators.validate_choice, value=[1, 2], valid_choices=[[3, 4]])

@unittest.mock.patch('website.libs.validators.Route.objects.get')
class TestValidateRouteTag(unittest.TestCase):
    """Tests for the validate_route_tag function."""

    def test_route_tag_returned_if_route_exists_in_database(self, route_get):
        """Test that the provided route tag, converted to a string, is returned if a route exists
        with the tag."""

        route_tag = 'foo'
        self.assertEquals(validators.validate_route_tag(route_tag), route_tag)
        route_get.assert_called_once_with(tag=route_tag)

        route_get.reset_mock()
        route_tag = 25
        self.assertEquals(validators.validate_route_tag(route_tag), str(route_tag))
        route_get.assert_called_once_with(tag=str(route_tag))

    def test_validation_error_raised_if_route_does_not_exist_in_database(self, route_get):
        """Test that a ValidationError exception is raised if no route in the database has a tag
        that matches the provided route tag."""

        route_get.side_effect = Route.DoesNotExist()
        self.assertRaises(ValidationError, validators.validate_route_tag, route_tag='foo')

@unittest.mock.patch('website.libs.validators.Stop.objects.get')
class TestValidateStopTag(unittest.TestCase):
    """Tests for the validate_stop_tag function."""

    def test_stop_tag_returned_if_stop_exists_in_database(self, stop_get):
        """Test that the provided stop tag, converted to a string, is returned if a stop exists
        with the tag."""

        stop_tag = 'foo'
        self.assertEquals(validators.validate_stop_tag(stop_tag), stop_tag)
        stop_get.assert_called_once_with(tag=stop_tag)

        stop_get.reset_mock()
        stop_tag = 25
        self.assertEquals(validators.validate_stop_tag(stop_tag), str(stop_tag))
        stop_get.assert_called_once_with(tag=str(stop_tag))

    def test_validation_error_raised_if_stop_does_not_exist_in_database(self, stop_get):
        """Test that a ValidationError exception is raised if no stop in the database has a tag
        that matches the provided stop tag."""

        stop_get.side_effect = Stop.DoesNotExist()
        self.assertRaises(ValidationError, validators.validate_stop_tag, stop_tag='foo')

class TestValidateTimestamp(unittest.TestCase):
    """Tests for the validate_timestamp function."""

    def test_validation_error_raised_if_timestamp_is_not_integer(self):
        """Test that a ValidationError exception is raised if the provided timestamp cannot be
        cast to an integer."""

        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp='foo')
        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp=None)
        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp=[1])

    def test_validation_error_raised_if_timestamp_is_below_min_time(self):
        """Test that a ValidationError exception is raised if the provided timestamp is earlier than
        the specified min_time."""

        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp=-1, min_time=0)
        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp=-1)
        self.assertRaises(ValidationError, validators.validate_timestamp, timestamp=1, min_time=2)

    def test_timestamp_returned_if_timestamp_is_valid(self):
        """Test that if a valid timestamp that can be cast to an integer and is greater than or
        equal to the min_time is provided, the timestamp cast to an integer is returned."""

        self.assertEquals(validators.validate_timestamp(timestamp=1, min_time=0), 1)
        self.assertEquals(validators.validate_timestamp(timestamp=1, min_time=1), 1)
        self.assertEquals(validators.validate_timestamp(timestamp='10', min_time=0), 10)
        self.assertEquals(validators.validate_timestamp(timestamp=10.000, min_time=0), 10)
        self.assertEquals(validators.validate_timestamp(timestamp=10.12345, min_time=0), 10)
