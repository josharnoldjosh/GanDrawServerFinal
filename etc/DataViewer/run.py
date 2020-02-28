from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import os
import re
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def root():    
    return render_template('index.html')

@socketio.on('view_data')   
def view_data(message):
    
    def extract_num(utt):        
        return int(re.findall(r'\d+', utt)[-1])        

    def utt(folder):
        utt_arr = []
        path = os.path.join('static/finished_games/', folder, 'dialog.json')
        with open(path, 'r') as file:
            data = json.load(file)
            for turn in data['dialog']:
                utt_arr += [turn['user_type'] + ": " + turn['text']]
        utt_arr.reverse()
        return utt_arr

    def target_image(folder):
        return "/static/finished_games/" + folder + "/target_image.jpg"

    def synthetic_images(folder):
        synthetic_images = [x for x in os.listdir('static/finished_games/'+folder+'/') if "synthetic_" in x]        
        synthetic_images = sorted(synthetic_images, key=lambda x: extract_num(x))
        return ['/static/finished_games/'+folder+'/'+x for x in synthetic_images]

    data = []

    for folder in [x for x in os.listdir('static/finished_games/') if "DS" not in x]:
        result = {
            "utt":utt(folder),
            "target_image":target_image(folder),
            "synthetic_images":synthetic_images(folder)
        }
        data.append(result)        

    # Send message back
    emit('all_data', {"data":data})

if __name__ == '__main__':
    """ Run the app. """
    socketio.run(app, port=3000)