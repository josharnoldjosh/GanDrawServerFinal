"""
Requires two folders:
    - landscape_label/
    - landscape_target/

It searches landscape _target/ and if it finds the same image name in the landscape_label folder, initializes a game from it.
"""

import os
import shutil
import json

if os.path.exists('games/'): shutil.rmtree('games/')
os.mkdir('games/')

def make_game(idx, target_image_path, target_label_path):
    game_path = os.path.join('games/', str(idx)+'/')
    os.mkdir(game_path)    
    shutil.copy(target_image_path, os.path.join(game_path, 'target_image.jpg'))
    shutil.copy(target_label_path, os.path.join(game_path, 'target_label.png'))
    flags = {'finished':False, 'drawer_connected':False, 'teller_connected':False, 'is_drawer_turn':False, 'drawer_uploaded_images':False, 'num_peaks_left':2}
    with open(os.path.join(game_path, 'flags.json'), 'w') as file: json.dump(flags, file)    
    dialog = {'dialog':[]}
    with open(os.path.join(game_path, 'dialog.json'), 'w') as file: json.dump(dialog, file)    
    

for idx, target_image in enumerate([x for x in os.listdir('landscape_target/') if ".jpg" in x]):
    target_path = os.path.join('landscape_target/', target_image)
    label_path = os.path.join('landscape_label/', target_image.replace('jpg', 'png'))
    if os.path.exists(label_path): make_game(idx, target_path, label_path)