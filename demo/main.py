# Custom imports
from custom_classes import question
from custom_functions import query
import engine

# SMTP imports
import smtplib, ssl
from getpass import getpass


port = 465  # For SSL
password = '420blazeit!'
sender_email = "chatbotquestionbank420@gmail.com"
receiver_email = "chatbotquestionbank420@gmail.com"


# Function to send email with missing question as message
def add_to_questionbank(message):
    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login("chatbotquestionbank420@gmail.com", password)
        server.sendmail(sender_email, receiver_email, message)


def ask(q):
    input_qn = question(q)
    payload = query(input_qn, engine.model, engine.datarows, debug=True)
    print("Question:{}".format(q))

    return payload
