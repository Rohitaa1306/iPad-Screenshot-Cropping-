import os
import cv2
import numpy as np
from tkinter import filedialog
from glob import iglob
import traceback

script_folder = os.path.dirname(os.path.realpath(__file__))

TOP_PATCH_IMAGE_LOCATION = fr"{script_folder}/top_patch_image.png"
BOTTOM_PATCH_IMAGE_LOCATION = fr"{script_folder}/bottom_patch_image.png"
FONT_LOCATION = fr"{script_folder}/SF-Pro-Display-Medium.otf"

def patch_image_bottom(image_path, min_height=2160):

    try:
        current_image = cv2.imread(image_path)
        curr_height, curr_width, _ = current_image.shape

        if curr_height < min_height:

            patching_image = cv2.imread(BOTTOM_PATCH_IMAGE_LOCATION)
            new_width = curr_width
            adjusted_patch_height = min_height - curr_height
            adjusted_patching_image = patching_image[:adjusted_patch_height, (-new_width):]
            # cv2.imshow("1",adjusted_patching_image)
            # cv2.waitKey(0)
            new_image = np.zeros((min_height, new_width, 3), dtype=np.uint8)
            new_image[:curr_height, :] = current_image
            # cv2.imshow("2",new_image)
            # cv2.waitKey(0)
            new_image[curr_height:, :] = adjusted_patching_image

            return new_image

        return current_image
    
    except:
        print(f"Failed to patch image {image_path}: {traceback.format_exc()}")
        return current_image
    
def patch_image_top(image_path, min_height=2275):

    try:
        current_image = cv2.imread(image_path)
        curr_height, curr_width, _ = current_image.shape

        if curr_height < min_height:
    
            cut_height = min_height - 2160
            patching_image = cv2.imread(TOP_PATCH_IMAGE_LOCATION)
            new_width = curr_width
            adjusted_patch_height = min_height - curr_height + cut_height
            adjusted_patching_image = patching_image[:adjusted_patch_height, (-new_width):]
            # cv2.imshow("1",adjusted_patching_image)
            # cv2.waitKey(0)
            new_image = np.zeros((2160, new_width, 3), dtype=np.uint8)
            new_image[:adjusted_patch_height, :] = adjusted_patching_image
            # cv2.imshow("2",new_image)
            # cv2.waitKey(0)
            current_image_cut = current_image[cut_height:, :]
            # cv2.imshow("3",current_image_cut  )
            # cv2.waitKey(0)
            new_image[adjusted_patch_height:, :] = current_image_cut


            return new_image

        return current_image
    
    except:
        print(f"Failed to patch image {image_path}: {traceback.format_exc()}")
        raise RuntimeError

def filter_folders(folders):
    ignore_folders = ["Patched Images", "Do Not Use", "Battery Activity", "parental"]
    return [
        f.replace("\\", "/")
        for f in folders
        if os.path.isdir(f) and all(ignored not in f for ignored in ignore_folders)
    ]

def patch_and_save_image(location, image_path, save_path):
    if location == "top":
        patched_image = patch_image_top(image_path)
    elif location == "bottom":
        patched_image = patch_image_bottom(image_path)
    else:
        return "Please enter a valid location"
    output_path = f"{save_path}/{os.path.basename(image_path)[:-4]} Patched.png"
    #print(output_path)
    cv2.imwrite(output_path, patched_image)

if __name__ == "__main__":
    
    main_folder_path = filedialog.askdirectory().replace("\\","/")
    try:
        if main_folder_path:
            patched_image_folder = f"{main_folder_path}/Patched Images/"
            image_types = ["PNG", "JPG", "png", "jpg"]

            participant_folders = filter_folders(iglob(f"{main_folder_path}/*", recursive=True))
            #print(participant_folders)

            for participant_folder in participant_folders:
                base_participant_folder = participant_folder.replace(f"{main_folder_path}/", "")
                patched_participant_folder = patched_image_folder + base_participant_folder + " Patched"
                if not os.path.isdir(patched_participant_folder):
                    os.makedirs(patched_participant_folder)
                    #print(cropped_participant_folder)
                
                day_folders = filter_folders(iglob(f"{participant_folder}/*", recursive=True))
                #print(day_folders)

                for day_folder in day_folders:
                    base_day_folder = day_folder.replace(f"{participant_folder}", "")
                    #print(base_day_folder)
                    patched_day_folder = patched_participant_folder + base_day_folder + " Patched"
                    if not os.path.isdir(patched_day_folder):
                        os.makedirs(patched_day_folder)
                        #print(cropped_day_folder)

                    images = [f for f in iglob(day_folder + "**/*", recursive=True) if os.path.isfile(f) and (f[-3:] in image_types) and "parental" not in f]
                    for image_path in images:
                        patch_and_save_image("top", image_path, patched_day_folder)
    except:
        exit()