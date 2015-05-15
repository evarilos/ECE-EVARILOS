#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""test_request1.py: Request the metrics calculation of the indoor localization experiment 
   performed offline - send a set of ground-truths and estimates, the service responds with
   the metrics.
"""

__author__ = "Filip Lemic"
__copyright__ = "Copyright 2015, EVARILOS Project"

__version__ = "1.0.0"
__maintainer__ = "Filip Lemic"
__email__ = "lemic@tkn.tu-berlin.de"
__status__ = "Development"

import sys
import time
import urllib2
import json
from generateURL import RequestWithMethod
import message_evarilos_engine_type1_pb2
import experiment_results_pb2

apiURI_ECE = 'http://localhost:5002/'

experiment = message_evarilos_engine_type1_pb2.ece_type1()

# Set the parameters of your experiment
experiment.timestamp_utc = int(time.time())                      # When did the experiment start?
experiment.experiment_label = 'Test_Experiment'                  # What is the name of the experiment?
experiment.metrics_storage_URI = 'http://localhost:5001/'        # Where do you want to store the evaluation data?
experiment.metrics_storage_database = 'fingerprinting'		     # Name of the database?
experiment.metrics_storage_collection = 'test' 		             # Name of the collection?
experiment.store_metrics = False	           		             # Store metrics?	

# Give the set of measurment locations

# Location 1
location1 = experiment.locations.add()
location1.point_id = 1
location1.localized_node_id = 1
location1.true_coordinate_x = 1
location1.true_coordinate_y = 1
location1.true_coordinate_z = 1
location1.true_room_label = 'Room_1'
location1.est_coordinate_x = 1.1
location1.est_coordinate_y = 1.01
location1.est_coordinate_z = 1.9
location1.est_room_label = 'Room_1_1'
location1.latency = 12.10
location1.power_consumption = 2.12

# Location 2
location2 = experiment.locations.add()
location2.point_id = 2
location2.localized_node_id = 2
location2.true_coordinate_x = 2
location2.true_coordinate_y = 2
location2.true_coordinate_z = 2
location2.true_room_label = 'Room_2'
location2.est_coordinate_x = 2.1
location2.est_coordinate_y = 2.2
location2.est_coordinate_z = 2.9
location2.est_room_label = 'Room_2'
location2.latency = 11.15
location2.power_consumption = 1.87

# Location 3
location2 = experiment.locations.add()
location2.point_id = 3
location2.localized_node_id = 3
location2.true_coordinate_x = 3
location2.true_coordinate_y = 3
location2.true_coordinate_z = 3
location2.true_room_label = 'Room_3'
location2.est_coordinate_x = 3.3
location2.est_coordinate_y = 4.2
location2.est_coordinate_z = 1.9
location2.est_room_label = 'Room_3'
location2.latency = 15.15
location2.power_consumption = 1.99

# Define the scenario of the experiment
experiment.scenario.testbed_label = 'dummy' 			 # Label the testbed 
experiment.scenario.testbed_description = 'dummy'        # Give the description
experiment.scenario.experiment_description = 'dummy'     # Describe your experiment
experiment.scenario.sut_description = 'dummy'            # Describe your SUT
experiment.scenario.receiver_description = 'dummy'       # Describe your receiver(s)
experiment.scenario.sender_description = 'dummy'         # Describe your sender(s)
experiment.scenario.interference_description = 'dummy'   # Describe interference scenario
  
# Send your data to the ECE (EVARILOS Central Engine) service
# Serialize your protobuffer to binary string 
experiment_string = experiment.SerializeToString()
	
# Send your data to over HTTP to the ECE service	
req = RequestWithMethod(apiURI_ECE + 'evarilos/ece/v1.0/calculate_and_store_metrics', 'POST', headers={"Content-Type": "application/x-protobuf"}, data = experiment_string)
resp = urllib2.urlopen(req)
response = json.loads(resp.read())
print json.dumps(response)
