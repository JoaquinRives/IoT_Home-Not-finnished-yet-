import time
import threading
import RPi.GPIO as GPIO


def auto_func(actuator, temp, t_range):
    
    is_on = False  # TODO get if it is on ???
    t_now = 15  # TODO get current temp
    t_keep = int(temp)
    t_max, t_min = t_keep + int(t_range),  t_keep - int(t_range)

    t = threading.currentThread()

    while getattr(t, "do_run", True):
        if t_now > t_max:
            is_on = False # TODO borrar?
            GPIO.output(actuator, GPIO.HIGH)
        if t_now < t_min:
            GPIO.output(actuator, GPIO.LOW)
            is_on = True
        if is_on:
            t_now += 1
        else:
            t_now -= 1
        print(t_now)
        time.sleep(1)
