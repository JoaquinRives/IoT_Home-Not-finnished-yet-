# IoT Home
Project for home automation with a Raspberry Pi 3

App to control things at home from anywhere using a Raspberry Pi 3. On this project I make use of different sensors to collect data and a Raspberry Pi Camera 5MP for surveillance. The GPIOs of the RPi are also programmed to control a 4 Channel Relay that can be connected to any appliances. 
The commands to the RPi are sent using a simple webpage by creating a local Web server on the Raspberry Pi. Python and Flask were used for this project.

=> Features:
  -	Temperature, humidity and atmospheric pressure monitoring.
  -	Switch control of any electrical device or lights
  -	House heating control
  -	Security Alarm system:
      o	Video recording
      o	Motion detection (OpenCV)
      o	Automatic notification by email
      o	Automatic uploading of captures to dropbox

=> Devices used for the project:
  -	Raspberry Pi 3 B with Raspbian OS
  -	4 Channel Relay (5V Active Low - Output AC 250V)
  -	Raspberry camera module 5MP 
  -	Sensor Hub:
      o	Temperature and Humidity
      o	Atmospheric Pressure
      o	Light Intensity Detection
      o	Motion Detection


=> Testing the App (Video)

[![Watch the video](/app/static/screenshot_video.png?raw=true "Screenshot Video")](https://youtu.be/laLAe-Fh5wk)


=> Screenshots

![alt text](/app/static/screenshot1.png?raw=true "Screenshot 1")
![alt text](/app/static/screenshot3.png?raw=true "Screenshot 2")


=> Accessing the server from outside the local network:

  This set up is needed to be able to access the server from outsite the local network with a Custom Domain Name:
    1- Give the raspberry a static IP adress (and add it to the flask app)
    2- Set up port forwarding
    3- Set up the DDNS (dynamic domain name setup)

    Tutorials:
    - https://www.youtube.com/watch?v=jfSLxs40sIw
    - https://maker.pro/raspberry-pi/projects/raspberry-pi-web-server
    - https://raspberrypi.stackexchange.com/questions/37920/how-do-i-set-up-networking-wifi-static-ip-address


Additional:
  - Tutorial to connect the Relay:
  https://www.youtube.com/watch?v=My1BDB1ei0E&t=273s
  -	Raspberry Pi 3 B+: 
  https://www.amazon.co.uk/Raspberry-Pi-Official-Desktop-Starter/dp/B01CI5879A/ref=sr_1_6?keywords=Raspberry+pi+b&qid=1570292368&sr=8-6
  -	Relay 4 Chanel: 
  https://www.amazon.co.uk/gp/product/B06XK6HCQC/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1 (Careful, only 10A max)
  -	Raspberry Pi Camera: 
  https://www.amazon.co.uk/gp/product/B07PMQK528/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1
  -	Sensor Hub: 
  https://www.amazon.co.uk/gp/product/B07TZD8B61/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1


![alt text](/app/static/photo1.jpg?raw=true "photo 1")
![alt text](/app/static/photo2.jpg?raw=true "photo 2")

