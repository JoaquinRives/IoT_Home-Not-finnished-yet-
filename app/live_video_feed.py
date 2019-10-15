from app.pyimagesearch.motion_detection import SingleMotionDetector
from app.pyimagesearch.tempimage import TempImage
from picamera.array import PiRGBArray
from picamera import PiCamera
from app.config.config import security_alarm_config as config
import warnings
import threading
#import dropbox
import datetime
import imutils
import time
import cv2

outputFrame = None
lock = threading.Lock()


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
				# unpack the tuple and draw the box surrounding the "motion area" on the output frame
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


def pi_surveillance(pi_camera):
	warnings.filterwarnings("ignore")
	
	# if conf["use_dropbox"]:
	# # connect to dropbox and start the session authorization process
	# client = dropbox.Dropbox(conf["dropbox_access_token"])
	# print("[SUCCESS] dropbox account linked")

	# initialize the camera and grab a reference to the raw camera capture
	camera = pi_camera
	camera.resolution = tuple(config["resolution"])
	camera.framerate = config["fps"]
	rawCapture = PiRGBArray(camera, size=tuple(config["resolution"]))

	# allow the camera to warmup, then initialize the average frame, last
	# uploaded timestamp, and frame motion counter
	print("[INFO] warming up...")  				# TODO log this
	time.sleep(config["camera_warmup_time"])
	avg = None
	lastUploaded = datetime.datetime.now()
	motionCounter = 0

	t = threading.currentThread()

	while getattr(t, "do_run", True):
		# capture frames from the camera
		for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
			# grab the raw NumPy array representing the image and initialize
			# the timestamp and occupied/unoccupied text
			frame = f.array
			timestamp = datetime.datetime.now()
			text = "Unoccupied"

			# resize the frame, convert it to grayscale, and blur it
			frame = imutils.resize(frame, width=500)
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			gray = cv2.GaussianBlur(gray, (21, 21), 0)

			# if the average frame is None, initialize it
			if avg is None:
				print("[INFO] starting background model...")  # TODO log this instead of print it
				avg = gray.copy().astype("float")
				rawCapture.truncate(0)
				continue

			# accumulate the weighted average between the current frame and
			# previous frames, then compute the difference between the current
			# frame and running average
			cv2.accumulateWeighted(gray, avg, 0.5)
			frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

			# threshold the delta image, dilate the thresholded image to fill
			# in holes, then find contours on thresholded image
			thresh = cv2.threshold(frameDelta, config["delta_thresh"], 255,
				cv2.THRESH_BINARY)[1]
			thresh = cv2.dilate(thresh, None, iterations=2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
				cv2.CHAIN_APPROX_SIMPLE)
			cnts = imutils.grab_contours(cnts)

			# loop over the contours
			for c in cnts:
				# if the contour is too small, ignore it
				if cv2.contourArea(c) < config["min_area"]:
					continue

				# compute the bounding box for the contour, draw it on the frame,
				# and update the text
				(x, y, w, h) = cv2.boundingRect(c)
				cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
				text = "Occupied"

			# draw the text and timestamp on the frame
			ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
			cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
			cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
				0.35, (0, 0, 255), 1)

			# check to see if the room is occupied
			if text == "Occupied":
				# check to see if enough time has passed between uploads
				if (timestamp - lastUploaded).seconds >= config["min_upload_seconds"]:
					# increment the motion counter
					motionCounter += 1

					# check to see if the number of frames with consistent motion is
					# high enough
					if motionCounter >= config["min_motion_frames"]:
						print('movement detected!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
						# check to see if dropbox sohuld be used
						if config["use_dropbox"]:
							# write the image to temporary file
							t = TempImage()
							cv2.imwrite(t.path, frame)

							# upload the image to Dropbox and cleanup the tempory image
							print("[UPLOAD] {}".format(ts))  							# TODO Log this ############
							path = "/{base_path}/{timestamp}.jpg".format(
								base_path=conf["dropbox_base_path"], timestamp=ts)
							client.files_upload(open(t.path, "rb").read(), path)
							t.cleanup()

						# update the last uploaded timestamp and reset the motion
						# counter
						lastUploaded = timestamp
						motionCounter = 0

			# otherwise, the room is not occupied
			else:
				motionCounter = 0

			# # check to see if the frames should be displayed to screen
			# if conf["show_video"]:										# TODO borrar
			# 	# display the security feed
			# 	cv2.imshow("Security Feed", frame)
			# 	key = cv2.waitKey(1) & 0xFF

			# 	# if the `q` key is pressed, break from the lop
			# 	if key == ord("q"):
			# 		break

			# clear the stream in preparation for the next frame
			rawCapture.truncate(0)
		
			

