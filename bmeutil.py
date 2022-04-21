def get_air_quality_score(sensor,gas_baseline):


    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    print('Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n'.format(gas_baseline,hum_baseline))

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

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