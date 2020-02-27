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
from score import Score

class GameManager:

    @classmethod
    def append_message(self, game_id, text, user_type):
        path = os.path.join('data/games/', game_id, 'dialog.json')
        if not os.path.exists(path): return

        with open(path, 'r') as file:
            dialog = json.load(file)

            curr_idx = self.get_current_turn_idx(game_id)
            if user_type.lower() == 'drawer': curr_idx -= 1

            turn = {'text':text, 'user_type':user_type, 'turn_idx':curr_idx}
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
            image = cv2.resize(image, (350, 350))
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
    def get_most_recent_drawer_images(self, game_id):
        path = os.path.join(os.getcwd(), 'data/games/', game_id)
        def extract_idx(text):
            try:
                return int(re.findall(r'\d+', text)[0])
            except Exception as error:
                # print("\nError extracting int in 'update_peek_image'\n")
                return 0
        synthetic = [x for x in os.listdir(path) if 'synthetic_image' in x]
        if len(synthetic) < 1: return {'synthetic':'', 'semantic':''}
        synthetic = sorted(synthetic, key=lambda x: extract_idx(x), reverse=False)
        synthetic = synthetic.pop()
        synthetic = os.path.join(os.getcwd(), 'data/games/', game_id, synthetic)

        semantic = [x for x in os.listdir(path) if 'semantic_image' in x]
        if len(semantic) < 1: return {'synthetic':'', 'semantic':''}
        semantic = sorted(semantic, key=lambda x: extract_idx(x), reverse=False)
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
        image = Image.open(semantic)
        image = image.convert('L').resize((350, 350))    
        image = np.array(image)          

        # Get target label
        path = os.path.join(os.getcwd(), 'data/games/', game_id, 'target_label.png')
        ground_truth = Image.open(path).convert('L').resize((350, 350))
        ground_truth = np.array(ground_truth)

        # calc score
        results = Score().calc(ground_truth, image)
        return results['co_draw']



