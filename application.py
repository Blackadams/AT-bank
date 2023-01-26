# works with both python 2 and 3
from __future__ import print_function
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from heyoo import WhatsApp
from log import post_logger, logger
import json
from datetime import datetime

application = Flask(__name__)

Token = 'EAAMJ83gJl0cBAEHFSqmDPfm43EwIlnJYHrA7hC4VQNrCJjIPhdxg3atSPlrseGnB5kUp8IUzvkawX7sv2J9t6TKaJjd9xXKfHb7cGu6GPT6YM1zNxGQe75WHAN9T9JrKcqSJAeH282cWJ8MjAilGAZAeQxuPu7GJIKZBcCQXcTHq2fGUDFZCr6a2DVab5Mk1jJfRi0eexbUZBwqbr5I0N2GIZAAIcTSAZD'

messenger = WhatsApp(Token, phone_number_id='102212482786354')

VERIFY_TOKEN = "1234"


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
        # message_id = messenger.get_message_id(data)
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
            name1 = messenger.get_name(data)
            name=name1.capitalize()

         
            if message_type == "text":

                message = messenger.get_message(data).lower()

                print(f"{mobile} sent {message}")


                message_id = messenger.get_message_id(data)

                true_id = f'{message_id}=='
              


                # try:

                #     messenger.send_message(f"Hi {name} what service would you like today?\n\n1 - Open account\n\n💡type *1* to make your selection 👇🏾", mobile)
                # except Exception as e:
                #     logger.exception(e)

                if "test" in message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Hi *{name}* what service would you like today?\n\n1 - *Top-up account*\n2 - *Check Balance*\n3 - *Top-up airtime*\n4 - *About Us*\n\n💡type *1 - 4* to make your selection below 👇🏾", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")

                elif "1" in message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Hi *{name}* Top-up successful 👍", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "2" in message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Bankify allows customers to save money in their accounts, which is then used to purchase airtime and resell it. The interest earned from this process is shared with the customer's savings account, providing a unique and convenient way for individuals to manage their finances. 👍", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "3" in message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Bankify allows customers to save money in their accounts, which is then used to purchase airtime and resell it. The interest earned from this process is shared with the customer's savings account, providing a unique and convenient way for individuals to manage their finances. 👍", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "4" in message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"*About Us*\n\n*Welcome to Bankify, where we specialize in creating innovative solutions using Africa's Talking Airtime API. One of our flagship products is a savings wallet chatbot that allows customers to save money in their accounts, which is then used to purchase airtime and resell it. The interest earned from this process is shared with the customer's savings account, providing a unique and convenient way for individuals to manage their finances.*", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                else:
                    print('duplicate')




                    

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

