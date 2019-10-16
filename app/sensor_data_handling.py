import smbus
import time
import datetime
import os
import logging
import threading
from app.config import config

sensor_logger = logging.getLogger(__name__)
sensor_logger = config.config_logger(sensor_logger, type="sensor")

main_logger = logging.getLogger(__name__)
main_logger = config.config_logger(sensor_logger, type="main")


def data_collection():
    """ Function for handling of the sensors data """

    t = threading.currentThread()

    while getattr(t, "do_run", True):    
        DEVICE_BUS = 1
        DEVICE_ADDR = 0x17

        TEMP_REG = 0x01
        LIGHT_REG_L = 0x02
        LIGHT_REG_H = 0x03
        STATUS_REG = 0x04
        ON_BOARD_TEMP_REG = 0x05
        ON_BOARD_HUMIDITY_REG = 0x06
        ON_BOARD_SENSOR_ERROR = 0x07
        BMP280_TEMP_REG = 0x08
        BMP280_PRESSURE_REG_L = 0x09
        BMP280_PRESSURE_REG_M = 0x0A
        BMP280_PRESSURE_REG_H = 0x0B
        BMP280_STATUS = 0x0C
        HUMAN_DETECT = 0x0D

        bus = smbus.SMBus(DEVICE_BUS)

        aReceiveBuf = []

        aReceiveBuf.append(0x00)

        data = []
        data.append(str(datetime.datetime.now()))

        # TODO: delete prints

        # Thermal infrarred
        for i in range(TEMP_REG,HUMAN_DETECT + 1):
            aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

        # External temperature detection (probe)
        if aReceiveBuf[STATUS_REG] & 0x01 :
            sensor_logger.warning("Off-chip temperature sensor overrange!")
            data.append('nan')
        elif aReceiveBuf[STATUS_REG] & 0x02 :
            sensor_logger.warning("No external temperature sensor!")
            data.append('nan')
        else :
            #print("Current off-chip sensor temperature = %d Celsius" % aReceiveBuf[TEMP_REG])
            data.append(str(aReceiveBuf[TEMP_REG]))
        
        # Light intensity detection
        if aReceiveBuf[STATUS_REG] & 0x04 :
            sensor_logger.warning("Onboard brightness sensor overrange!")
            data.append('nan')
        elif aReceiveBuf[STATUS_REG] & 0x08 :
            sensor_logger.warning("Onboard brightness sensor failure!")
            data.append('nan')
        else :
            #print("Current onboard sensor brightness = %d Lux" % (aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L]))
            data.append(str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L])))

        # OnBoard temperature sensor
        #print("Current onboard sensor temperature = %d Celsius" % aReceiveBuf[ON_BOARD_TEMP_REG])
        data.append(str(aReceiveBuf[ON_BOARD_TEMP_REG]))

        # Humidity sensor
        #print("Current onboard sensor humidity = %d %%" % aReceiveBuf[ON_BOARD_HUMIDITY_REG])
        data.append(str(aReceiveBuf[ON_BOARD_HUMIDITY_REG]))

        if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
            sensor_logger.warning("Onboard temperature and humidity sensor data may not be up to date!")

        # Pressure sensor
        if aReceiveBuf[BMP280_STATUS] == 0 :
            #print("Current barometer temperature = %d Celsius" % aReceiveBuf[BMP280_TEMP_REG])
            data.append(str(aReceiveBuf[BMP280_TEMP_REG]))
            #print("Current barometer pressure = %d pascal" % (aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16))
            data.append(str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16)))
        else :
            sensor_logger.warning("Onboard barometer works abnormally!")
            data.append('nan')
            data.append('nan')

        # Human detection
        if aReceiveBuf[HUMAN_DETECT] == 1 :
            #print("Live body detected within 5 seconds!")
            data.append('1')
        else:
            #print("No humans detected!")
            data.append('0')

        data_row = ";".join(data) + "\n"

        data_header = "time_stamp;off-chip temperature;brightness;onboard temperature;onboard humidity;" \
            "barometer temperature;barometer pressure;humans detected\n"

        sensor_data_file = config.SENSOR_DATA_FILE

        # Create the sensors_data file and add the "header" if the file doesn't exist or it is empty
        if not os.path.exists(config.SENSOR_DATA_FILE) or not os.path.getsize(config.SENSOR_DATA_FILE) > 0:
            try:
                with open(sensor_data_file, 'w') as f:
                    f.write(data_header)
            except Exception as e:
                sensor_logger.warning(f"Failure writing header to sensor_data.txt - Exception: {e}")
            
        # Append row of data to the sensors data file
        try:            
            with open(sensor_data_file, 'a') as f:
                f.write(data_row)

        except Exception as e:
            sensor_logger.warning(f"Failure writing row of data to sensor_data.txt - Exception: {e}")


        time.sleep(10)


def get_sensorhub_data():
    DEVICE_BUS = 1
    DEVICE_ADDR = 0x17

    TEMP_REG = 0x01
    LIGHT_REG_L = 0x02
    LIGHT_REG_H = 0x03
    STATUS_REG = 0x04
    ON_BOARD_TEMP_REG = 0x05
    ON_BOARD_HUMIDITY_REG = 0x06
    ON_BOARD_SENSOR_ERROR = 0x07
    BMP280_TEMP_REG = 0x08
    BMP280_PRESSURE_REG_L = 0x09
    BMP280_PRESSURE_REG_M = 0x0A
    BMP280_PRESSURE_REG_H = 0x0B
    BMP280_STATUS = 0x0C
    HUMAN_DETECT = 0x0D

    bus = smbus.SMBus(DEVICE_BUS)

    aReceiveBuf = []

    aReceiveBuf.append(0x00)

    data = {}

    # Thermal infrarred
    for i in range(TEMP_REG,HUMAN_DETECT + 1):
        aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

    # External temperature detection (probe)
    if aReceiveBuf[STATUS_REG] & 0x01 :
        main_logger.warning("Off-chip temperature sensor overrange!")
        data["off-chip temperature"] = 'nan'
    elif aReceiveBuf[STATUS_REG] & 0x02 :
        main_logger.warning("No external temperature sensor!")
        data["off-chip temperature"] = 'nan'
    else :
        data["off-chip temperature"] = str(aReceiveBuf[TEMP_REG])
    
    # Light intensity detection
    if aReceiveBuf[STATUS_REG] & 0x04 :
        main_logger.warning("Onboard brightness sensor overrange!")
        data["brightness"] = 'nan'
    elif aReceiveBuf[STATUS_REG] & 0x08 :
        main_logger.warning("Onboard brightness sensor failure!")
        data["brightness"] = 'nan'
    else :
        data["brightness"] = str((aReceiveBuf[LIGHT_REG_H] << 8 | aReceiveBuf[LIGHT_REG_L]))

    # OnBoard temperature sensor
    data["onboard temperature"] = str(aReceiveBuf[ON_BOARD_TEMP_REG])

    # Humidity sensor
    data["onboard humidity"] = str(aReceiveBuf[ON_BOARD_HUMIDITY_REG])

    if aReceiveBuf[ON_BOARD_SENSOR_ERROR] != 0 :
        main_logger.warning("Onboard temperature and humidity sensor data may not be up to date!")

    # Pressure sensor
    if aReceiveBuf[BMP280_STATUS] == 0 :
        data["barometer temperature"] = str(aReceiveBuf[BMP280_TEMP_REG])
        data["barometer pressure"] = str((aReceiveBuf[BMP280_PRESSURE_REG_L] | aReceiveBuf[BMP280_PRESSURE_REG_M] << 8 | aReceiveBuf[BMP280_PRESSURE_REG_H] << 16))
    else :
        main_logger.warning("Onboard barometer works abnormally!")
        data["barometer temperature"] = 'nan'
        data["barometer pressure"] = 'nan'

    # Human detection
    if aReceiveBuf[HUMAN_DETECT] == 1 :
        data["humans detected"] = '1'
    else:
        data["humans detected"] = '0'

    return data

    



