"""Unit tests for libs/utils.py"""

import unittest
import unittest.mock

from django.test import tag

import worker.libs.utils as utils

@tag('unit')
class TestEnsureIsList(unittest.TestCase):
    """Tests for the ensure_is_list function"""

    def test_list_returned_for_single_value(self):
        """Test that if the provided value is not a list, a list containing the value as its only
        element is returned."""

        str_value = 'abcd'
        str_response = utils.ensure_is_list(str_value)
        self.assertEquals([str_value], str_response)

        int_value = 5
        int_response = utils.ensure_is_list(int_value)
        self.assertEquals([int_value], int_response)

        bool_value = False
        bool_response = utils.ensure_is_list(bool_value)
        self.assertEquals([bool_value], bool_response)

        none_value = None
        none_response = utils.ensure_is_list(none_value)
        self.assertEquals([none_value], none_response)

        dict_value = {'a': 1, 'b': 2}
        dict_response = utils.ensure_is_list(dict_value)
        self.assertEquals([dict_value], dict_response)

        tuple_value = (1, 2, 3, 4)
        tuple_response = utils.ensure_is_list(tuple_value)
        self.assertEquals([tuple_value], tuple_response)

    def test_unmodified_list_returned_if_value_is_list(self):
        """Test that if the provided value is a list, it is returned without being modified."""

        value = ['a', 2, {'A': 1}]
        response = utils.ensure_is_list(value)
        self.assertIs(response, value)

        # Test with a nested list
        nested_list = [[1, 2], [[[[[3]], 5]]]]
        nested_list_response = utils.ensure_is_list(nested_list)
        self.assertIs(nested_list_response, nested_list)

@tag('unit')
@unittest.mock.patch('worker.libs.utils.datetime.datetime')
class TestGetCurrentServiceClass(unittest.TestCase):
    """Tests for the get_current_service_class function"""

    def test_sat_returned_if_current_day_is_saturday(self, datetime):
        """Test that "sat" is returned when the current day of the week is Saturday."""

        datetime.now.return_value.strftime.return_value = 'Saturday'
        response = utils.get_current_service_class()
        self.assertEquals(response, 'sat')

    def test_sun_returned_if_current_day_is_sunday(self, datetime):
        """Test that "sun" is returned when the current day of the week is Sunday."""

        datetime.now.return_value.strftime.return_value = 'Sunday'
        response = utils.get_current_service_class()
        self.assertEquals(response, 'sun')

    def test_wkd_returned_if_current_day_is_a_weekday(self, datetime):
        """Test that "wkd" is returned when the current day of the week is any weekday."""

        datetime.now.return_value.strftime.return_value = 'Monday'
        monday_response = utils.get_current_service_class()
        self.assertEquals(monday_response, 'wkd')

        datetime.now.return_value.strftime.return_value = 'Tuesday'
        tuesday_response = utils.get_current_service_class()
        self.assertEquals(tuesday_response, 'wkd')

        datetime.now.return_value.strftime.return_value = 'Wednesday'
        wednesday_response = utils.get_current_service_class()
        self.assertEquals(wednesday_response, 'wkd')

        datetime.now.return_value.strftime.return_value = 'Thursday'
        thursday_response = utils.get_current_service_class()
        self.assertEquals(thursday_response, 'wkd')

        datetime.now.return_value.strftime.return_value = 'Friday'
        friday_response = utils.get_current_service_class()
        self.assertEquals(friday_response, 'wkd')

@tag('unit')
@unittest.mock.patch('worker.libs.utils.datetime.datetime')
class TestGetSecondsSinceMidnight(unittest.TestCase):
    """Tests for the get_seconds_since_midnight function"""

    def test_correct_number_of_seconds_returned(self, datetime):
        """Test that the number of seconds that have elapsed in the current day since midnight are
        returned."""

        # Test with time being exactly midnight
        datetime.now.return_value.timetuple.return_value = unittest.mock.MagicMock(tm_hour=0,
                                                                                   tm_min=0,
                                                                                   tm_sec=0)
        midnight_response = utils.get_seconds_since_midnight()
        self.assertEquals(midnight_response, 0)

        # Test with a few hours after midnight
        datetime.now.return_value.timetuple.return_value = unittest.mock.MagicMock(tm_hour=3,
                                                                                   tm_min=0,
                                                                                   tm_sec=0)
        two_am_response = utils.get_seconds_since_midnight()
        self.assertEquals(two_am_response, 60 * 60 * 3)

        # Test with a few minutes after midnight
        datetime.now.return_value.timetuple.return_value = unittest.mock.MagicMock(tm_hour=0,
                                                                                   tm_min=5,
                                                                                   tm_sec=0)
        two_am_response = utils.get_seconds_since_midnight()
        self.assertEquals(two_am_response, 60 * 5)

        # Test with a few seconds after midnight
        datetime.now.return_value.timetuple.return_value = unittest.mock.MagicMock(tm_hour=0,
                                                                                   tm_min=0,
                                                                                   tm_sec=5)
        two_am_response = utils.get_seconds_since_midnight()
        self.assertEquals(two_am_response, 5)

        # Test right before midnight
        datetime.now.return_value.timetuple.return_value = unittest.mock.MagicMock(tm_hour=23,
                                                                                   tm_min=59,
                                                                                   tm_sec=59)
        two_am_response = utils.get_seconds_since_midnight()
        self.assertEquals(two_am_response, (60 * 60 * 24) - 1)
