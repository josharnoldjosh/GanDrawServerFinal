from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import os
import re

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
        drawer_utt = sorted(['data/'+folder+'/'+x for x in os.listdir('data/'+folder+'/') if "drawer_" in x], key=lambda x: extract_num(x))
        teller_utt = sorted(['data/'+folder+'/'+x for x in os.listdir('data/'+folder+'/') if "teller_" in x], key=lambda x: extract_num(x))
        for i in range(max(len(drawer_utt), len(teller_utt))):
            try:                
                with open(teller_utt[i], 'r') as file:
                    utt_arr.append(file.readlines()[0].replace('You:', 'Teller:'))
                with open(drawer_utt[i], 'r') as file:
                    utt_arr.append(file.readlines()[0].replace('You:', 'Drawer:'))
            except:
                pass
        
        utt_arr.reverse()
        return utt_arr

    def target_image(folder):
        return "/static/" + folder + "/target_image.jpg"

    def synthetic_images(folder):
        return ['/static/'+folder+'/'+x for x in sorted([x for x in os.listdir('data/'+folder+'/') if "synthetic_" in x], key=lambda x: extract_num(x))]

    data = []

    for folder in [x for x in os.listdir('data/') if "DS" not in x]:
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