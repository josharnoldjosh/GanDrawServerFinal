"""
- Checks which games are finished and moves them to a different folder. 
- Run "generate_games.py" again after.
"""

import os, json, shutil, uuid

if not os.path.exists('finished_games/'): os.mkdir('finished_games/')

def game_is_finished(game_id):
    try:
        with open('games/'+game_id+'/flags.json', 'r') as file:
            flags = json.load(file)
            return flags['finished']
    except:
        pass
    return False

def move_folder(game_id):
    shutil.move('games/'+game_id, 'finished_games/'+str(uuid.uuid4())[:8])

for game_id in os.listdir('games/'):
    if game_is_finished(game_id):
        move_folder(game_id)

