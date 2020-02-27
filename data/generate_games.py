"""
Requires two folders:
    - landscape_label/
    - landscape_target/

It searches landscape _target/ and if it finds the same image name in the landscape_label folder, initializes a game from it.
"""

import os
import shutil
import json

if not os.path.exists('games/'):
    os.mkdir('games/')

def game_original_target_name(game_id):
    try:
        with open('games/'+game_id+'/flags.json', 'r') as file:
            flags = json.load(file)
            return flags['target_image_original_name']
    except:
        pass
    return ""

def game_is_finished(game_id):
    try:
        with open('games/'+game_id+'/flags.json', 'r') as file:
            flags = json.load(file)
            return flags['finished']
    except:
        pass
    return False

def can_make_game(idx, target_image_path):    
    target_image_original_name = target_image_path.split('/')[-1]    
    for game in [x for x in os.listdir('games/')]:          
        if game_original_target_name(game) == target_image_original_name and not game_is_finished(game):
            print("Cannot regen", idx, "because the game hasn't finished!")
            return False
    return True

def make_game(idx, target_image_path, target_label_path):

    if not can_make_game(idx, target_image_path):
        return

    game_path = os.path.join('games/', str(idx)+'/')
    if os.path.exists(game_path):
        shutil.rmtree(game_path)

    os.mkdir(game_path)    
    shutil.copy(target_image_path, os.path.join(game_path, 'target_image.jpg'))
    shutil.copy(target_label_path, os.path.join(game_path, 'target_label.png'))

    flags = {
        'finished':False,
        'drawer_connected':False,
        'teller_connected':False,
        'is_drawer_turn':False,
        'drawer_uploaded_images':False,
        'num_peaks_left':2,
        'score':0,
        'drawer_email':'',
        'teller_email':'',
        'target_image_original_name':target_image_path.split('/')[-1]
    }

    with open(os.path.join(game_path, 'flags.json'), 'w') as file: json.dump(flags, file)    
    dialog = {'dialog':[]}
    with open(os.path.join(game_path, 'dialog.json'), 'w') as file: json.dump(dialog, file)
    print("Regenerated game:", idx)    
    

for idx, target_image in enumerate([x for x in os.listdir('landscape_target/') if ".jpg" in x]):
    target_path = os.path.join('landscape_target/', target_image)
    label_path = os.path.join('landscape_label/', target_image.replace('jpg', 'png'))
    if os.path.exists(label_path): make_game(idx, target_path, label_path)