import os
import json
from collections import Counter
import pprint

games = [x for x in os.listdir('finished_games/') if os.path.isdir('finished_games/'+x)]

target_images = []

for game_id in games:
    path = os.path.join('finished_games/', game_id, 'flags.json')
    with open(path, 'r') as file:
        data = json.load(file)
        target_images += [data['target_image_original_name']]

pp = pprint.PrettyPrinter(depth=6)
counts = Counter(target_images)
pp.pprint(counts)