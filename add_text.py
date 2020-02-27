"""
Author: Mingyang Zhou
"""
import cv2
import numpy as np
import glob
import shutil
import os

#Load a Target Mask
GT_MASKS_DIR = "../sample_image/test_edited_img"
GT_MASKS_NAME = "target_image_semantic_79.png"
# GT_MASKS_DIR = "/Users/kevinz/Desktop"
# GT_MASKS_NAME = "target_label.png"

LABEL2COLOR = {
    156: {"name": "sky", "color": np.array([134, 193, 46])},
    110: {"name": "dirt", "color": np.array([30, 22, 100])},
    124: {"name": "gravel", "color": np.array([163, 164, 153])},
    135: {"name": "mud", "color": np.array([35, 90, 74])},
    14: {"name": "sand", "color": np.array([196, 15, 241])},
    105: {"name": "clouds", "color": np.array([198, 182, 115])},
    119: {"name": "fog", "color": np.array([76, 60, 231])},
    126: {"name": "hill", "color": np.array([190, 128, 82])},
    134: {"name": "mountain", "color": np.array([122, 101, 17])},
    147: {"name": "river", "color": np.array([97, 140, 33])},
    149: {"name": "rock", "color": np.array([90, 90, 81])},
    154: {"name": "sea", "color": np.array([255, 252, 51])},
    158: {"name": "snow", "color": np.array([51, 255, 252])},
    161: {"name": "stone", "color": np.array([106, 107, 97])},
    177: {"name": "water", "color": np.array([0, 255, 0])},
    96: {"name": "bush", "color": np.array([204, 113, 46])},
    118: {"name": "flower", "color": np.array([0, 0, 255])},
    123: {"name": "grass", "color": np.array([255, 0, 0])},
    162: {"name": "straw", "color": np.array([255, 51, 252])},
    168: {"name": "tree", "color": np.array([255, 51, 175])},
    181: {"name": "wood", "color": np.array([66, 18, 120])}
}

def Colorize_Mask(mask):
    """
    convert the mask to image
    """
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
    mask_w = mask.shape[0]
    mask_h = mask.shape[1]

    #Extend the mask to a bigger size
    back_ground = np.uint8(np.zeros((mask_w, mask_h + 150,3)))
    back_ground[:, :mask_h, :] = new_mask

    #Now Add a corresponding Text in the back_ground
    v_location  = mask_w // 10
    for l in labels:
    	label_name = LABEL2COLOR[l]["name"]
    	label_color = (int(LABEL2COLOR[l]["color"][0]), int(LABEL2COLOR[l]["color"][1]), int(LABEL2COLOR[l]["color"][2]))
    	print(label_color)
    	cv2.putText(back_ground, label_name, (mask_w + 25, v_location),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2, cv2.LINE_AA)
    	v_location += mask_w // 10

    return back_ground

# gt_mask = cv2.imread(os.path.join(GT_MASKS_DIR, GT_MASKS_NAME))
# text_mask = PutingText2Mask(gt_mask)

# cv2.namedWindow("GroundTruth Masks")
# cv2.imshow('GT Mask', text_mask)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

