#!/usr/bin/env python

"""EVARILOS Central Engine - Calculation of metrics for indoor localization performance benchmarking."""

__author__ = "Filip Lemic"
__copyright__ = "Copyright 2015, EVARILOS Project"

__version__ = "1.0.0"
__maintainer__ = "Filip Lemic"
__email__ = "lemic@tkn.tu-berlin.de"
__status__ = "Development"

import sys
import urllib
import urllib2
import json
import time
import math
import numpy
import datetime
import protobuf_json
from flask import url_for
from datetime import timedelta
import message_evarilos_engine_type1_pb2
import message_evarilos_engine_type2_pb2
import message_evarilos_engine_type1_presentation_pb2
import message_evarilos_engine_type2_presentation_pb2
import experiment_results_pb2
from flask import Flask, request, jsonify
from generateURL import RequestWithMethod
from flask import make_response, request, current_app
from functools import update_wrapper

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            try:
                h['Access-Control-Allow-Methods'] = get_methods()
            except:
                h['Access-Control-Allow-Methods'] = 'OPTIONS'
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

#################################################################################################
### Task Listing
#################################################################################################

app = Flask(__name__)

@app.route("/")
@crossdomain(origin='*')
def hello():
    response = {'EVARILOS Central Engine': 'This is a prototype of the ECE (EVARILOS Cenatral Engine) service for the EVARILOS project',
                'Description of message types': url_for("messages", _external = True)}
    return json.dumps(response)


#######################################################################################################
# Task 1: Get the list of all message descriptions
#######################################################################################################
@app.route('/evarilos/ece/v1.0', methods = ['GET'])
@crossdomain(origin='*')
def messages():
    message_list = {}
    message_list['Message Type 1'] = {}
    message_list['Message Type 1']['URL'] = url_for("type1_present", _external = True)
    message_list['Message Type 1']['Description'] = "This message is used when one has a set of evaluated locations (at least ground truth + location estimate) and wants to use ECE service to calculate and optionally store metrics."
    message_list['Message Type 1']['Usage'] = url_for("figure1", _external = True)
    message_list['Message Type 2'] = {}
    message_list['Message Type 2']['URL'] = url_for("type3_present", _external = True)
    message_list['Message Type 2']['Description'] = "This message is used when one wants to run experiments and calculation of metrics in the real time."
    message_list['Message Type 2']['Usage'] = url_for("figure3", _external = True)
    return json.dumps(message_list)


@app.route('/evarilos/ece/v1.0/type1/usage')
@crossdomain(origin='*')
def figure1():
    with open('figures/type1.jpg', 'rb') as image_file:
        def wsgi_app(environ, start_response):
            start_response('200 OK', [('Content-type', 'image/jpeg')])
            return image_file.read()
        return make_response(wsgi_app)

@app.route('/evarilos/ece/v1.0/type2/usage')
@crossdomain(origin='*')
def figure3():
    with open('figures/type2.jpg', 'rb') as image_file:
        def wsgi_app(environ, start_response):
            start_response('200 OK', [('Content-type', 'image/jpeg')])
            return image_file.read()
        return make_response(wsgi_app)



#################################################################################################
### Type 1 Communication: Calculating and Storing Metrics
#################################################################################################
@app.route("/evarilos/ece/v1.0/calculate_and_store_metrics", methods=['POST'])
@crossdomain(origin='*')
def type1():
    
    try:
        experiment = message_evarilos_engine_type1_pb2.ece_type1()
        experiment.ParseFromString(request.data)
    except:
        return json.dumps('Experiment is not well defined!')

    experiment_results = experiment_results_pb2.Experiment()
    localization_error_2D = {}
    localization_error_3D = {}
    latency = {} 
    power_consumption = {}
    number_of_points = 0
    number_of_good_rooms = {}

    for location in experiment.locations:
        number_of_points += 1
        measurement_location = experiment_results.locations.add()
        measurement_location.point_id = location.point_id
        try:
            measurement_location.localized_node_id = location.localized_node_id
        except:
            time.sleep(0)
        measurement_location.true_coordinate_x = x1 = location.true_coordinate_x
        measurement_location.true_coordinate_y = y1 = location.true_coordinate_y
        measurement_location.est_coordinate_x = x2 = location.est_coordinate_x
        measurement_location.est_coordinate_y = y2 = location.est_coordinate_y
        measurement_location.localization_error_2D = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2))
        localization_error_2D[number_of_points] = measurement_location.localization_error_2D
        try:
            measurement_location.true_coordinate_z = z1 = location.true_coordinate_z
            measurement_location.est_coordinate_z = z2 = location.est_coordinate_z
            measurement_location.localization_error_3D = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2) + math.pow((z1-z2), 2))
            localization_error_3D[number_of_points] = measurement_location.localization_error_3D
        except:
            time.sleep(0)
        try:
            measurement_location.true_room_label = room1 = location.true_room_label
            measurement_location.est_room_label = room2 = location.est_room_label
            if room1.strip() == room2.strip():
                measurement_location.localization_correct_room = 1
                number_of_good_rooms[number_of_points] = 1
            else:
                measurement_location.localization_correct_room = 0
                number_of_good_rooms[number_of_points] = 0
        except:
            time.sleep(0)
        try:
            measurement_location.latency = location.latency
            latency[number_of_points] = location.latency
        except:
            time.sleep(0)
        try:
            measurement_location.power_consumption = location.power_consumption
            power_consumption[number_of_points] = location.power_consumption
        except:
            time.sleep(0)

    experiment_results.primary_metrics.accuracy_error_2D_average = float(sum(localization_error_2D.values()))/number_of_points
    experiment_results.primary_metrics.accuracy_error_2D_min = min(localization_error_2D.values())
    experiment_results.primary_metrics.accuracy_error_2D_max = max(localization_error_2D.values())
    experiment_results.primary_metrics.accuracy_error_2D_variance = numpy.var(localization_error_2D.values())
    experiment_results.primary_metrics.accuracy_error_2D_median = numpy.median(localization_error_2D.values())
    experiment_results.primary_metrics.accuracy_error_2D_75_percentile = numpy.percentile(localization_error_2D.values(), 75)
    experiment_results.primary_metrics.accuracy_error_2D_90_percentile = numpy.percentile(localization_error_2D.values(), 90)
    experiment_results.primary_metrics.accuracy_error_2D_rms = math.sqrt( (1 / float(number_of_points)) * numpy.sum( numpy.power( localization_error_2D.values(), 2)))

    if len(localization_error_3D) != 0:
         experiment_results.primary_metrics.accuracy_error_3D_average = float(sum(localization_error_3D.values()))/number_of_points
         experiment_results.primary_metrics.accuracy_error_3D_min = min(localization_error_3D.values())
         experiment_results.primary_metrics.accuracy_error_3D_max = max(localization_error_3D.values())
         experiment_results.primary_metrics.accuracy_error_3D_variance = numpy.var(localization_error_3D.values())
         experiment_results.primary_metrics.accuracy_error_3D_median = numpy.median(localization_error_3D.values())
         experiment_results.primary_metrics.accuracy_error_3D_75_percentile = numpy.percentile(localization_error_3D.values(), 75)
         experiment_results.primary_metrics.accuracy_error_3D_90_percentile = numpy.percentile(localization_error_3D.values(), 90)
         experiment_results.primary_metrics.accuracy_error_3D_rms = math.sqrt( (1 / float(number_of_points)) * numpy.sum( numpy.power( localization_error_3D.values(), 2)))

    if len(number_of_good_rooms) != 0: 
        experiment_results.primary_metrics.room_accuracy_error_average = float(sum(number_of_good_rooms.values()))/number_of_points
    if len(latency) != 0:
        experiment_results.primary_metrics.latency_average = float(sum(latency.values()))/number_of_points
        experiment_results.primary_metrics.latency_min = min(latency.values())
        experiment_results.primary_metrics.latency_max = max(latency.values())
        experiment_results.primary_metrics.latency_variance = numpy.var(latency.values())
        experiment_results.primary_metrics.latency_median = numpy.median(latency.values())
        experiment_results.primary_metrics.latency_75_percentile = numpy.percentile(latency.values(), 75)
        experiment_results.primary_metrics.latency_90_percentile = numpy.percentile(latency.values(), 90)
        experiment_results.primary_metrics.latency_rms = math.sqrt( (1 / float(number_of_points)) * numpy.sum( numpy.power( latency.values(), 2)))
    if len(power_consumption) != 0:
        experiment_results.primary_metrics.power_consumption_average = float(sum(power_consumption.values()))/number_of_points
        experiment_results.primary_metrics.power_consumption_median = numpy.median(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_min = min(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_max = max(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_variance = numpy.var(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_75_percentile = numpy.percentile(power_consumption.values(), 75)
        experiment_results.primary_metrics.power_consumption_90_percentile = numpy.percentile(power_consumption.values(), 90)
        experiment_results.primary_metrics.power_consumption_rms = math.sqrt( (1 / float(number_of_points)) * numpy.sum( numpy.power( power_consumption.values(), 2)))
    else:
        try:
            experiment_results.primary_metrics.power_consumption_average = experiment.power_consumption_per_experiment
        except:
            time.sleep(0)
    
    experiment_results.scenario.testbed_label = experiment.scenario.testbed_label
    experiment_results.scenario.testbed_description = experiment.scenario.testbed_description
    experiment_results.scenario.experiment_description = experiment.scenario.experiment_description
    experiment_results.scenario.sut_description = experiment.scenario.sut_description
    experiment_results.scenario.receiver_description = experiment.scenario.receiver_description 
    experiment_results.scenario.sender_description = experiment.scenario.sender_description  
    experiment_results.scenario.interference_description = experiment.scenario.interference_description
    experiment_results.timestamp_utc = experiment.timestamp_utc
    experiment_results.experiment_label = experiment.experiment_label

    obj = json.dumps(protobuf_json.pb2json(experiment_results))

    response = {}
    if experiment.store_metrics is True:
        apiURL_metrics = experiment.metrics_storage_URI

        db_id = experiment.metrics_storage_database
        req = urllib2.Request(apiURL_metrics + 'evarilos/metrics/v1.0/database', headers={"Content-Type": "application/json"}, data = db_id)
        resp = urllib2.urlopen(req)
        coll_id = experiment.metrics_storage_collection
        req = RequestWithMethod(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id  + '/experiment', 'POST', headers={"Content-Type": "application/json"}, data = coll_id)
        resp = urllib2.urlopen(req)       
        req = urllib2.Request(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id + '/experiment/' + coll_id, headers={"Content-Type": "application/json"}, data = obj)
        resp = urllib2.urlopen(req)
    
    response = protobuf_json.pb2json(experiment_results)
    
    return json.dumps(response)


#################################################################################################
### Type 2 Communication: Online calculation
#################################################################################################
@app.route("/evarilos/ece/v1.0/add_one_location", methods=['POST'])
@crossdomain(origin='*')
def type3():
    try:
        experiment = message_evarilos_engine_type2_pb2.ece_type2()
        experiment.ParseFromString(request.data)
    except:
        return json.dumps('Experiment is not well defined!')

    response ={}

    if experiment.request_raw_data is True:
        raw_rssi_collection = raw_rssi_pb2.RawRSSIReadingCollection() 
        apiURL_raw_data = str(experiment.sut_raw_data_URI)
        
        data = {}
        data['coordinate_x'] = experiment.ground_truth.true_coordinate_x
        data['coordinate_y'] = experiment.ground_truth.true_coordinate_y
        try:
            data['coordinate_z'] = experiment.ground_truth.true_coordinate_z
        except:
            time.sleep(0)
        try:
            data['room_label'] = experiment.ground_truth.true_room_label
        except:
            time.sleep(0)

        req = RequestWithMethod(apiURL_raw_data, 'GET', headers={"Content-Type": "application/json"}, data = json.dumps(data))
        resp = urllib2.urlopen(req)
       
    if experiment.store_metrics is True:
        apiURL_metrics = experiment.metrics_storage_URI
        db_id = experiment.metrics_storage_database
        req = urllib2.Request(apiURL_metrics + 'evarilos/metrics/v1.0/database', headers={"Content-Type": "application/json"}, data = db_id)
        resp = urllib2.urlopen(req)

        coll_id = experiment.metrics_storage_collection
        req = RequestWithMethod(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id  + '/experiment', 'POST', headers={"Content-Type": "application/json"}, data = coll_id)
        resp = urllib2.urlopen(req)
            
        try:   
            req = RequestWithMethod(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id + '/experiment/' + coll_id, 'GET', headers={"Content-Type": "application/x-protobuf"}, data = 'protobuf')
            resp = urllib2.urlopen(req)
            message = resp.read()
            experiment_results = experiment_results_pb2.Experiment() 
            experiment_results.ParseFromString(message)
        except:
            experiment_results = experiment_results_pb2.Experiment() 

    localization_error_2D = {}
    localization_error_3D = {}
    latency = {} 
    power_consumption = {}
    number_of_points = 0
    number_of_good_rooms = {}

    for location in experiment_results.locations:
        number_of_points += 1
        x1 = location.true_coordinate_x
        y1 = location.true_coordinate_y
        x2 = location.est_coordinate_x
        y2 = location.est_coordinate_y
        localization_error_2D[number_of_points] = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2))
        try:
            z1 = location.true_coordinate_z
            z2 = location.est_coordinate_z
            localization_error_3D[number_of_points] = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2) + math.pow((z1-z2), 2))
        except:
            time.sleep(0)
        try:
            room1 = location.true_room_label
            room2 = location.est_room_label
            if room1.strip() == room2.strip():
                number_of_good_rooms[number_of_points] = 1 
            else:
                number_of_good_rooms[number_of_points] = 0
        except:
            time.sleep(0)
        try:
            latency[number_of_points] = location.latency
        except:
            time.sleep(0)
        try:
            power_consumption[number_of_points] = location.power_consumption
        except:
            time.sleep(0)

    # Get location estimate from the SUT
    if experiment.request_estimates is True:
        time1 = time.time()
        req = urllib2.Request(str(experiment.sut_location_estimate_URI), headers={"Content-Type": "application/json"})
        resp = urllib2.urlopen(req)
        time2 = time.time()
        loc_est_latency = time2 - time1
        estimated_location = json.loads(resp.read())
    else:
        estimated_location = {}
        try:
            estimated_location['coordinate_x'] = experiment.estimate.est_coordinate_x
            estimated_location['coordinate_y'] = experiment.estimate.est_coordinate_y
        except:
            return json.dumps('Define the location estimate in the message!')
        try:  
            estimated_location['coordinate_z'] = experiment.estimate.est_coordinate_z
        except:
            time.sleep(0)
        try:  
            estimated_location['room_label'] = experiment.estimate.est_room_label
        except:
            time.sleep(0)

    measurement_location = experiment_results.locations.add()
    number_of_points += 1
    measurement_location.point_id = experiment.ground_truth.point_id
    try:
        measurement_location.localized_node_id = experiment.ground_truth.localized_node_id 
    except:
        time.sleep(0)
    measurement_location.true_coordinate_x = x1 = experiment.ground_truth.true_coordinate_x
    measurement_location.true_coordinate_y = y1 = experiment.ground_truth.true_coordinate_y
    measurement_location.est_coordinate_x = x2 = estimated_location['coordinate_x']
    measurement_location.est_coordinate_y = y2 = estimated_location['coordinate_y']
    measurement_location.localization_error_2D = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2))
    localization_error_2D[number_of_points] = measurement_location.localization_error_2D
    try:
        measurement_location.true_coordinate_z = z1 = experiment.ground_truth.true_coordinate_z
        measurement_location.est_coordinate_z = z2 = estimated_location['coordinate_z']
        measurement_location.localization_error_3D = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2) + math.pow((z1-z2), 2))
        localization_error_3D[number_of_points] = measurement_location.localization_error_3D
    except:
        time.sleep(0)
    try:
        measurement_location.true_room_label = room1 = experiment.ground_truth.true_room_label
        measurement_location.est_room_label = room2 = estimated_location['room_label']
        if room1.strip() == room2.strip():
            measurement_location.localization_correct_room = 1
            number_of_good_rooms[number_of_points] = 1
        else:
            measurement_location.localization_correct_room = 0
            number_of_good_rooms[number_of_points] = 0
    except:
        time.sleep(0)
    try:
        measurement_location.latency = latency[number_of_points] = loc_est_latency
    except:
        time.sleep(0)
    try:
        measurement_location.latency = latency[number_of_points] = experiment.estimate.latency
    except:
        time.sleep(0)
    try:
        measurement_location.power_consumption = location.power_consumption
        power_consumption[number_of_points] = measurement_location.power_consumption
    except:
        time.sleep(0)
    try:
        measurement_location.power_consumption = experiment.estimate.power_consumption
        power_consumption[number_of_points] = measurement_location.power_consumption
    except:
        time.sleep(0)
    
    experiment_results.primary_metrics.error_2D_average = float(sum(localization_error_2D.values()))/number_of_points
    experiment_results.primary_metrics.error_2D_min = min(localization_error_2D.values())
    experiment_results.primary_metrics.error_2D_max = max(localization_error_2D.values())
    experiment_results.primary_metrics.error_2D_std = numpy.std(localization_error_2D.values())
    experiment_results.primary_metrics.error_2D_median = numpy.median(localization_error_2D.values())
    if len(localization_error_3D) != 0:
        experiment_results.primary_metrics.error_3D_average = float(sum(localization_error_3D.values()))/number_of_points
        experiment_results.primary_metrics.error_3D_min = min(localization_error_3D.values())
        experiment_results.primary_metrics.error_3D_max = max(localization_error_3D.values())
        experiment_results.primary_metrics.error_3D_std = numpy.std(localization_error_3D.values())
        experiment_results.primary_metrics.error_3D_median = numpy.median(localization_error_3D.values())
    if len(number_of_good_rooms) != 0:
        experiment_results.primary_metrics.room_error_average = float(sum(number_of_good_rooms.values()))/number_of_points
        print number_of_good_rooms.values()
        print number_of_points
    if len(latency) != 0:
        experiment_results.primary_metrics.latency_average = float(sum(latency.values()))/number_of_points
        experiment_results.primary_metrics.latency_min = min(latency.values())
        experiment_results.primary_metrics.latency_max = max(latency.values())
        experiment_results.primary_metrics.latency_std = numpy.std(latency.values())
        experiment_results.primary_metrics.latency_median = numpy.median(latency.values())
    if sum(power_consumption) != 0:
        experiment_results.primary_metrics.power_consumption_average = float(sum(power_consumption.values()))/number_of_points
        experiment_results.primary_metrics.power_consumption_median = numpy.median(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_min = min(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_max = max(power_consumption.values())
        experiment_results.primary_metrics.power_consumption_std = numpy.std(power_consumption.values())
    else:
        try:
            experiment_results.primary_metrics.power_consumption_average = experiment.power_consumption_per_experiment
        except:
            time.sleep(0)
    
    experiment_results.scenario.testbed_label = experiment.scenario.testbed_label
    experiment_results.scenario.testbed_description = experiment.scenario.testbed_description
    experiment_results.scenario.experiment_description = experiment.scenario.experiment_description
    experiment_results.scenario.sut_description = experiment.scenario.sut_description
    experiment_results.scenario.receiver_description = experiment.scenario.receiver_description 
    experiment_results.scenario.sender_description = experiment.scenario.sender_description  
    experiment_results.scenario.interference_description = experiment.scenario.interference_description
    experiment_results.timestamp_utc = experiment.timestamp_utc
    experiment_results.experiment_label = experiment.experiment_label
    
    obj = json.dumps(protobuf_json.pb2json(experiment_results))

    if experiment.store_metrics is True:
        apiURL_metrics = experiment.metrics_storage_URI
        db_id = experiment.metrics_storage_database
        req = urllib2.Request(apiURL_metrics + 'evarilos/metrics/v1.0/database', headers={"Content-Type": "application/json"}, data = db_id)
        resp = urllib2.urlopen(req)
        
        coll_id = experiment.metrics_storage_collection
        req = RequestWithMethod(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id  + '/experiment/' + coll_id, 'DELETE', headers={"Content-Type": "application/json"}, data = coll_id)
        resp = urllib2.urlopen(req)
        
        req = RequestWithMethod(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id  + '/experiment', 'POST', headers={"Content-Type": "application/json"}, data = coll_id)
        resp = urllib2.urlopen(req)
               
        req = urllib2.Request(apiURL_metrics + 'evarilos/metrics/v1.0/database/' + db_id + '/experiment/' + coll_id, headers={"Content-Type": "application/json"}, data = obj)
        resp = urllib2.urlopen(req)
        
    response = protobuf_json.pb2json(experiment_results)

    return json.dumps(response)       


##################################################################################################
### Type 1 Communication: Calculating and Storing Metrics
#################################################################################################
@app.route("/evarilos/ece/v1.0/calculate_and_store_metrics", methods=['GET'])
@crossdomain(origin='*')
def type1_present():
    experiment = message_evarilos_engine_type1_presentation_pb2.ece_type1() 

    with open("message_type_1.pb", "rb") as f:
        experiment.ParseFromString(f.read())

    return json.dumps(protobuf_json.pb2json(experiment))

#################################################################################################
### Type 2 Communication: Online calculation
#################################################################################################
@app.route("/evarilos/ece/v1.0/online_calculation", methods=['GET'])
@crossdomain(origin='*')
def type3_present():
    experiment = message_evarilos_engine_type2_presentation_pb2.ece_type2() 

    with open("message_type_2.pb", "rb") as f:
        experiment.ParseFromString(f.read())

    return json.dumps(protobuf_json.pb2json(experiment))

#######################################################################################################
# Additional help functions
#######################################################################################################

# Error handler
@app.errorhandler(404)
@crossdomain(origin='*')
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404) 

# Creating the URIs
def make_public_task(function):
    new_function = {}
    for field in function:
        if field == 'id':
            new_function['uri'] = url_for('get_function', function_id = function['id'], _external = True)
        else:
            new_function[field] = function[field]
    return new_function

# Enabling DELETE, PUT, etc.
class RequestWithMethod(urllib2.Request):
    """Workaround for using DELETE with urllib2"""
    def __init__(self, url, method, data=None, headers={}, origin_req_host=None, unverifiable=False):
        self._method = method
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self) 

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5002, debug = 'True') 
