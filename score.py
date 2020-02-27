import numpy as np
from scipy import ndimage
from itertools import permutations
import cv2
import matplotlib.pyplot as plt
from math import sqrt
from skimage import io, morphology, measure
import numpy as np

GAUGAN2LABEL = {
    156: {"name": "sky", "color": np.array([221, 238, 156])},
    110: {"name": "dirt", "color": np.array([40, 110, 110])},
    # 124: {"name": "gravel", "color": np.array([163, 164, 153])},
    135: {"name": "mud", "color": np.array([111, 113, 135])},
    14: {"name": "sand", "color": np.array([0, 153, 153])},
    105: {"name": "clouds", "color": np.array([105, 105, 105])},
    119: {"name": "fog", "color": np.array([29, 186, 119])},
    126: {"name": "hill", "color": np.array([100, 200, 126])},
    134: {"name": "mountain", "color": np.array([100, 150, 134])},
    147: {"name": "river", "color": np.array([200, 100, 147])},
    149: {"name": "rock", "color": np.array([50, 100, 149])},
    154: {"name": "sea", "color": np.array([218, 198, 154])},
    158: {"name": "snow", "color": np.array([170, 158, 158])},
    161: {"name": "stone", "color": np.array([100, 161, 161])},
    177: {"name": "water", "color": np.array([255, 200, 177])},
    96: {"name": "bush", "color": np.array([50, 110, 96])},
    118: {"name": "flower", "color": np.array([0, 0, 118])},
    123: {"name": "grass", "color": np.array([0, 200, 123])},
    162: {"name": "straw", "color": np.array([235, 163, 162])},
    168: {"name": "tree", "color": np.array([50, 200, 168])},

    # 181: {"name": "wood", "color": np.array([66, 18, 120])}
}

# GAUGAN2LABEL = {
#     211: {"name": "sky", "label": 156},
#     102: {"name": "dirt", "label": 110},
#     119: {"name": "mud", "label": 135},
#     135: {"name": "sand", "label": 14},
#     105: {"name": "clouds", "label": 105},
#     148: {"name": "fog", "label": 119},
#     166: {"name": "hill", "label": 126},
#     139: {"name": "mountain", "label": 134},
#     125: {"name": "river", "label": 147},
#     108: {"name": "rock", "label": 149},
#     187: {"name": "sea", "label": 154},
#     159: {"name": "snow", "label": 158},
#     154: {"name": "stone", "label": 161},
#     199: {"name": "water", "label": 177},
#     98: {"name": "bush", "label": 96},
#     35: {"name": "flower", "label": 118}
# }

def convert_GAUGAN2MASK(gaugan_image):
    label_masks = np.zeros((gaugan_image.shape[0], gaugan_image.shape[1]), dtype='uint8')
    #print(label_masks.shape)
    #label_index = np.where(np.all(drawer_raw == np.array([221, 238, 156]), axis=-1))
    for label, gaugan_info in GAUGAN2LABEL.items():
        label_index = np.where(np.all(gaugan_image == gaugan_info['color'], axis=-1))
        # if label_index.size:
        #     print(gaugan_info["name"])
        if label_index[0].size > 0:
            label_masks[label_index] = label
    return label_masks

class Score:
    def calc(self, ground_truth_image, drawer_image):        
        if ground_truth_image[0][0] == 1 or ground_truth_image.shape != drawer_image.shape:
            print("SHAPES NOT EQUAL OR IMAGE DOES NOT EXIST")
            return {"pixel_acc":0, "mean_acc":0, "mean_iou":0, "co_draw":0}

        # pixel_accuracy = self.pixel_accuracy(ground_truth_image, drawer_image, 182)     
        # mean_accuracy = self.mean_accuracy(ground_truth_image, drawer_image, 182)
        # mean_IoU = self.mean_IoU(ground_truth_image, drawer_image, 182)     
        co_draw_metric = self.gaugancodraw_eval_metrics(drawer_image, ground_truth_image, 182)        

        return {"pixel_acc":0, "mean_acc":0, "mean_iou":0, "co_draw":co_draw_metric}

    def _fast_hist(self, label_true, label_pred, n_class):
        mask = (label_true >= 0) & (label_true < n_class)
        hist = np.bincount(
            n_class * label_true[mask].astype(int) + label_pred[mask],
            minlength=n_class ** 2,
        ).reshape(n_class, n_class)        
        return hist

    def pixel_accuracy(self, label_gt, label_pred, n_class):
        hist = np.zeros((n_class, n_class))
        #loop throught the matrix row by row
        for lt, lp in zip(label_gt, label_pred):
            hist += self._fast_hist(lt.flatten(), lp.flatten(), n_class)
        #The [i,j] the element in hist indicate the number of values when gt_matrix = i and pred_matrix =j 
        acc = np.diag(hist).sum() / hist.sum()
        return acc

    def mean_accuracy(self, label_gt, label_pred, n_class):
        hist = np.zeros((n_class, n_class))
        #loop throught the matrix row by row
        for lt, lp in zip(label_gt, label_pred):
            hist += self._fast_hist(lt.flatten(), lp.flatten(), n_class)
        #The [i,j] the element in hist indicate the number of values when gt_matrix = i and pred_matrix =j 
        acc_cls = np.diag(hist) / hist.sum(axis=1)
        acc_cls = np.nanmean(acc_cls)
        return acc_cls

    def mean_IoU(self, label_gt, label_pred, n_class):
        hist = np.zeros((n_class, n_class))        
        for lt, lp in zip(label_gt, label_pred):
            hist += self._fast_hist(lt.flatten(), lp.flatten(), n_class)        
        iu = np.diag(hist) / (hist.sum(axis=1) + hist.sum(axis=0) - np.diag(hist))    
        valid = hist.sum(axis=1) > 0  # added        
        mean_iu = np.nanmean(iu[valid])
        
        return mean_iu


    def find_label_centers(self, image, shared_label, noisy_filter=1000):
        """
          find the centers of the labels in the image
        """
        image_shared = {l:None for l in shared_label}
        #construct the center for draw_shared
        for key in image_shared.keys():
            mask = np.int_((image == key))
            lbl = ndimage.label(mask)[0]
            unique_labels, unique_counts = np.unique(lbl,return_counts=True)
            filtered_labels = unique_labels[np.where(unique_counts > noisy_filter)]
            filtered_labels = filtered_labels[np.where(filtered_labels > 0)]
            
            centers = ndimage.measurements.center_of_mass(mask, lbl, filtered_labels)
            image_shared[key] = centers
        return image_shared

    def relevant_score(self, x,y):
        """
        x and y are two turples of the objects in drawed image and ground truth image.
        """
        
        score_x =  1 if (x[0][0]-y[0][0])*(x[1][0]-y[1][0]) > 0 else 0 
        score_y =  1 if (x[0][1]-y[0][1])*(x[1][1]-y[1][1]) > 0 else 0
        
        return score_x+score_y

    def relevant_eval_metrics(self, draw_raw, gt_raw, d_smooth=False, g_smooth=False, g_smooth_thred=1000, relevant_mode="unknown_count"):
        if d_smooth:
            #replace the river and sea label into water
            draw_smooth = best_smooth_method(draw_raw)
            draw_smooth[np.where(draw_smooth == 147)] = 177
            draw_smooth[np.where(draw_smooth == 154)] = 177
        else:
            draw_smooth = draw_raw

        if g_smooth:
            g_unique_class, g_unique_counts = np.unique(gt_raw, return_counts=True)
            #Need to smooth gt_labels as well

            result = np.where(g_unique_counts > g_smooth_thred) #3000 is a bit too much
            dominant_class = g_unique_class[result].tolist()
            gt_smooth = merge_noisy_pixels(gt_raw,dominant_class)
            gt_smooth[np.where(gt_smooth == 147)] = 177
            gt_smooth[np.where(gt_smooth == 154)] = 177
        else:
            gt_smooth = gt_raw
        
        draw_set = np.unique(draw_smooth).tolist()        
        gt_set = np.unique(gt_smooth).tolist()        
        shared_labels =  set(draw_set).intersection(set(gt_set))        
        
        #Find the centers of each region in shared label
        draw_shared = self.find_label_centers(draw_smooth, shared_labels)
        gt_shared = self.find_label_centers(gt_smooth, shared_labels)

        if relevant_mode == "unknown_count":
            #Find the centers of each region in unshared label
            draw_unshared = self.find_label_centers(draw_smooth, set(draw_set)-shared_labels)
            gt_unshared = self.find_label_centers(gt_smooth, set(gt_set)-shared_labels)
        else:
            draw_unshared = set(draw_set) - shared_labels
            gt_unshared = set(gt_set) - shared_labels
            
        #Resolve the unmatched pairs between draw_shared and gt_shared
        gt_draw_shared = self.pair_objects(draw_shared, gt_shared)
        if len(gt_draw_shared) > 0:
            #decouple the gt_draw_shared to a list of turples
            shared_item_list = []
            for key, value in gt_draw_shared.items():
                for d_center,gt_center in zip(value['draw_center'],value['gt_center']):
                    shared_item_list.append((d_center, gt_center))
            if relevant_mode == "unknown_count":
                #decouple the unshared objects to a list of turples
                unshared_item_list = []
                for key, value in draw_unshared.items():
                    unshared_item_list += value
                for key, value in gt_unshared.items():
                    unshared_item_list += value
            else:
                unshared_item_list = list(draw_unshared)+list(gt_unshared)

            #compute the numerator score
            score = 0
            for x in range(len(shared_item_list)):
                for y in range(x+1, len(shared_item_list)):
                    score += self.relevant_score(shared_item_list[x], shared_item_list[y])
                        
            union = len(unshared_item_list)
            for key, value in gt_draw_shared.items():
                union += value['max_num_objects']            
            intersection = len(shared_item_list)
            if intersection > 1:                
                final_score = score/(union*(intersection-1))
            else:
                final_score = score/union
        else:
            final_score = 0
        return final_score

    def gaugancodraw_eval_metrics(self, label_d, label_gt, n_class, d_smooth=True, g_smooth=True, g_smooth_thred=1000, score_1_mode ="pixelAccuracy", score_2_mode = "unknown"):        

        draw_smooth = label_d
        draw_smooth[np.where(draw_smooth == 147)] = 177
        draw_smooth[np.where(draw_smooth == 154)] = 177        
        
        if g_smooth:
            g_unique_class, g_unique_counts = np.unique(label_gt, return_counts=True)
            #Need to smooth gt_labels as well

            result = np.where(g_unique_counts > g_smooth_thred) #3000 is a bit too much
            dominant_class = g_unique_class[result].tolist()            
            gt_smooth = self.merge_noisy_pixels(label_gt, dominant_class)
            gt_smooth[np.where(gt_smooth == 147)] = 177
            gt_smooth[np.where(gt_smooth == 154)] = 177
        else:
            gt_smooth = label_gt
        
        if score_1_mode == "meanIoU":
            score_1 = self.mean_IoU(gt_smooth,draw_smooth, n_class)
        elif score_1_mode == "pixelAccuracy":
            score_1 = self.pixel_accuracy(gt_smooth, draw_smooth, n_class)
        
        score_2 = self.relevant_eval_metrics(draw_smooth, gt_smooth, relevant_mode=score_2_mode)        
    
        final_score = 2*score_1+3*score_2
        return final_score 

    def pair_objects(self, draw_shared, gt_shared):
        """
        Pair the regions in drawer's image and the regions in groundtruth image based on the mean square distance.
        TODO:
        1. Rethink the way we pair the objects
        """
        gt_draw_shared = {}

        for key in draw_shared.keys():
            #check if the number maps
            if len(draw_shared[key]) == len(gt_shared[key]) and len(draw_shared[key]) == 1:
                gt_draw_shared[key] = {"draw_center": draw_shared[key], "gt_center": gt_shared[key], "max_num_objects": 1}
            else:
                #pair the centers
                pair_regions = []
                pair_index = []
                for i, draw_c in enumerate(draw_shared[key]):
                    for j, gt_c in enumerate(gt_shared[key]):
                        pair_regions.append((draw_c, gt_c))
                        pair_index.append((i,j))
                #group all possible combinations of i,j together
                if len(draw_shared[key]) < len(gt_shared[key]):
                    perm = permutations(range(len(gt_shared[key])),len(draw_shared[key]))
                    pair_candidates = []
                    for p in perm:
                        #form the groups
                        pair_centers = []
                        for i in range(len(draw_shared[key])):
                            current_pair = (i,p[i])
                            current_pair_index = pair_index.index(current_pair)
                            current_pair_centers = pair_regions[current_pair_index]
                            pair_centers.append(current_pair_centers)
                        pair_candidates.append(pair_centers)
                else:
                    perm = permutations(range(len(draw_shared[key])),len(gt_shared[key]))
                    pair_candidates = []
                    for p in perm:
                        #form the groups
                        pair_centers = []
                        for i in range(len(gt_shared[key])):
                            current_pair = (p[i],i)
                            current_pair_index = pair_index.index(current_pair)
                            current_pair_centers = pair_regions[current_pair_index]
                            pair_centers.append(current_pair_centers)
                        pair_candidates.append(pair_centers)
                
                #sort pair_candidates based on their pair sum
                pair_candidates.sort(key = lambda p: sum([sqrt((c[0][0]-c[1][0])**2 + (c[0][1]-c[1][1])**2) for c in p]))
                
                optimal_pair = pair_candidates[0]
                paired_draw_centers = [x[0] for x in optimal_pair]
                paired_gt_centers = [x[1] for x in optimal_pair]

                gt_draw_shared[key] = {"draw_center": paired_draw_centers, "gt_center": paired_gt_centers, "max_num_objects": max(len(draw_shared[key]), len(gt_shared[key]))}
        return gt_draw_shared


    def merge_noisy_pixels(self, sample_matrix, d_class,kernel_width=3, kernel_height=3,sliding_size=1):
        #First extract all the (x,y) positions of a certain label
        i = 0
        j = 0
        converted_pixels = 0
        while i + kernel_width <= sample_matrix.shape[1]:
            while j + kernel_height <= sample_matrix.shape[0]:
                current_window = sample_matrix[j:j+kernel_width,i:i+kernel_height]
                current_window_list = current_window.flatten().tolist()
                # Check whether there is unknown labels in current_window
                current_labels = set(current_window_list)
                if not current_labels.issubset(set(d_class)):
                    #replace the noisy labels with the closes 
                    d_class_subset = list(current_labels.intersection(set(d_class)))
                    # replace the noisy labels with the dominant class 
                    d_class_subset.sort(key = lambda p : current_window_list.count(p), reverse=True)
                    dominant_d_class = d_class_subset[0]
                    sample_matrix[j:j+kernel_width][i:i+kernel_height] = dominant_d_class
                    mask = ~ np.isin(current_window, d_class)
                    converted_pixels += np.sum(mask)
                    current_window[mask] = dominant_d_class
                    sample_matrix[j:j+kernel_width,i:i+kernel_height] = current_window
                j += sliding_size
            i += sliding_size
            j = 0
        return sample_matrix


if __name__ == "__main__":
    print("Debug the scorer")

    #Load the image
    drawer_raw = cv2.imread('semantic_image_3.png')
    
    label_masks = convert_GAUGAN2MASK(drawer_raw)
    print(np.unique(label_masks))
    print(label_masks.shape)

    target_raw = cv2.imread('target_label.png', cv2.IMREAD_GRAYSCALE)[:512, :512]
    print(np.unique(target_raw))

    score_class = Score()
    score = score_class.calc(target_raw, label_masks)
    print(score)

    # drawer_raw_2 = cv2.imread('gaugan_input_1.png', cv2.IMREAD_GRAYSCALE)
    # print(drawer_raw_2[0,0])

    # target_raw = cv2.imread('target_label.png', cv2.IMREAD_GRAYSCALE)
    # print(np.unique(target_raw))