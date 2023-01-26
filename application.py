# works with both python 2 and 3
from __future__ import print_function
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from heyoo import WhatsApp
from log import post_logger, logger
import json
from datetime import datetime

application = Flask(__name__)

Token = 'EABXwLvbonGMBADwOKa594mA2vpQMgCKTNw31w9GZAKZCEQWU5TF5jPjFOkHnszd7uxHks8pOJuoSoSbTZCa36jBrTTtkK2oW0AUjB9TrIwiKa6usME23PnMLGgKM9xgZB9gPUgPceanpWVeh8L5DT604XASFGgDKiRx60ZBodSw2SH7ZCq9yzfROHurlpXZA4j4KZBPekawvfoTC2liOfOLj'

messenger = WhatsApp(Token, phone_number_id='106592595452225')

VERIFY_TOKEN = "30cca545-3838-48b2-80a7-9e43b1ae8ce4"

application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///conversations.db"

db = SQLAlchemy(application)

class IncomingRequest(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    status = db.Column(db.String(255))
    timestamp = db.Column(db.String(255))
    recipient_id = db.Column(db.String(255))
    conversation_id = db.Column(db.String(255))
    message_id = db.Column(db.String, unique=True)
    expiration_timestamp = db.Column(db.String(255))
    origin = db.Column(db.String(255))
    billable = db.Column(db.String(255))
    pricing_model = db.Column(db.String(255))
    processed = db.Column(db.Boolean, default=False)
   

    def __init__(self, status, timestamp, recipient_id, conversation_id, message_id, origin, billable, pricing_model, processed):

        self.status = status
        self.timestamp = timestamp
        self.recipient_id = recipient_id
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.origin = origin
        self.billable = billable
        self.pricing_model = pricing_model
        self.processed = processed



def save_request(data):

        # Extract the conversation_id and message_id from the data
        conversation_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['conversation']['id'] #c1b63a1655a036852a22a89da7fb908a
        message_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['id'] #wamid.HBgMMjU0NzQxNTkwMzMwFQIAERgSMTZCMjIzOTlEMjVFQTE2MjUyAA==
        
        
        # Check if a request with the same conversation_id and message_id already exists in the database
        request_exists = IncomingRequest.query.filter_by(conversation_id=conversation_id, id=message_id).first()

        if request_exists:
            logging.info("Incoming request already exists in the database")
        else:

            try:            
                status = data['entry'][0]['changes'][0]['value']['statuses'][0]['status'] #sent
                timestamp = data['entry'][0]['changes'][0]['value']['statuses'][0]['timestamp'] #1674635192
                recipient_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['recipient_id'] #254716434058 
                origin = data['entry'][0]['changes'][0]['value']['statuses'][0]['conversation']['origin']['type'] #user_initiated
                billable = data['entry'][0]['changes'][0]['value']['statuses'][0]['pricing']['billable'] #True
                pricing_model = data['entry'][0]['changes'][0]['value']['statuses'][0]['pricing']['pricing_model'] #CBP

        
                new_request = IncomingRequest(status=status, timestamp=timestamp, recipient_id=recipient_id, conversation_id=conversation_id, message_id=message_id, origin=origin, billable=billable, pricing_model=pricing_model, processed=False)
                db.session.add(new_request)
                db.session.commit()             

            except Exception as e:
                logger.exception(e)

        return 'ok'

def check_message_processed(message_id):
    processed = IncomingRequest.query.filter_by(message_id=message_id, processed=True).first()
    return True if processed else False




@application.before_request
def log_request():
    try:
        if request.method == 'POST':

            # Log the incoming request
            post_logger.info(f"Incoming request: {request.url} {request.method} {request.data}")

            # Store the incoming request to variable data
            data = request.get_json()

            # Store the incoming request to database
            save_request(data)

        else:
            pass
    except Exception as e:
        pass

    
@application.route('/', methods=['GET'])
def index():
    conversations = IncomingRequest.query.all()
    return render_template('conversation.html', conversations=conversations)


@application.route('/heyoo',methods=['GET','POST'])
def heyoo():

    # complicated
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
            if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
                return "Verification token mismatch", 403
            return request.args["hub.challenge"], 200

    data = request.get_json()

    changed_field = messenger.changed_field(data)
   
    if changed_field == 'messages':

        new_message = messenger.get_mobile(data)
     
        if new_message:

            mobile = messenger.get_mobile(data)
            message_type = messenger.get_message_type(data)
            name = messenger.get_name(data)

         
            if message_type == "text":

                message = messenger.get_message(data).lower()
                message_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['id'] #wamid.HBgMMjU0NzQxNTkwMzMwFQIAERgSMTZCMjIzOTlEMjVFQTE2MjUyAA==

                if not check_message_processed(message_id):
                    print(f"{mobile} sent {message}")
                    try:
                        if "at" in message:
                            messenger.send_message(f"Hi {name} what service would you like today?\n\n1 - Open account\n\n💡type *1* to make your selection 👇🏾", mobile)

                            #Mark the message as processed
                            new_ = IncomingRequest(status='deliiverd', timestamp='', recipient_id='', conversation_id='', message_id=message_id, origin='', billable='', pricing_model='', processed=True)
                            db.session.add(new_)
                            db.session.commit()

                            print('ookkkkk')
                        else:
                            print('not ok')
                    except Exception as e:
                        logger.exception(e)
                else:
                    print(f"{mobile} sent {message} but it's already processed.")
                    

            elif message_type == "interactive":

                message_response = messenger.get_interactive_response(data)
                intractive_type = message_response.get("type")
                message_id = message_response[intractive_type]["id"]
                message_text = message_response[intractive_type]["title"]

                # logging.info(f"Interactive Message; {message_id}: {message_text}")

                try:
                    messenger.send_message(f"{name} sent {message_text}", mobile)
                except Exception as e:
                    # logger.exception(e)
                    pass

            else:

                print(f"{mobile} sent {message_type} ")
                # logging.info(f"{mobile} sent {message_type}")

        else:

            delivery = messenger.get_delivery(data)

            if delivery:
                print(f"Message : {delivery}")
            else:
                print("No new message")
                
    return "ok"

if __name__ == '__main__':

    with application.app_context():
        db.create_all()
    application.run(port=4000)

