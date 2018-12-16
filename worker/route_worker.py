import configparser
import datetime
import logging
import os.path as path
import threading
import time
from urllib.error import URLError

import py_nextbus

import how_late_is_muni.settings as settings
from worker.models import Arrival, Route, ScheduleClass, ScheduledArrival, Stop
import worker.libs.utils as utils

LOG = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read(path.join(settings.BASE_DIR, 'config.ini'))

class RouteWorker(threading.Thread):
    """Class to manage the predictions and arrivals for a single route."""

    def __init__(self, route_tag, agency, service_class):
        """
        Arguments:
            route_tag: (String) Number or letter of the route.
            agency: (String) Name of the transit agency this route is part of.
            service_class: (String) The current day of the week to use the schedule for, either
                "wkd", "sat", "sun".
        """

        threading.Thread.__init__(self, name='%s worker' % route_tag)

        self.running = False

        self.agency = agency
        self.route = Route.objects.get(tag=route_tag)
        self.service_class = service_class

        self.stops = Stop.objects.filter(route=self.route,
                                         stop_schedule_class__schedule_class__service_class=service_class,
                                         stop_schedule_class__schedule_class__is_active=True,
                                         stop_schedule_class__schedule_class__route=self.route)

        self.nextbus_client = py_nextbus.NextBusClient(output_format='json',
                                                       agency=agency)

        self.update_frequency = int(config.get('worker', 'prediction_update_seconds'))
        self.duplicate_arrival_threshold = int(config.get('worker', 'duplicate_arrival_threshold'))

    def get_arrivals(self, current_predictions, current_predictions_retrieve_time,
                     previous_predictions, previous_predictions_retrieve_time):
        """Determine the arrivals that occurred between the two most recent retrievals of
        predictions for the route.

        Arguments:
            current_predictions: (Dictionary) Nested dictionaries returned by the get_predictions
                method containing the most recent predictions that were retrieved, keyed by stop
                tags -> block IDs -> trip tags, with the number of seconds until the predicted
                arrival as the value.
            current_predictions_retrieve_time: (Integer) Midnight epoch timestamp of when the
                current predictions were retrieved.
            previous_predictions: (Dictionary) Nested dictionaries returned by the get_predictions
                method containing the predictions retrieved prior to the most recent predictions,
                keyed by stop tags -> block IDs -> trip tags, with the number of seconds until the
                predicted arrival as the value.
            previous_predictions: (Integer) Midnight epoch timestamp of when the previous
                predictions were retrieved.

        Returns:
            Dictionary with stop tags as keys and lists of block IDs of arrivals as values. For
            example:
            {
                5001: [
                    2101,
                    2102
                ]
            }
        """

        time_between_retrievals = (current_predictions_retrieve_time -
                                   previous_predictions_retrieve_time)

        # Maximum number of seconds away a vehicle can have been in the previous predictions to
        # consider it to have arrived if it isn't in the most recent predictions, to prevent
        # vehicles that are far from the stop from incorrectly being considered to have arrived at
        # the stop if they disappear from the predictions
        arrival_threshold = 500

        arrivals = {}
        for stop_tag, blocks in previous_predictions.items():
            if stop_tag not in current_predictions:
                LOG.warning('Stop %s is not in the current set of predictions', stop_tag)
                continue

            stop_arrivals = []
            for block_id, trips in blocks.items():
                # If a block ID that was in the previous predictions is not present in the most
                # recent predictions, consider it to have arrived if the earliest predictied
                # arrival time for that block ID is within the arrival threshold, or if the
                # arrivals were not updated for a longer time than the predicted arrival time.
                if block_id not in current_predictions[stop_tag]:
                    next_arrival_time = min(previous_predictions[stop_tag][block_id].values())
                    # Might need to add a time buffer, in case the vehicle was slightly delayed
                    if next_arrival_time < arrival_threshold or \
                            next_arrival_time < time_between_retrievals:
                        stop_arrivals.append(block_id)

                else:
                    for trip_id, arrival_seconds in trips.items():
                        # If a trip ID is in the previous predictions but not in the current
                        # predictions, it is considered to have arrived as long as the predicted
                        # arrival in the previous predictions is below the arrival time threshold,
                        # or if the arrivals have not been updated for a longer time than the
                        # predicted arrival time
                        if trip_id not in current_predictions[stop_tag][block_id] and \
                                (arrival_seconds < arrival_threshold or
                                 time_between_retrievals > arrival_seconds):
                            stop_arrivals.append(block_id)

            if stop_arrivals:
                arrivals[stop_tag] = stop_arrivals

        LOG.debug('Found arrivals: %s', arrivals)
        return arrivals

    def get_predictions(self, stop_tags):
        """Get predictions for multiple stops, and return formatted arrival predictions for those
        stops.

        Arguments:
            stop_tags: (List of strings) List of the tags of the stops on the route to retrieve
                predictions for.

        Returns:
            Nested dictionaries keyed by stop tags -> block IDs -> trip tags, with the number of
            seconds until the predicted arrival as the value. For example:
            {
                5001: {
                    2101: {
                        7895989: 180
                        7895991: 1259
                    }
                    2102: {
                        7895990: 900
                    }
                }
            }
        """

        LOG.debug('Getting predictions')

        stops = [{'route_tag': self.route.tag, 'stop_tag': stop_tag} for stop_tag in stop_tags]
        predictions = self.nextbus_client.get_predictions_for_multi_stops(stops)

        prediction_dict = {}
        for stop in predictions['predictions']:
            stop_predictions = {}
            for direction in utils.ensure_is_list(stop.get('direction', [])):
                for prediction in utils.ensure_is_list(direction.get('prediction', [])):
                    try:
                        block_id = int(prediction['block'])
                    except (ValueError, TypeError):
                        LOG.info('Block ID %s is not an integer', prediction['block'])
                    else:
                        if block_id not in stop_predictions:
                            stop_predictions[block_id] = {}

                        stop_predictions[block_id][int(prediction['tripTag'])] = \
                            int(prediction['seconds'])

            prediction_dict[int(stop['stopTag'])] = stop_predictions

        return prediction_dict

    def get_scheduled_arrival_for_arrival(self, stop_tag, block_id, arrival_time,
                                          scheduled_arrivals):
        """Get the scheduled arrival for an arrival that occurred.

        Arguments:
            stop_tag: (Integer) The tag identifying the stop where the arrival occurred.
            block_id: (Integer) Block ID of the vehicle that arrived at the stop.
            arrival_time: (Intger) Midnight epoch timestamp indicating when the arrival occurred.
            scheduled_arrivals: (List of instances of ScheduledArrivals) The scheduled arrivals for
                the combination of stop and block ID where the arrival occurred.

        Returns:
            Instance of worker.models.ScheduledArrival for the closest scheduled arrival for the
            arrival, or None if there are no scheduled arrivals for the combination of stop and
            block.
        """

        # Some stops only have one scheduled arrival time for a block ID even if there are multiple
        # trips for the block ID that serve the stop, when there is a trip that begins or ends at
        # the stop. To avoid every arrival throughout the day from being compared to the single
        # scheduled arrival time, the arrival will only be compared to the single arrival time if
        # the arrival is within a threshold.
        if len(scheduled_arrivals) == 1:
            if abs(arrival_time - scheduled_arrivals[0].time) <= \
                    (int(config.get('worker', 'single_scheduled_arrival_threshold'))):
                return scheduled_arrivals[0]
            else:
                return None

        closest_arrival = None
        closest_difference = None
        for scheduled_arrival in scheduled_arrivals:
            difference = min([abs(arrival_time - scheduled_arrival.time),
                              # If arrival is before midnight and closest arrival is after midnight
                              abs(arrival_time - scheduled_arrival.time - (60 * 60 * 24)),
                              # If arrival is after midnight and closest arrival is before midnight
                              abs(arrival_time - (scheduled_arrival.time - (60 * 60 * 24)))])
            if closest_difference is  None or difference < closest_difference:
                closest_arrival = scheduled_arrival
                closest_difference = difference
        return closest_arrival

    def get_scheduled_arrivals(self, service_class):
        """Get the scheduled arrivals for the route in the service class for the current day.

        Arguments:
            service_class: (String) The service class for the current day.

        Returns:
            A dictionary with stop tags as keys and dictionaries of arrivals for each block ID on
            the route as values. Each dictionary of arrivals has block IDs as keys and an unsorted
            list of instances of worker.models.ScheduledArrival as values. For example:
            {
                "5001": {
                    2101: [
                        <instance of worker.models.ScheduledArrival>,
                        <instance of worker.models.ScheduledArrival>
                    ]
                }
            }
        """

        LOG.info('Getting scheculed arrivals for service class %s', service_class)

        scheduled_arrivals = ScheduledArrival.objects.filter(
            stop_schedule_class__schedule_class__route__exact=self.route,
            stop_schedule_class__schedule_class__service_class__exact=service_class,
            stop_schedule_class__schedule_class__is_active__exact=True
        )

        scheduled_arrival_dict = {}
        for scheduled_arrival in scheduled_arrivals:
            stop_tag = scheduled_arrival.stop_schedule_class.stop.tag

            if stop_tag not in scheduled_arrival_dict:
                scheduled_arrival_dict[stop_tag] = {}

            if scheduled_arrival.block_id not in scheduled_arrival_dict[stop_tag]:
                scheduled_arrival_dict[stop_tag][int(scheduled_arrival.block_id)] = []

            scheduled_arrival_dict[stop_tag][int(scheduled_arrival.block_id)].append(scheduled_arrival)

        return scheduled_arrival_dict

    def run(self):
        """Run the worker to get arrivals. This will start a loop that performs the following
        actions:
        1. Get arrival predictions for all stops with schedule information on the route.
        2. Determine if any arrivals occurred between the latest predictions and the previously
            retrieved predictions.
        3. If any arrivals were found, save them to the database.
        """

        self.running = True

        scheduled_arrivals = self.get_scheduled_arrivals(service_class=self.service_class)
        stop_tags = [stop.tag for stop in self.stops]

        current_predictions = {}
        current_retrieve_time = time.time()
        while self.running:
            previous_predictions = current_predictions
            previous_retrieve_time = current_retrieve_time

            try:
                current_predictions = self.get_predictions(stop_tags=stop_tags)
            except URLError:
                LOG.exception('Failed to get arrival predictions due to exception')
                time.sleep(self.update_frequency)
                continue

            current_retrieve_time = time.time()

            arrivals = self.get_arrivals(current_predictions=current_predictions,
                                         current_predictions_retrieve_time=current_retrieve_time,
                                         previous_predictions=previous_predictions,
                                         previous_predictions_retrieve_time=previous_retrieve_time)

            if current_retrieve_time - previous_retrieve_time > self.update_frequency * 3:
                LOG.warning('Predictions have not been updated in %d seconds, arrivals will be inaccurate and will not be saved',
                            current_retrieve_time - previous_retrieve_time)

            elif arrivals:
                self.save_arrivals(arrivals=arrivals,
                                   arrival_time=current_retrieve_time,
                                   scheduled_arrivals=scheduled_arrivals)
            else:
                LOG.debug('No arrivals to save')

            time.sleep(self.update_frequency)

        LOG.info('Stopping worker')

    def save_arrivals(self, arrivals, arrival_time, scheduled_arrivals):
        """Save arrivals to the database.

        Arguments:
            arrivals: (Dictionary) Dictionary with stop tags as keys and lists of block IDs of
                arrivals as values.
            arrival_time: (Integer) Unix timestamp indicating the time at which the arrivals
                occurred.
            scheduled_arrivals: (Dictionary) Dictionary with stop tags as keys and dictionaries of
                arrivals for each block ID on the route as values. Each dictionary of arrivals has
                block IDs as keys and an unsorted list of instances of worker.model.ScheduledArrival
                as values.
        """

        arrival_date = datetime.datetime.fromtimestamp(arrival_time)
        arrival_date_start = arrival_date - datetime.timedelta(hours=arrival_date.hour,
                                                               minutes=arrival_date.minute,
                                                               seconds=arrival_date.second,
                                                               microseconds=arrival_date.microsecond)
        midnight_epoch_arrival = arrival_time - arrival_date_start.timestamp()

        for stop_tag, block_ids in arrivals.items():
            for block_id in block_ids:
                if stop_tag in scheduled_arrivals and block_id in scheduled_arrivals[stop_tag]:
                    scheduled_arrival = \
                        self.get_scheduled_arrival_for_arrival(stop_tag=stop_tag,
                                                               block_id=block_id,
                                                               arrival_time=midnight_epoch_arrival,
                                                               scheduled_arrivals=scheduled_arrivals[stop_tag][block_id])

                    # Only save arrivals that can be associated with a scheduled arrival
                    if scheduled_arrival is not None:
                        # If there was already an arrival at the same stop for the same scheduled
                        # arrival, consider the two arrivals to be duplicates if they are within a
                        # certain threshold, and update the the arrival time to the current
                        # arrival's time.
                        Arrival.objects.update_or_create(
                            stop=scheduled_arrival.stop_schedule_class.stop,
                            scheduled_arrival=scheduled_arrival,
                            time__gte=arrival_time - self.duplicate_arrival_threshold,
                            defaults={
                                'time': arrival_time,
                                'difference': midnight_epoch_arrival - scheduled_arrival.time
                            }
                        )
                else:
                    LOG.warning('Block ID %s is not in scheduled arrivals' % block_id)
