import smtplib
from email.mime.text import MIMEText
import sys
import os

# read arguments -- username and random number
username = sys.argv[1]
random_number = sys.argv[2]

# read configuration file
if os.path.exists('config_email.txt') == False:
    print('** Error: config_email.txt file not found!')
else:
    config_file = open('config_email.txt').readlines()
    port, sender, psw, host = config_file[-1].rstrip().split()

    # Email details
    subject = 'Motifscope job'
    sender_name = f"MotifScope <{sender}>"
    body = 'Your job is completed. Your run ID is %s. \n\nGo to https://motifscope.holstegelab.eu/download/, insert your run ID, and download the results.\n\nMotifScope Team' %(random_number)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_name
    msg['To'] = username

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(sender, psw)
        server.sendmail(sender, username, msg.as_string())

    print('** Email sent successfully!')








