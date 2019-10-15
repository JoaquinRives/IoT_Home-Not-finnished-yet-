from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart, MIMEBase
import smtplib
import logging
from app.config import config
import os

logger = logging.getLogger(__name__)  # TODO
logger = config.config_logger(logger)


class EmailSender:

    def __init__(self):
        self.from_addr = config.FROM_ADDR
        self.password = config.PASSWORD
        self.to_addr = config.TO_ADDR
        self.smtp_server = config.SMTP_SERVER 

    def send_email(self, subject, message, attach_images=None):

        # TODO:
        # - Add msg templates to the config file
        # - Rearrange the arguments of this function
        # - Add date and time to de msg
        # - Log everything

        # Email multiple part object
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = Header(subject, 'utf-8').encode()

        # Attach images and insert them in the html code.
        images_html = None
        if attach_images:
            list_images = []
            for img_id, image in enumerate(attach_images):    
                with open(image, 'rb') as f:
                    mime = MIMEBase(os.path.splitext(image)[0], os.path.splitext(image)[1], filename=os.path.basename(image))
                    mime.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image))
                    mime.add_header('X-Attachment-Id', str(img_id))
                    mime.add_header('Content-ID', '<' + str(img_id) + '>')
                    mime.set_payload(f.read())
                    encoders.encode_base64(mime)
                    # Add object to MIMEMultipart object
                    msg.attach(mime)
                    list_images.append("<p><img src='cid:" + str(img_id) + "'></p>")
            
            images_html = " \n ".join(list_images)

        # Add object to MIMEMultipart object
        msg_content = MIMEText(

            "<html>"
                "<body>"
                    "<h1>RPi Home:</h2>"
                    "<h2>" + subject + "</h2>"
                    "<h3>" + message + "</h3>"
                    "<br>" + (images_html if images_html else "") + "<br>"
                "</body>"
            "</html>", "html", "utf-8")

        msg.attach(msg_content)

        # Connect to the server and send email
        smtp = smtplib.SMTP(self.smtp_server)
        smtp.starttls()
        smtp.login(self.from_addr, self.password)
        smtp.sendmail(self.from_addr, [self.to_addr], msg.as_string())
        smtp.quit()
