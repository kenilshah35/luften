from flask import Flask, request, jsonify
from flask_cors import CORS

from flask_socketio import SocketIO
from flask_socketio import emit

from openai import OpenAI

from pupils import Pupil, PupilMessage
from pupils import ReadingTutor

import eventlet
import random


from openai.types.beta.threads.run import Run

client = OpenAI()

PROVIDERS = ['OpenAI', 'Groq']

MODELS = [{'OpenAI': ['gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125', 'gpt-4', 'gpt-4-0613', 'gpt-4-turbo-preview', 'gpt-4-turbo']},
          {'Groq': ['msi', 'bef']}]

PREF_PROVIDER = 'OpenAI'
PREF_MODEL = "gpt-3.5-turbo-1106"



app = Flask(__name__)
CORS(app=app)
socketio = SocketIO(app, cors_allowed_origins="*")


def hello(): 
    return "hello"


def get_providers() : 
    return jsonify(PROVIDERS)

def get_models() : 
    return jsonify(MODELS)




def get_reading_tutor() : 

    list_reading_tutors = ReadingTutor.list() # THere should be one or None
    
    reading_tutor = None

    if len(list_reading_tutors) > 0:
        reading_tutor = list_reading_tutors[0]
    
    ret_val = {

    }

    if reading_tutor == None:
        ret_val['assistant_id'] = None
        ret_val['instructions'] = ReadingTutor.__doc__
        ret_val['provider'] = PREF_PROVIDER
        ret_val['real_model'] = PREF_MODEL

    else :
        ret_val['assistant_id'] = reading_tutor.id
        ret_val['instructions'] = reading_tutor.instructions
        ret_val['provider'] = reading_tutor.provider
        ret_val['real_model'] =    reading_tutor.real_model


    return jsonify(ret_val)



def update_reading_tutor() : 

    if request.is_json:
        data = request.get_json()
 
        assistant_id =  data['assistant_id'] 
        provider = data['provider']
        real_model = data['real_model']
        instructions = data['instructions']

        rt = ReadingTutor.retrieve(assistant_id=assistant_id)
        rt.update(provider=provider, real_model=real_model, instructions=instructions)
        print(rt.id)

        return jsonify("ok")
    else:
        print("no")

        return jsonify("error")



def create_reading_tutor(): 
    if request.is_json:
        data = request.get_json()
        provider = data['provider']
        real_model = data['real_model']
        instructions = data['instructions']

        rt = ReadingTutor.create(provider=provider, real_model=real_model, instructions=instructions)
        print(rt.id)

        return jsonify("ok")
    else:
        print("no")

        return jsonify("error")




def delete_pupil(pupil_id):
    Pupil.delete(pupil_id=pupil_id)
    return jsonify("ok")


def create_pupil(pupil_name):

    pupil = Pupil.create(pupil_name=pupil_name)
    return jsonify("ok")




def get_stats_for_pupil_messages(pupil_id):
    # (first_interaction, last_interaction, word_count)

    first_interaction, last_interaction, word_count = (0,0,0)

    return (first_interaction, last_interaction, word_count)


def create_pupil_message():

    if request.is_json:
        data = request.get_json()
        pupil_id = data['pupil_id']
        content = data['content']
        role ='user'

        print(content)
        print(type(pupil_id))
        print(pupil_id)

        pupil_msg = PupilMessage.create(thread_id=pupil_id, content=content, role=role)
        print(pupil_msg.id)
        return jsonify("ok")
    else:
        return jsonify("request is not json")


def retrieve_pupil_run():

    if request.is_json:
        data = request.get_json()
        pupil_id = data['pupil_id']
        run_id = data['run_id']
        run = client.beta.threads.runs.retrieve(run_id=run_id, thread_id=pupil_id)
        print(run)
        return jsonify("ok")
    else:
        return jsonify("error")
    
def create_pupil_run() :

    
    if request.is_json:
        data = request.get_json()
        pupil_id = data['pupil_id']
        assistant_id = data['assistant_id']




        stream = client.beta.threads.runs.create(
                thread_id=pupil_id,
                assistant_id=assistant_id,
                stream=True
        )


        run_id = stream.id



        print(run.id)
        return jsonify(run_id)
    else: 
        return jsonify("error")
    
    


def get_pupil_messages() :
    msgs = []

    order = 'desc'
    limit = 100

    if request.is_json:
        data = request.get_json()
        pupil_id = data['pupil_id']
        if 'order' in data:
            order = data['order']
        if 'limit' in data:
            limit = int(data['limit'])

        _msgs = _get_pupil_messages(thread_id=pupil_id, order=order, limit=limit)
    for msg in _msgs:
        if msg.content != None and msg.content != '' and len(msg.content) > 0:

            print(f"MESSAGE CONTENT : {msg.content} {type(msg.content)} {len(msg.content)}")

            msgs.append((msg.id, msg.content, msg.role))
        
    return jsonify(msgs)

def _get_pupil_messages(thread_id, order, limit) :

    msgs = PupilMessage.list(ignore_cls_type = "1", thread_id=thread_id, order=order, limit=limit)

    return msgs



def get_pupil(pupil_id):
    ret_val  = {
    }
    ret_val['pupil_id'] = None

    pupil = Pupil.retrieve(pupil_id=pupil_id)

    msgs = PupilMessage.list(thread_id=pupil_id)
    print(len(msgs))
    


    if pupil != None:
        ret_val['pupil_id'] = pupil_id
        ret_val['pupil_name'] = pupil.pupil_name
        ret_val['created_at'] = pupil.created_at
        ret_val['pupil_messages_stats'] = get_stats_for_pupil_messages(pupil_id)

    return jsonify(ret_val)

def list_pupils():
    pupils = Pupil.list()
    actual_pupils = []
    for pupil in pupils:
        actual_pupil = Pupil.retrieve(pupil_id=pupil.pupil_id)
        actual_pupils.append((pupil.pupil_id, actual_pupil.pupil_name, actual_pupil.created_at))
    return jsonify(actual_pupils)





def link_functions_to_flask(app:Flask): 
    

    app.add_url_rule("/get_providers", "get_providers", get_providers)
    app.add_url_rule("/get_models", "get_models", get_models)

    

    app.add_url_rule("/get_reading_tutor", "get_reading_tutor", get_reading_tutor)
    app.add_url_rule("/create_reading_tutor", "create_reading_tutor", create_reading_tutor,methods=["POST"])
    app.add_url_rule("/update_reading_tutor", "update_reading_tutor", update_reading_tutor,methods=["POST"])


    app.add_url_rule("/list_pupils", "list_pupils", list_pupils)
    app.add_url_rule("/get_pupil/<pupil_id>", "get_pupil", get_pupil)


    app.add_url_rule("/create_pupil_run", "create_pupil_run", create_pupil_run, methods=["POST"])
    app.add_url_rule("/retrieve_pupil_run", "retrieve_pupil_run", retrieve_pupil_run, methods=["POST"])
    app.add_url_rule("/create_pupil_message", "create_pupil_message", create_pupil_message, methods=["POST"])

    app.add_url_rule("/get_pupil_messages", "get_pupil_messages", get_pupil_messages, methods=["POST"])

    
    app.add_url_rule("/create_pupil/<pupil_name>", "create_pupil", create_pupil, methods=["POST"])
    app.add_url_rule("/delete_pupil/<pupil_id>", "delete_pupil", delete_pupil, methods=['DELETE'])

@socketio.on('connect')
def handle_socketio_connect():
    print(f"Client connected {request.sid}")

@socketio.on("disconnect")
def handle_socketio_disconnect():
    print(f"Client disconnected {request.sid}")


def n_create_pupil_message(sid, data) :

    RANDOM_DELAY_INTERVALS = [7, 11, 13]

    respondAt = data['respondAt']

    pupil_id = data['pupil_id']
    assistant_id = data['assistant_id']
    content = data['content']

    role = "user"

    pupil_msg = PupilMessage.create(thread_id=pupil_id, content=content, role=role)

    stream = client.beta.threads.runs.create(
                thread_id=pupil_id,
                assistant_id=assistant_id,
                stream=True
            )
    
    socketio.emit(respondAt, {'type': 'beginStream'}, room=sid)


    event_count = 0
    for event in stream:
        event_count = event_count + 1

        if event.event == 'thread.message.delta':
#            print(event.data.delta.content[0].text.value)
            socketio.emit(respondAt, 
                          {  
                            'type': 'InStream', 
                            'content': event.data.delta.content[0].text.value
                          },
                         room=sid)

            which_prime = random.randint(0, len(RANDOM_DELAY_INTERVALS) - 1)
            if event_count % RANDOM_DELAY_INTERVALS[which_prime] == 0:
                eventlet.sleep(0)
    eventlet.sleep(0)


    socketio.emit(respondAt, {'type': 'endStream'}, room=sid)



@socketio.on('request_response')
def handle_request_response(data) :
       
    sid = request.sid  # Obtain the client's session ID
    
    if 'cmd' in data:
        if data['cmd'] == 'create_pupil_message': 
            eventlet.spawn(n_create_pupil_message, sid, data)


def link_functions_to_socketio(socketio:SocketIO) :
    socketio.on('connect', handle_socketio_connect)
    socketio.on('disconnect', handle_socketio_disconnect)
    
    


if __name__ == "__main__":

    link_functions_to_flask(app=app)
#    link_functions_to_socketio(socketio=socketio)

    socketio.run(app)



