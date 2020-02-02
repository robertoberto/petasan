'''
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
'''

from PetaSAN.core.entity.status import EmailStatus
from PetaSAN.core.common.enums import EmailSecurity
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def create_msg(sender, to, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return msg

def send_email(server, port, msg, sender_password, security):
    status = EmailStatus()
    security = int(security)
    try:
        if EmailSecurity.ssl == security:
            server = smtplib.SMTP_SSL(server, int(port))
            server.login(msg['From'], sender_password)
        elif EmailSecurity.tls ==security:
            server = smtplib.SMTP(server, int(port))
            server.starttls()
            server.login(msg['From'], sender_password)

        elif EmailSecurity.plain == security:
            server = smtplib.SMTP(server, int(port))
            server.login(msg['From'], sender_password)
        elif EmailSecurity.anonymous ==security:
            server = smtplib.SMTP(server, int(port))

        text = msg.as_string()
        server.sendmail(msg['From'], msg['To'], text)
        server.quit()
    except Exception as e:
        status.exception = e
        status.err_msg = e.message
        status.success = False
    return status


#
# msg = create_msg("mostafa@petasan.org","dr.samamostafa@gmail.com","hi test","test test test")
# r  = send_email("localhost",25,msg,"",EmailSecurity.anonymous)
# print r.success,r.err_msg