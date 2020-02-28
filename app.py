from flask import * 
from flask_socketio import *
from game_manager import GameManager as GM
from english import english

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'tmp/'
socketio = SocketIO(app, logger=True)

@app.route('/')
def root():    
    return render_template('index.html')

@app.route('/error')
def error():    
    return "😨 something may have gone terribly wrong, or terribly great, please try again!"   

@app.route('/<email>/<game_id>/<user_type>')
def game(email, game_id, user_type):    
    
    if not GM.game_exists(game_id): return "Sorry, there is no game to be found at this link :("

    if user_type == "drawer":        
        return render_template('drawer.html', game_id=game_id, email=email)
    else:        
        return render_template('teller.html', game_id=game_id, email=email)

@app.route('/<game_id>/upload', methods=['POST'])
def upload_drawer_images(game_id):
    if request.method == 'POST' and 'target_image' in request.files and 'target_label' in request.files:           
        if '.jpg' in request.files['target_image'].filename and '.png' in request.files['target_label'].filename:
            target_image = request.files['target_image']
            target_image.save(os.path.join(app.config['UPLOAD_FOLDER'], game_id+'_target_image.jpg'))
            target_label = request.files['target_label']
            target_label.save(os.path.join(app.config['UPLOAD_FOLDER'], game_id+'_target_label.png'))
            # OPTIONAL : Stop user from accidently uploading the same image
            GM.copy_tmp_images(game_id, path=app.config['UPLOAD_FOLDER'])
            GM.set_flags(game_id=game_id, key="drawer_uploaded_images", value=True)
            return "success"    
    return 'error'

@socketio.on('find_game')
def find_game(message):
    result = GM.find_game(message['email'], message['user_type'])
    print(result)
    emit('go_to_game', {'href':result})

@socketio.on('join_game')  
def join_game(message):    
    join_room(message['game_id'])
    GM.add_connection(request.sid, message['game_id'], message['user_type'], message['email'])

@socketio.on('leave_game')
def leave_game(message):    
    leave_room(message['game_id'])

@socketio.on('disconnect')  
def user_connected():    
    GM.remove_connection(request.sid)

@socketio.on('get_game_data')  
def send_game_data(message):
    game_id = message['game_id']
    user_type = message['user_type']

    text = GM.get_dialog(game_id, user_type)
    is_drawer_turn = GM.read_flags(game_id, "is_drawer_turn")
    drawer_uploaded_images = GM.drawer_uploaded_images(game_id)
    target_image_and_label = GM.get_target_image_and_label(game_id)
    num_peaks_left = GM.read_flags(game_id, 'num_peaks_left')
    turn_idx = GM.get_current_turn_idx(game_id)
    peek_image = GM.get_peek_image(game_id)
    is_game_finished = GM.read_flags(game_id, 'finished')
    score = GM.score(game_id)

    payload = {
    'text':text,
    'game_id':game_id,
    'is_drawer_turn':is_drawer_turn,
    'drawer_uploaded_images':drawer_uploaded_images,
    'target_image_and_label':target_image_and_label,
    'num_peaks_left':num_peaks_left,
    'turn_idx':turn_idx,
    'peek_image':peek_image,
    'is_game_finished':is_game_finished,
    'score':score
    }

    emit('game_data', payload, broadcast=True, room=game_id)       

@socketio.on('send_message')   
def message_recieved(message):        
    text = message['text']

    check_english = english(text)
    if not check_english['can_send']:
        emit('bad_english', {'text':check_english['info']})
        return

    game_id = message['game_id']    
    user_type = message['user_type']    
    email = message['email']
    GM.append_message(game_id, text, user_type, email)
    GM.set_flags(game_id=game_id, key="is_drawer_turn", toggle=True)
    if user_type.lower() == "drawer":
        GM.set_flags(game_id=game_id, key="drawer_uploaded_images", value=False)
    send_game_data(message)

@socketio.on('peek')
def peek(message):
    game_id = message['game_id']
    num_peeks = GM.read_flags(game_id, 'num_peaks_left')
    GM.set_flags(game_id=game_id, key='num_peaks_left', value=num_peeks-1)
    GM.update_peek_image(game_id=game_id)
    send_game_data(message)

@socketio.on('finish_game')
def finish_game(message):
    game_id = message['game_id']
    GM.set_flags(game_id=game_id, key='finished', value=True)
    send_game_data(message)

if __name__ == '__main__':
    """ Run the app. """    
    socketio.run(app, port=3000, debug=True)