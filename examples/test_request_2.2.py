#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""test_request_2.2.py: Request the metrics calculation in the online manner without interfacing the SUT."""

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
import message_evarilos_engine_type2_pb2
import experiment_results_pb2

# Define the communication with ECE (EVARILOS Central Engine)
# Message Type 2: Online calculaton of metrics

apiURI_ECE = 'http://localhost:5002/'
experiment = message_evarilos_engine_type2_pb2.ece_type2()

experiment.timestamp_utc = int(time.time())                                 # When did the experiment start?
experiment.experiment_label = 'Test_experiment'                             # What is the name of the experiment?
experiment.request_raw_data = False 		       		                    # Request raw data from the SUT?
experiment.request_estimates = False
experiment.store_metrics = True 				                            # Storing metrics?
experiment.request_power_consumption = False 		       	                # Request power consumption?
	
# Storing metrics

experiment.metrics_storage_URI = 'http://localhost:5001/';	                # URI for storing the processed data
experiment.metrics_storage_database = 'fingerprinting';		                # Name of the database for storing the results
experiment.metrics_storage_collection = 'test';                             # Name of the collection for storing the results  

# Define the scenario of the experiment

experiment.scenario.testbed_label = 'TWIST' 				                      # Label the testbed 
experiment.scenario.testbed_description = 'Berlin Office Bricked walls'           # Give the description
experiment.scenario.experiment_description = 'Test experiment'                    # Describe your experiment
experiment.scenario.sut_description = 'MacBook TP LINK routers fingerprinting'    # Describe your SUT
experiment.scenario.receiver_description = 'MacBook Airport'                      # Describe your receiver(s)
experiment.scenario.sender_description = 'TP LINK routers beaconing'              # Describe your sender(s)
experiment.scenario.interference_description = 'No interference'                  # Describe interference scenario

experiment.ground_truth.point_id = 1
experiment.ground_truth.localized_node_id = 1
experiment.ground_truth.true_coordinate_x = 3.0
experiment.ground_truth.true_coordinate_y = 3.1
experiment.ground_truth.true_coordinate_z = 3.4
experiment.ground_truth.true_room_label = 'FT123'

experiment.estimate.est_coordinate_x = 4.1
experiment.estimate.est_coordinate_y = 4.1
experiment.estimate.est_coordinate_z = 4.1
experiment.estimate.est_room_label = 'FT113'
experiment.estimate.latency = 20.123
experiment.estimate.power_consumption = 130.72

# Send your data to the ECE (EVARILOS Central Engine) service
# Serialize your protobuffer to binary string 

experiment_string = experiment.SerializeToString()

# Send your data to over HTTP to the ECE service	

req = RequestWithMethod(apiURI_ECE + 'evarilos/ece/v1.0/add_one_location', 'POST', headers={"Content-Type": "application/x-protobuf"}, data = experiment_string)
resp = urllib2.urlopen(req)
response = json.loads(resp.read())
print json.dumps(response)