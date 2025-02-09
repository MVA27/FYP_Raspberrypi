#!/usr/bin/env python

import bme680
import time
import bmeutil
import requests as req

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)


# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS) #bme680.DISABLE_GAS_MEAS


print('\n\nInitial reading:')
for name in dir(sensor.data):
    value = getattr(sensor.data, name)

    if not name.startswith('_'):
        print('{}: {}'.format(name, value))


# Heating durations between 1 ms and 4032 ms can be configured.
# Approximately 20-30 ms are necessary for the heater to reach the intended target temperature.

sensor.set_gas_heater_profile(temperature=300, duration=150, nb_profile=0)
sensor.select_gas_heater_profile(0)


start_time = time.time()
current_time = time.time()

burn_in_time = 60
burn_in_data_list = []

print('\n\nPolling:')
try:
    # Collect gas resistance burn-in values, then use the average
    # of the last 50 values to set the upper limit for calculating
    # gas_baseline.
    print('Collecting gas resistance burn-in data for 5 mins\n')
    while current_time - start_time < burn_in_time:
        current_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data_list.append(gas)
            print('Gas: {0} Ohms'.format(gas))
            time.sleep(1)

    gas_baseline = sum(burn_in_data_list[-50:]) / 50.0

    ip = 'http://43.204.219.105'

    #Send a blank request (i.e request without data) to receive Flag values
    link = ip + '/Raspberrypi/catch.php'
    response = req.get(link,verify=False)
    json = response.json()
    flags = Flags(**json)

    if flags.terminate == "1":
        print("WARNING: Administrator has stopped the execution. Ask the Administrator to start the execution..!")

    #Infinite Loop to fetch the data
    while True:

        if flags.terminate == "0": #Continue fetching values from Raspberry pi and sending it to server
            if sensor.get_sensor_data():
                output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(sensor.data.temperature,sensor.data.pressure,sensor.data.humidity)

                if sensor.data.heat_stable:
                    air_quality_score = bmeutil.get_air_quality_score(sensor,gas_baseline)
                    print('{0},air quality: {1:.2f}'.format(output,air_quality_score))
                    link = ip + '/Raspberrypi/catch.php?t={0:.2f}&p={1:.2f}&h={2:.2f}&a={3:.2f}'.format(sensor.data.temperature,sensor.data.pressure,sensor.data.humidity,air_quality_score)
                    response = req.get(link,verify=False)
                    json = response.json()
                    flags = Flags(**json)
                    print("Current Flags : sleep="+flags.sleep+", terminate="+flags.terminate,end="\n")

                else:
                    print(output)
             
        else: #Continue fetching flags
            print("System terminated..")
            link = ip + '/Raspberrypi/catch.php'
            response = req.get(link,verify=False)
            json = response.json()
            flags = Flags(**json)   
            print("Current Flags : sleep="+flags.sleep+", terminate="+flags.terminate,end="\n")   
        
        #TODO : Increase the time and set minimum time
        time.sleep(flags.sleep)

except KeyboardInterrupt:
    print("Exception : key pressed")


# class and functions decleration
class Flags:
    def __init__(self, sleep, terminate):
        self.sleep = sleep
        self.terminate = terminate