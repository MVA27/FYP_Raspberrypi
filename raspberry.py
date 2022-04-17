#!/usr/bin/env python

import bme680
import time

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

def get_air_quality_score(sensor):
    gas = sensor.data.gas_resistance
    gas_offset = gas_baseline - gas

    hum = sensor.data.humidity
    hum_offset = hum - hum_baseline

    # Calculate hum_score as the distance from the hum_baseline.
    if hum_offset > 0:
        hum_score = (100 - hum_baseline - hum_offset)
        hum_score /= (100 - hum_baseline)
        hum_score *= (hum_weighting * 100)

    else:
        hum_score = (hum_baseline + hum_offset)
        hum_score /= hum_baseline
        hum_score *= (hum_weighting * 100)

    # Calculate gas_score as the distance from the gas_baseline.
    if gas_offset > 0:
        gas_score = (gas / gas_baseline)
        gas_score *= (100 - (hum_weighting * 100))

    else:
        gas_score = 100 - (hum_weighting * 100)

    # Calculate air_quality_score.
    air_quality_score = hum_score + gas_score
    return air_quality_score

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

    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

    print('Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n'.format(gas_baseline,hum_baseline))

    while True:
        if sensor.get_sensor_data():
            output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(sensor.data.temperature,sensor.data.pressure,sensor.data.humidity)

            if sensor.data.heat_stable:
                air_quality_score = get_air_quality_score(sensor)
                print('{0},air quality: {1:.2f}'.format(output,air_quality_score))

            else:
                print(output)

        time.sleep(1)

except KeyboardInterrupt:
    print("Exception : key pressed")