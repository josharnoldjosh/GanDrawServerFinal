"""
Author: Mingyang Zhou
"""
import cv2
import numpy as np
import glob
import shutil
import os

#Load a Target Mask
GT_MASKS_DIR = "sample_image/test_edited_img"
GT_MASKS_NAME = "target_image_semantic_79.png"

LABEL2COLOR = {
    156: {"name": "sky", "color": np.array([107, 185, 240])},
    110: {"name": "dirt", "color": np.array([228, 120, 51])},
    124: {"name": "gravel", "color": np.array([163, 164, 153])},
    135: {"name": "mud", "color": np.array([252, 185, 65])},
    14: {"name": "sand", "color": np.array([254, 250, 212])},
    105: {"name": "clouds", "color": np.array([232, 236, 241])},
    119: {"name": "fog", "color": np.array([76, 60, 231])},
    126: {"name": "hill", "color": np.array([190, 128, 82])},
    134: {"name": "mountain", "color": np.array([118, 93, 105])},
    147: {"name": "river", "color": np.array([129, 207, 224])},
    149: {"name": "rock", "color": np.array([115, 101, 152])},
    154: {"name": "sea", "color": np.array([83, 51, 237])},
    158: {"name": "snow", "color": np.array([228, 241, 254])},
    161: {"name": "stone", "color": np.array([106, 107, 97])},
    177: {"name": "water", "color": np.array([65, 131, 215])},
    96: {"name": "bush", "color": np.array([42, 187, 155])},
    118: {"name": "flower", "color": np.array([250, 216, 89])},
    123: {"name": "grass", "color": np.array([135, 211, 124])},
    162: {"name": "straw", "color": np.array([255, 51, 252])},
    168: {"name": "tree", "color": np.array([63, 195, 128])},
    181: {"name": "wood", "color": np.array([66, 18, 120])}
}

def Colorize_Mask(mask):
    labels = np.unique(mask)
    new_mask = mask
    for l in labels:        
        try:
            new_mask[np.where(mask[:, :, 0] == l)] = LABEL2COLOR[l]["color"]
        except:
            pass
    return new_mask, labels

def PutingText2Mask(mask):
    new_mask, labels = Colorize_Mask(mask)

    #Extend the mask to a bigger size
    back_ground = np.uint8(np.zeros((350, 500,3)))
    back_ground[:, :350, :] = new_mask

    #Now Add a corresponding Text in the back_ground
    v_location  = 35
    for l in labels:
        try:
            label_name = LABEL2COLOR[l]["name"]
            label_color = (int(LABEL2COLOR[l]["color"][0]), int(LABEL2COLOR[l]["color"][1]), int(LABEL2COLOR[l]["color"][2]))            
            cv2.putText(back_ground, label_name, (375, v_location),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2, cv2.LINE_AA)
            v_location += 35
        except:
            pass
    return back_ground