from app.pyimagesearch.motion_detection import SingleMotionDetector
from app.pyimagesearch.tempimage import TempImage
from picamera.array import PiRGBArray
from app.config import config
from app.emailer_classes import EmailSender
import warnings
import threading
import dropbox
import datetime
import imutils
import time
import cv2
import logging

logger = logging.getLogger(__name__)
logger = config.config_logger(logger)

outputFrame = None
lock = threading.Lock()

email_sender = EmailSender()


def detect_motion(frameCount, video_stream):
    global outputFrame, lock

    t = threading.currentThread()
    vs = video_stream

    # initialize the motion detector and the total number of frames
    md = SingleMotionDetector(accumWeight=0.1)
    total = 0

    time.sleep(2)  # Leave time for the webcam to warm up

    # loop over frames from the video stream
    while getattr(t, "do_run", True):
        # read the next frame from the video stream, resize it, convert to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime(
            "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            motion = md.detect(gray)

            # check to see if motion was found in the frame
            if motion is not None:
                # unpack the tuple and draw surrounding box
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY),
                              (0, 0, 255), 2)

        # update the background model and increment the total number of frames read thus far
        md.update(gray)
        total += 1

        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()


def generate_video_feed():
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')
