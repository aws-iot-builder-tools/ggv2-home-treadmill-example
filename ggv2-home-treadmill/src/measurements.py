# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import time
import traceback
import json

import signal
import sys
import RPi.GPIO as GPIO
from collections import deque

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    IoTCoreMessage,
    QOS,
    PublishToIoTCoreRequest
)

BUTTON_GPIO = 18
# 1Hz is 2.2km/h
CONVERSION_FACTOR = 2.2

start = time.time()
# Used to calculate average speed
speeds = deque([0, 0, 0, 0, 0])

TIMEOUT = 10

ipc_client = awsiot.greengrasscoreipc.connect()

topic = "home/treadmill/speed"
qos = QOS.AT_MOST_ONCE

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def reed_switch_callback(channel):
    global start
    # Elapsed time between previous falling edge
    elapsed = time.time() - start
    start = time.time()
    speed = CONVERSION_FACTOR / elapsed
    # Discard the noise as we can't measure speed above 36
    if speed < 36:
        speeds.append(speed)
        speeds.popleft()


GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON_GPIO, GPIO.FALLING, callback=reed_switch_callback, bouncetime=10)

signal.signal(signal.SIGINT, signal_handler)
while True:
    no_activity = time.time() - start
    
    if no_activity > 1:
        # if there is no activity for more then 1s
        # this means we are bellow 2.2km/h so we add 0km/h measurement
        speeds.append(0)
        speeds.popleft()
    av_speed = sum(speeds) / len(speeds)
    if av_speed > 0:

        print(f'average speed: {av_speed}')

        request = PublishToIoTCoreRequest()
        request.topic_name = topic
        message = json.dumps({
            'time': time.time(),
            'speed': av_speed
        })
        request.payload = bytes(message, "utf-8")
        request.qos = qos
        operation = ipc_client.new_publish_to_iot_core()
        operation.activate(request)
        future_response = operation.get_response()
        future_response.result(TIMEOUT)        

    time.sleep(0.5)

