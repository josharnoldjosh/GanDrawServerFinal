import os
import json
from PIL import Image
import cv2
import base64
import io
from add_text import *
import shutil
import re
from uuid import uuid4
import time
import numpy as np
from score import Score, convert_GAUGAN2MASK
from collections import Counter

class CountGames:
    
    def __init__(self):
        path = os.path.join(os.getcwd(), 'data/finished_games/')
        self.games = [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
        self.target_images = []

        for game_id in self.games:            
            path = os.path.join(os.getcwd(), 'data/finished_games/', game_id, 'flags.json')
            with open(path, 'r') as file:
                data = json.load(file)
                self.target_images += [data['target_image_original_name']]

        self.counts = Counter(self.target_images)
    
    def count(self, target_image):
        if target_image in self.counts.keys():
            return self.counts[target_image]
        return 0

class GenGames:

    @classmethod
    def regen(self):
        counter = CountGames()
        GenGames.ensure_dirs()

        for idx, target_image in GenGames.enumerate_games():            
            (target_path, label_path) = GenGames.target_label_paths(target_image)

            if os.path.exists(target_path) and GenGames.can_make_game(idx, target_path):

                if counter.count(target_image) < 5:
                    print(idx, "has current count", counter.count(target_image), "regenerating...")
                    GenGames.make_game(idx, target_path, label_path)
                else:
                    print(idx, "has count", counter.count(target_image), "no need to regenerate!")

    @classmethod
    def target_label_paths(self, target_image):
        target_path = os.path.join(os.getcwd(), 'data/','landscape_target/', target_image)
        label_path = os.path.join(os.getcwd(), 'data/', 'landscape_label/', target_image.replace('jpg', 'png'))
        return (target_path, label_path)

    @classmethod
    def enumerate_games(self):
        return enumerate([x for x in os.listdir(os.path.join(os.getcwd(), 'data/', 'landscape_target/')) if ".jpg" in x])

    @classmethod
    def ensure_dirs(self):
        for item in ['landscape_target', 'landscape_label', 'games']:
            path = os.path.join(os.getcwd(), 'data/', item)
       
    @classmethod
    def can_make_game(self, idx, target_image_path):    
        target_image_original_name = target_image_path.split('/')[-1]    
        all_games_path = os.path.join(os.getcwd(), 'data/games/')
        for game in os.listdir(all_games_path):  
            if not os.path.isdir(os.path.join(os.getcwd(), 'data/games/', game)): continue

            if GenGames.game_original_target_name(game) == target_image_original_name and not GenGames.is_game_finished(game):
                print("Cannot regen", idx, "because the game hasn't finished!")
                return False          
        return True

    @classmethod
    def game_original_target_name(self, game_id):
        try:
            path = os.path.join(os.getcwd(), 'data/games/', game_id, 'flags.json')
            with open(path, 'r') as file:
                flags = json.load(file)
                return flags['target_image_original_name']
        except Exception as error:
            print(error)
        return ""

    @classmethod
    def is_game_finished(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id, 'flags.json')
        try:
            with open(path, 'r') as file:
                flags = json.load(file)
                return flags['finished']
        except Exception as error:
            print(error)
        return False

    @classmethod
    def make_game(self, idx, target_image_path, target_label_path):
        game_path = os.path.join(os.getcwd(), 'data/', 'games/', str(idx)+'/')
        if os.path.exists(game_path): shutil.rmtree(game_path)

        os.mkdir(game_path)    
        shutil.copy(target_image_path, os.path.join(game_path, 'target_image.jpg'))
        shutil.copy(target_label_path, os.path.join(game_path, 'target_label.png'))

        flags = {
            'finished':False,        
            'is_drawer_turn':False,
            'drawer_uploaded_images':False,
            'num_peaks_left':2,
            'score':0,        
            'target_image_original_name':target_image_path.split('/')[-1]
        }

        with open(os.path.join(game_path, 'flags.json'), 'w') as file: json.dump(flags, file)    
        dialog = {'dialog':[]}
        with open(os.path.join(game_path, 'dialog.json'), 'w') as file: json.dump(dialog, file)

class FinishedGames:

    @classmethod
    def move(self):    
        self.ensure_dir()    
        path = os.path.join(os.getcwd(), 'data/games/')
        for game_id in [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]:
            if self.is_game_finished(game_id):                
                self.move_folder(game_id)

    @classmethod
    def ensure_dir(self):
        path = os.path.join(os.getcwd(), 'data/finished_games/')
        if not os.path.exists(path): os.mkdir(path)

    @classmethod
    def is_game_finished(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id, 'flags.json')
        try:
            with open(path, 'r') as file:
                flags = json.load(file)
                return flags['finished']
        except Exception as error:
            print(error)
        return False

    @classmethod
    def move_folder(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id)
        output_path = os.path.join(os.getcwd(), 'data/finished_games/' + str(uuid4())[:8] + '/')
        shutil.move(path, output_path)

class GameManager:

    @classmethod
    def append_message(self, game_id, text, user_type, email):
        path = os.path.join('data/games/', game_id, 'dialog.json')
        if not os.path.exists(path): return

        with open(path, 'r') as file:
            dialog = json.load(file)

            curr_idx = self.get_current_turn_idx(game_id)
            if user_type.lower() == 'drawer': curr_idx -= 1

            turn = {'text':text, 'user_type':user_type, 'turn_idx':curr_idx, 'email':email}
            dialog['dialog'].append(turn)            
        
            with open(path, 'w') as file:
                json.dump(dialog, file)    

    @classmethod
    def get_dialog(self, game_id, user_type):
        path = os.path.join('data/games/', game_id, 'dialog.json')
        if not os.path.exists(path): return "[Error loading data]"

        result = ""

        with open(path, 'r') as file:
            dialog = json.load(file)
            for turn in dialog['dialog']:                
                result += turn['user_type'] + ': ' + turn['text'] + '\n\n'            
            return result

        return result

    @classmethod
    def drawer_uploaded_images(self, game_id):
        path = os.path.join('data/games/', game_id, 'flags.json')
        with open(path, 'r') as file:
            flags = json.load(file)
            return flags["drawer_uploaded_images"]

    @classmethod
    def set_flags(self, game_id, key, value=None, toggle=False):
        flags_path = os.path.join('data/games/', game_id, 'flags.json')
        with open(flags_path, 'r') as file:
            flags = json.load(file)

            if toggle:
                flags[key] = not flags[key]            
            else:
                flags[key] = value                            

            with open(flags_path, 'w') as file:
                json.dump(flags, file)                
        return

    @classmethod
    def read_flags(self, game_id, key):
        path = os.path.join('data/games/', game_id, 'flags.json')
        with open(path, 'r') as file:
            flags = json.load(file)
            return flags[key]

    @classmethod
    def get_current_turn_idx(self, game_id):
        """
        Returns an Int.
        """
        path = os.path.join('data/games/', game_id, 'dialog.json')
        current_turn_idx = -1;
        with open(path, 'r') as file:
            dialog = json.load(file)
            for turn in dialog['dialog']: current_turn_idx = max(current_turn_idx, turn['turn_idx'])                
        return current_turn_idx+1
        
    @classmethod
    def get_target_image_and_label(self, game_id):
        
        def target_image(game_id):
            imgByteArr = io.BytesIO()
            path = os.path.join(os.getcwd(), 'data/games/', game_id, 'target_image.jpg')        
            im = Image.open(path)
            im.save(imgByteArr, format='PNG')        
            return 'data:image/png;base64,'+base64.b64encode(imgByteArr.getvalue()).decode('ascii')    

        def target_label(game_id):
            path = os.path.join('data/games/', game_id, 'target_label.png')
            image = cv2.imread(path)            
            text_mask = PutingText2Mask(image)
            image = Image.fromarray(text_mask)
            buffered = io.BytesIO()
            image.save(buffered, format="png")        
            img_str = 'data:image/png;base64,'+base64.b64encode(buffered.getvalue()).decode('ascii')
            return img_str

        return {'target_image':target_image(game_id), 'target_label':target_label(game_id)}

    @classmethod
    def copy_tmp_images(self, game_id, path):
        target_image_path = os.path.join(path, game_id+'_target_image.jpg')
        target_label_path = os.path.join(path, game_id+'_target_label.png')
        current_turn = self.get_current_turn_idx(game_id)
        shutil.copyfile(target_image_path, os.path.join(os.getcwd(), 'data/games', game_id, 'synthetic_image_'+str(current_turn)+'.jpg'))
        shutil.copyfile(target_label_path, os.path.join(os.getcwd(), 'data/games', game_id, 'semantic_image_'+str(current_turn)+'.png'))
        return

    @classmethod
    def get_peek_image(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id, 'peek.jpg')
        if not os.path.exists(path): return ""
        
        imgByteArr = io.BytesIO()
        im = Image.open(path)
        im.save(imgByteArr, format='JPEG')   
        return 'data:image/png;base64,'+base64.b64encode(imgByteArr.getvalue()).decode('ascii')

    @classmethod
    def extract_idx(self, text):
        try:
            return int(re.findall(r'\d+', text)[0])
        except Exception as error:
            print("\nError extracting int in 'update_peek_image'\n", error)
            return 0

    @classmethod
    def get_most_recent_drawer_images(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id)
        synthetic = [x for x in os.listdir(path) if 'synthetic_image' in x]
        if len(synthetic) < 1: return {'synthetic':'', 'semantic':''}
        synthetic = sorted(synthetic, key=lambda x: GameManager.extract_idx(x), reverse=False)
        synthetic = synthetic.pop()
        synthetic = os.path.join(os.getcwd(), 'data/games/', game_id, synthetic)

        semantic = [x for x in os.listdir(path) if 'semantic_image' in x]
        if len(semantic) < 1: return {'synthetic':'', 'semantic':''}
        semantic = sorted(semantic, key=lambda x: GameManager.extract_idx(x), reverse=False)
        semantic = semantic.pop()
        semantic = os.path.join(os.getcwd(), 'data/games/', game_id, semantic)

        return {'synthetic':synthetic, 'semantic':semantic}

    @classmethod
    def update_peek_image(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id)
        image = GameManager.get_most_recent_drawer_images(game_id)['synthetic']
        if image == '': return None

        intput_path = os.path.join(path, image)
        output_path = os.path.join(path, "peek.jpg")

        try:
            os.remove(output_path)
        except:
            pass

        shutil.copyfile(intput_path, output_path)

        stamp = str(uuid4())[:4]
        with open(output_path.replace('peek.jpg', 'peek_'+stamp+'.txt'), 'w') as file: file.writelines([str(time.time())])
        
    @classmethod
    def score(self, game_id):

        # Get semantic input
        semantic = GameManager.get_most_recent_drawer_images(game_id)['semantic']
        if semantic == '':return 0
        image = cv2.imread(semantic)
        image = image[0:512, 0:512]     
        image = convert_GAUGAN2MASK(image)   

        # Get target label
        path = os.path.join(os.getcwd(), 'data/games/', game_id, 'target_label.png')        
        ground_truth = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        ground_truth = ground_truth[0:512, 0:512]     

        # calc score
        results = Score().calc(ground_truth, image)

        # Update score
        GameManager.set_flags(game_id, 'score', results['co_draw'])

        return results['co_draw']

    @classmethod
    def unique_request(self):
        return str(uuid4())[:4]

    @classmethod
    def load_games(self):        
        all_games = os.listdir(os.path.join(os.getcwd(), 'data/games/'))        
        all_games = [x for x in all_games if os.path.isdir(os.path.join(os.getcwd(), 'data/games', x))]
        all_games = sorted(all_games, key=lambda text:GameManager.extract_idx(text))
        return all_games

    @classmethod
    def game_exists(self, game_id):
        path = os.path.join('data/games', game_id)
        if os.path.exists(path): return True
        return False

    @classmethod
    def connection_exists(self, game_id, user_type):
        if not os.path.exists('connections/'): os.mkdir('connections/')
        
        all_files = [x for x in os.listdir('connections') if ".json" in x]

        for json_file in all_files:
            with open('connections/'+json_file, 'r') as file:
                data = json.load(file)
                if data['game_id'] == game_id and data['user_type'].lower() == user_type.lower():
                    return True

        return False

    @classmethod
    def connection_exists_with_email(self, game_id, email):
        if not os.path.exists('connections/'): os.mkdir('connections/')

        all_files = [x for x in os.listdir('connections') if ".json" in x]

        for json_file in all_files:
            with open('connections/'+json_file, 'r') as file:
                data = json.load(file)
                if data['game_id'] == game_id and data['email'].lower() == email:
                    return True

        return False

    @classmethod
    def find_game(self, email, user_type):
        if not os.path.exists('connections/'): os.mkdir('connections/')

        # Get email     
        email = email.split('@')[0]
        if len(email) < 1: return '/error'
        
        for game_id in GameManager.load_games():
            is_finished = GameManager.read_flags(game_id, "finished")            

            if is_finished or GameManager.connection_exists(game_id, user_type) or GameManager.connection_exists_with_email(game_id, email):
                continue

            return '/' + email + "/" + game_id + "/" + user_type

        return "/error"

    @classmethod
    def add_connection(self, sid, game_id, user_type, email):
        if not os.path.exists('connections/'): os.mkdir('connections/')

        data = {'game_id':game_id, 'user_type':user_type.lower(), 'email':email.lower()}
        path = os.path.join('connections/', sid+'.json')
        with open(path, 'w') as file:
            json.dump(data, file)
        return

    @classmethod
    def remove_connection(self, sid):
        if not os.path.exists('connections/'): os.mkdir('connections/')

        path = os.path.join('connections/', sid+'.json')
        try:
            os.remove(path)
        except:
            pass

    @classmethod
    def prune_finished_games(self):
        FinishedGames.move()
        GenGames.regen()
