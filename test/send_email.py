from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import smtplib


MY_ADDRESS = 'blackcreekapp@gmail.com'
PASSWORD = 'Evarist@28'


def main():
    emails = ["dcmalevae@gmail.com", "dcmalevae@gmail.com",
              "dpmalevae@gmail.com"]  # read contacts

    # set up the SMTP server
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    for email in emails:
        msg = MIMEMultipart()
        # setup the parameters of the message
        msg['From'] = MY_ADDRESS
        msg['To'] = email
        msg['Subject'] = "This is TEST"
        msg['Body'] = "Hello testing"

        # add in the message body

        # send the message via the server set up earlier.
        s.send_message(msg)
        del msg

        # Terminate the SMTP session and close the connection
    s.quit()


if __name__ == '__main__':
    main()
