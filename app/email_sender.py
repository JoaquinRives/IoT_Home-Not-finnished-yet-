from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart, MIMEBase
import smtplib
import logging
from app.config.config import config_logger

logger = logging.getLogger(__name__)  # TODO
logger = config_logger(logger)

from_addr = 'email@gmail.com'
password = 'password' 
to_addr = 'email@gmail.com'
smtp_server = 'Smtp.gmail.com'

# Email multiple part object
msg = MIMEMultipart()
msg['From'] = from_addr
msg['To'] = to_addr
msg['Subject'] = Header('hello world from smtp server', 'utf-8').encode()

# to add an attachment is just add a MIMEBase object to read a picture locally.
with open(r'D:\OneDrive\Desktop\Raspberry_WebApp\static\light_off_icon3.jpg', 'rb') as f:
    mime = MIMEBase('light_off_icon3', 'jpg', filename='light_off_icon3.jpg')
    mime.add_header('Content-Disposition', 'attachment', filename='light_off_icon3.jpg')
    mime.add_header('X-Attachment-Id', '0')
    mime.add_header('Content-ID', '<0>')
    mime.set_payload(f.read())
    encoders.encode_base64(mime)
    # Add object to MIMEMultipart object
    msg.attach(mime)

# # Add object to MIMEMultipart object
msg_content = MIMEText(

    '<html>'
        '<body>'
            '<h1>Hello</h1>'
            '<p><img src="cid:0"></p>'
        '</body>'
    '</html>', 'html', 'utf-8')

msg.attach(msg_content)

# Connect to the server and send email
smtp = smtplib.SMTP('smtp.gmail.com:587')
smtp.starttls()
smtp.login(from_addr, password)
smtp.sendmail(from_addr, [to_addr], msg.as_string())
smtp.quit()
