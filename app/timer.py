import datetime
import time
import threading
import RPi.GPIO as GPIO
import re


def timer_func(actuator, time_on, time_off, repeat):

    now = datetime.datetime.now()

    # Add seconds to get the right format
    if re.match('^\d+\:\d+\:\d+$', time_on):
        time_on = time_on
    else:
        time_on = time_on + ':00'  

    if re.match('^\d+\:\d+\:\d+$', time_off):
        time_off = time_off
    else:
        time_off = time_off + ':00'

    time_on = datetime.datetime.strptime(time_on, "%H:%M:%S")
    time_off = datetime.datetime.strptime(time_off, "%H:%M:%S")

    time_on = now.replace(hour=time_on.time().hour, minute=time_on.time().minute, second=0, microsecond=0)
    time_off = now.replace(hour=time_off.time().hour, minute=time_off.time().minute, second=0, microsecond=0)

    t = threading.currentThread()

    # Timer logic for controlling  the GPIOs
    while getattr(t, "do_run", True):  # <-- To stop the thread with a Flag
        current_str = str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute)
        time_on_str = str(time_on.hour) + ':' + str(time_on.minute)
        time_off_str = str(time_off.hour) + ':' + str(time_off.minute)

        if current_str > max( time_on_str, time_off_str):
            if time_off_str == time_on_str:
                pass
            elif time_on_str > time_off_str:
                GPIO.output(actuator, GPIO.LOW)
            else:
                GPIO.output(actuator, GPIO.HIGH)
        elif min(time_off_str, time_on_str) < current_str < max(time_off_str, time_on_str):
            if time_on_str < current_str:
                GPIO.output(actuator, GPIO.LOW)
            else:
                GPIO.output(actuator, GPIO.HIGH)
        else:
            if time_off_str == time_on_str:
                pass
            elif current_str == time_on_str:
                GPIO.output(actuator, GPIO.LOW)
            elif current_str == time_off_str:
                GPIO.output(actuator, GPIO.HIGH)

        # Stop timer at the end of the day if repeat==off
        if repeat == 'off':
            if datetime.datetime.now().day > now.day:
                break

        time.sleep(1) 
