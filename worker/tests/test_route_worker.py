"""Tests for the RouteWorker class"""

from copy import deepcopy
import random
import string
import unittest
import unittest.mock

from django.test import TestCase

from worker.models import Arrival, Route, ScheduledArrival, ScheduleClass, Stop, StopScheduleClass
import worker.route_worker as route_worker

def _get_random_string(length):
    """Get a string of a given length containing randomly selected lowercase letters.

    Arguments:
        length (Integer) Length of the string to create.

    Returns:
        A string containing random lowercase letters.
    """

    return ''.join(random.choices(string.ascii_lowercase, k=length))

@unittest.mock.patch('worker.route_worker.RouteWorker.__init__', return_value=None)
class TestGetArrivals(unittest.TestCase):
    """Tests for the get_arrivals method in the RouteWorker class."""

    def test_arrival_returned_if_block_id_not_in_current_predictions_and_time_below_threshold(
            self, _):
        """Test that an arrival is returned if a block ID is in the previous predictions but is not
        in the most recent predictions, and the earliest predicted arrival time for the block ID is
        less than the arrival time threshold."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 1
                }
            }
        }
        current_predictions = {
            "1234": {}
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=12300)

        self.assertEquals(response, {
            "1234": [
                5678
            ]
        })

    def test_arrival_returned_if_block_id_not_in_current_predictions_and_time_below_retrieval_time(
            self, _):
        """Test that an arrival is returned if a block ID is in the previous predictions but is not
        in the most recent predictions, and the earliest predicted arrival time for the block ID is
        above the arrival time threshold but below the amount of time between when the most recent
        and previous predictions were retrieved."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 1000
                }
            }
        }
        current_predictions = {
            "1234": {}
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=10000)

        self.assertEquals(response, {
            "1234": [
                5678
            ]
        })

    def test_no_arrivals_returned_if_block_id_not_in_current_predictions_and_time_above_thresholds(
            self, _):
        """Test that no arrivals are returned if a block ID is in the previous predictions but is
        not in the most recent predictions, and the earliest predicted arrival time for the block ID
        is above both the arrival time threshold and the amount of time between when the most recent
        and previous predictions were retrieved."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 9999
                }
            }
        }
        current_predictions = {
            "1234": {}
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=12344)

        self.assertEquals(response, {})

    def test_arrival_returned_if_trip_id_not_in_current_predictions_and_time_below_threshold(
            self, _):
        """Test that an arrival is returned if a trip ID is in the previous predictions but is not
        in the most recent predictions, and the predicted arrival time for that trip ID was less
        than the arrival time threshold."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 1
                }
            }
        }
        current_predictions = {
            "1234": {
                5678: {}
            }
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=12300)

        self.assertEquals(response, {
            "1234": [
                5678
            ]
        })

    def test_arrival_returned_if_trip_id_not_in_current_predictions_and_time_below_retrieval_time(
            self, _):
        """Test that an arrival is returned if a trip ID is in the previous predictions but is not
        in the most recent predictions, and the predicted arrival time for that trip ID is above the
        arrival time threshold but below the amount of time between when the most recent and
        previous predictions were retrieved."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 1000
                }
            }
        }
        current_predictions = {
            "1234": {
                5678: {}
            }
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=10000)

        self.assertEquals(response, {
            "1234": [
                5678
            ]
        })

    def test_no_arrivals_returned_if_trip_id_not_in_current_predictions_and_time_above_thresholds(
            self, _):
        """Test that no arrivals are returned if a trip ID is in the previous predictions but is not
        in the most recent predictions and the predicted arrival time for that trip ID is above both
        the arrival time threshold and the amount of time between when the most recent and previous
        predictions were retrieved."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 9999
                }
            }
        }
        current_predictions = {
            "1234": {
                5678: {}
            }
        }

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=12344)

        self.assertEquals(response, {})

    def test_no_arrivals_returned_if_all_block_ids_and_trip_ids_in_current_predictions(self, _):
        """Test that no arrivals are returned if all block IDs and trip IDs from the previous
        predictions are also in the most recent predictions."""

        previous_predictions = {
            "1234": {
                5678: {
                    123: 999,
                    456: 1999
                },
                6789: {
                    359: 5555,
                    246: 8888
                }
            }
        }
        current_predictions = deepcopy(previous_predictions)

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_arrivals(current_predictions=current_predictions,
                                       current_predictions_retrieve_time=12345,
                                       previous_predictions=previous_predictions,
                                       previous_predictions_retrieve_time=12344)

        self.assertEquals(response, {})

@unittest.mock.patch('worker.route_worker.RouteWorker.__init__', return_value=None)
class TestGetScheduledArrivalForArrival(unittest.TestCase):
    """Tests for the get_scheduled_arrival_for_arrival in the RouteWorker class."""

    def test_none_returned_if_block_has_no_scheduled_arrivals(self, _):
        """Test that None is returned if the arrival was made by a vehicle with a block ID that is
        in the scheduled arrivals but does not have any scheduled arrivals."""

        stop_tag = 'buz'
        block_id = 1234

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')

        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=10,
                                                            scheduled_arrivals=[])
        self.assertIs(response, None)

    def test_exact_match_arrival_time_returned(self, _):
        """Test that when the arrival time is exactly the same as a scheduled arrival time for
        the combination of stop and block ID, the scheduled arrival for that exact is returned."""

        stop_tag = 'buz'
        block_id = 1234

        arrival_time = 10
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time - 1),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time + 1),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time),
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[2])

    def test_earlier_arrival_time_returned(self, _):
        """Test that when the closest scheduled arrival time for an arrival is earlier than the
        arrival time, the earlier scheduled arrival is returned."""

        stop_tag = 'buz'
        block_id = 1234

        arrival_time = 10
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time - 1),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time + 2)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[0])


    def test_later_arrival_time_returned(self, _):
        """Test that when the closest scheduled arrival time for an arrival is later than the
        arrival time, the later scheduled arrival is returned."""

        stop_tag = 'buz'
        block_id = 1234

        arrival_time = 10
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time - 2),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time + 1)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[1])

    def test_time_after_midnight_returned(self, _):
        """Test that when an arrival time is just before midnight and the closest scheduled arrival
        is after midnight, the correct scheduled arrival is returned."""

        stop_tag = 'buz'
        block_id = 1234

        # Time right before midnight
        arrival_time = (60 * 60 * 24) - 1
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=60),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time - 120),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=15)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[2])

    def test_time_before_midnight_returned(self, _):
        """Test that when an arrival time is just after midnight and the closest scheduled arrival
        is before midnight, the correct scheduled arrival is returned."""

        stop_tag = 'buz'
        block_id = 1234

        # Time right after midnight
        arrival_time = 1
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=120),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=(60 * 60 * 24) - 60),
            unittest.mock.MagicMock(spec=ScheduledArrival, time=(60 * 60 * 24) - 120)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agency='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                            block_id=block_id,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[1])

    @unittest.mock.patch('worker.route_worker.config.get', autospec=True)
    def test_arrival_returned_if_block_id_has_one_scheduled_arrival_and_time_within_threshold(
        self, config_get, _):
        """Test that if there is only one scheduled arrival for the block ID and stop, that
        scheduled arrival is returned if the difference between the scheduled arrival time and the
        actual arrival time is less than the threshold for counting arrivals at stops with only one
        scheduled arrival for the block ID."""

        threshold = 100
        config_get.return_value = threshold

        arrival_time = 1000
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time + threshold - 1)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agencey='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag='buz',
                                                            block_id=1234,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertEquals(response, scheduled_arrivals[0])

    @unittest.mock.patch('worker.route_worker.config.get', autospec=True)
    def test_none_returned_if_block_id_has_one_scheduled_arrival_and_time_greater_than_threshold(
        self, config_get, _):
        """Test that if there is only one scheduled arrival for the block ID and stop, None is
        returned if the difference between the scheduled arrival time and the actual arrival time
        is higher than the threshold for counting arrivals at stops with only one scheduled arrival
        for the block ID."""

        threshold = 100
        config_get.return_value = threshold

        arrival_time = 1000
        scheduled_arrivals = [
            unittest.mock.MagicMock(spec=ScheduledArrival, time=arrival_time + threshold + 1)
        ]

        worker = route_worker.RouteWorker(route_tag='foo',
                                          agencey='bar',
                                          service_class='baz')
        response = worker.get_scheduled_arrival_for_arrival(stop_tag='buz',
                                                            block_id=1234,
                                                            arrival_time=arrival_time,
                                                            scheduled_arrivals=scheduled_arrivals)
        self.assertIsNone(response)

class TestGetScheduledArrivals(TestCase):
    """Tests for the get_scheduled_arrivals method in the RouteWorker class."""

    def setUp(self):
        """Setup data in the database with random values for each test."""

        self.route = Route(tag=_get_random_string(length=5),
                           title=_get_random_string(length=16))
        self.route.save()
        self.stop = Stop(tag=random.randint(1, 10000),
                         title=_get_random_string(length=16),
                         route=self.route)
        self.stop.save()

        # Setup a ScheduleClass where is_active is True, and a related StopScheduleClass and
        # ScheduleArrival
        self.active_schedule_class = ScheduleClass(route=self.route,
                                                   direction=_get_random_string(length=8),
                                                   service_class=_get_random_string(length=3),
                                                   name=_get_random_string(length=16),
                                                   is_active=True)
        self.active_schedule_class.save()
        self.active_stop_schedule_class = \
            StopScheduleClass(stop=self.stop,
                              schedule_class=self.active_schedule_class,
                              stop_order=random.randint(1, 20))
        self.active_stop_schedule_class.save()
        self.active_scheduled_arrival = \
            ScheduledArrival(stop_schedule_class=self.active_stop_schedule_class,
                             block_id=random.randint(1, 9999),
                             time=random.randint(1000, 1000000))
        self.active_scheduled_arrival.save()

        # Setup a ScheduleClass where is_active is False, and a related StopScheduleClass and
        # ScheduleArrival
        self.inactive_schedule_class = ScheduleClass(route=self.route,
                                                     direction=_get_random_string(length=8),
                                                     service_class=_get_random_string(length=3),
                                                     name=_get_random_string(length=16),
                                                     is_active=False)
        self.inactive_schedule_class.save()
        self.inactive_stop_schedule_class = \
            StopScheduleClass(stop=self.stop,
                              schedule_class=self.inactive_schedule_class,
                              stop_order=random.randint(1, 20))
        self.inactive_stop_schedule_class.save()
        self.inactive_scheduled_arrival = \
            ScheduledArrival(stop_schedule_class=self.inactive_stop_schedule_class,
                             block_id=random.randint(1, 9999),
                             time=random.randint(1000, 1000000))
        self.inactive_scheduled_arrival.save()

    def test_arrivals_for_inactive_schedule_classes_not_returned(self):
        """Test that scheduled arrivals associated with inactive schedule classes are not returned.
        """

        worker = route_worker.RouteWorker(route_tag=self.route.tag,
                                          agency='foo',
                                          service_class=self.inactive_schedule_class.service_class)
        result = \
            worker.get_scheduled_arrivals(service_class=self.inactive_schedule_class.service_class)

        self.assertEquals(result, {})

    def test_formatted_arrivals_returned(self):
        """Test that the scheduled arrivals are returned in the expected format."""

        block_id = self.active_scheduled_arrival.block_id

        # Create a scheduled arrival with a different block ID than the one already setup in the
        # database
        second_arrival = \
            ScheduledArrival(stop_schedule_class=self.active_stop_schedule_class,
                             block_id=block_id - 1,
                             time=random.randint(1000, 1000000))
        second_arrival.save()

        # Create another scheduled arrival with a different block ID than the one already setup in
        # the database
        third_arrival = \
            ScheduledArrival(stop_schedule_class=self.active_stop_schedule_class,
                             block_id=block_id + 1,
                             time=random.randint(1000, 1000000))
        third_arrival.save()

        worker = route_worker.RouteWorker(route_tag=self.route.tag,
                                          agency='foo',
                                          service_class=self.active_schedule_class.service_class)
        result = \
            worker.get_scheduled_arrivals(service_class=self.active_schedule_class.service_class)

        self.assertEquals(result, {
            self.stop.tag: {
                self.active_scheduled_arrival.block_id: [
                    self.active_scheduled_arrival
                ],
                second_arrival.block_id: [
                    second_arrival
                ],
                third_arrival.block_id: [
                    third_arrival
                ]
            }
        })

@unittest.mock.patch('worker.route_worker.py_nextbus.NextBusClient')
class TestGetPredictions(TestCase):
    """Tests for the get_predictions method in the RouteWorker class."""

    def test_stops_passed_to_client(self, nextbus_client):
        """Test that the stops in the arguments are passed to the get_predictions_for_multi_stops
        method in the NextBus client in the expected format."""

        test_route = Route(tag='foo',
                           title='bar')
        test_route.save()
        agency = 'baz'
        worker = route_worker.RouteWorker(route_tag=test_route.tag,
                                          agency=agency,
                                          service_class='buz')

        stops = [1234, 5678, 8910]
        worker.get_predictions(stops)

        nextbus_client.assert_called_once_with(output_format='json',
                                               agency=agency)
        nextbus_client.return_value.get_predictions_for_multi_stops.assert_called_once_with([
            {
                'stop_tag': stops[0],
                'route_tag': test_route.tag
            },
            {
                'stop_tag': stops[1],
                'route_tag': test_route.tag
            },
            {
                'stop_tag': stops[2],
                'route_tag': test_route.tag
            },
        ])

    def test_formatted_response_returned(self, nextbus_client):
        """Test that the response from the NextBus API is formatted into the expected structure and
        returned."""

        nextbus_client.return_value.get_predictions_for_multi_stops.return_value = {
            'predictions': [
                {
                    'stopTag': '5684',
                    'direction': [
                        {
                            'prediction': [
                                {
                                    'seconds': '120',
                                    'block': '3804',
                                    'tripTag': '123456'
                                },
                                {
                                    'seconds': '1250',
                                    'block': '3814',
                                    'tripTag': '123457'
                                },
                                {
                                    'seconds': '3157',
                                    'block': '3804',
                                    'tripTag': '123460'
                                },
                            ]
                        },
                        {
                            'prediction': [
                                {
                                    'seconds': '855',
                                    'block': '3815',
                                    'tripTag': '123458'
                                },
                                {
                                    'seconds': '1891',
                                    'block': '3812',
                                    'tripTag': '123459'
                                }
                            ]
                        }
                    ],
                },
                {
                    'stopTag': '4757',
                    'direction': [
                        {
                            'prediction': [
                                {
                                    'seconds': '359',
                                    'block': '3804',
                                    'tripTag': '123456'
                                },
                                {
                                    'seconds': '1511',
                                    'block': '3814',
                                    'tripTag': '123457'
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        test_route = Route(tag='foo',
                           title='bar')
        test_route.save()
        worker = route_worker.RouteWorker(route_tag=test_route.tag,
                                          agency='baz',
                                          service_class='buz')
        response = worker.get_predictions([1234])

        expected_response = {
            5684: {
                3804: {
                    123456: 120,
                    123460: 3157
                },
                3814: {
                    123457: 1250
                },
                3815: {
                    123458: 855
                },
                3812: {
                    123459: 1891
                }
            },
            4757: {
                3804: {
                    123456: 359
                },
                3814: {
                    123457: 1511
                }
            }
        }

        self.assertEqual(response, expected_response)

@unittest.mock.patch('worker.route_worker.RouteWorker.get_scheduled_arrival_for_arrival')
class TestSaveArrivals(TestCase):
    """Tests for the save_arrivals method in the RouteWorker class."""

    def setUp(self):
        """Setup data in the database with random values for each test."""

        self.route = Route(tag=_get_random_string(length=5),
                           title=_get_random_string(length=16))
        self.route.save()
        self.stop = Stop(tag=random.randint(1, 10000),
                         title=_get_random_string(length=16),
                         route=self.route)
        self.stop.save()

        self.schedule_class = ScheduleClass(route=self.route,
                                            direction=_get_random_string(length=8),
                                            service_class=_get_random_string(length=3),
                                            name=_get_random_string(length=16),
                                            is_active=True)
        self.schedule_class.save()
        self.stop_schedule_class = StopScheduleClass(stop=self.stop,
                                                     schedule_class=self.schedule_class,
                                                     stop_order=random.randint(1, 20))
        self.stop_schedule_class.save()

    def test_arrivals_saved_to_database(self, get_scheduled_arrival_for_arrival):
        """Test that the details of the provided arrivals are saved to the database."""

        first_block_id = random.randint(1, 9999)
        second_block_id = random.randint(1, 9999)
        first_scheduled_arrival = ScheduledArrival(stop_schedule_class=self.stop_schedule_class,
                                                   block_id=first_block_id,
                                                   time=1234567)
        second_scheduled_arrival = ScheduledArrival(stop_schedule_class=self.stop_schedule_class,
                                                    block_id=second_block_id,
                                                    time=3456789)

        scheduled_arrivals = {
            self.stop.tag: {
                first_block_id: [
                    first_scheduled_arrival
                ],
                second_block_id: [
                    second_scheduled_arrival
                ]
            }
        }
        first_scheduled_arrival.save()
        second_scheduled_arrival.save()

        get_scheduled_arrival_for_arrival.side_effect = \
            [first_scheduled_arrival, second_scheduled_arrival]

        arrivals = {
            self.stop.tag: [
                first_scheduled_arrival.block_id,
                second_scheduled_arrival.block_id
            ]
        }
        arrival_time = 678910

        worker = route_worker.RouteWorker(route_tag=self.route.tag,
                                          agency='foo',
                                          service_class='bar')

        worker.save_arrivals(arrivals=arrivals,
                             arrival_time=arrival_time,
                             scheduled_arrivals=scheduled_arrivals)

        # Try to get both Arrivals that should have been added to the database
        Arrival.objects.get(stop=self.stop,
                            scheduled_arrival=first_scheduled_arrival,
                            time=arrival_time)
        Arrival.objects.get(stop=self.stop,
                           scheduled_arrival=second_scheduled_arrival,
                           time=arrival_time)

    def test_arrival_not_saved_if_scheduled_arrival_does_not_exist(
            self, get_scheduled_arrival_for_arrival):
        """Test that arrivals are not saved to the database if no scheduled arrival time could be
        found for an arrival."""

        get_scheduled_arrival_for_arrival.return_value = None
        stop_tag = 1234
        block_id = 5678
        arrivals = {
            stop_tag: [
                block_id
            ]
        }
        scheduled_arrivals = {
            stop_tag: {
                block_id: [
                    unittest.mock.MagicMock()
                ],
            }
        }

        num_arrivals_before = Arrival.objects.count()

        worker = route_worker.RouteWorker(route_tag=self.route.tag,
                                          agency='foo',
                                          service_class='bar')

        worker.save_arrivals(arrivals=arrivals,
                             arrival_time=678910,
                             scheduled_arrivals=scheduled_arrivals)

        self.assertEquals(Arrival.objects.count(), num_arrivals_before)
