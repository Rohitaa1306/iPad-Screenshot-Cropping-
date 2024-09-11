""" Credit to Olivia Walch for some code used here from https://github.com/Arcascope/screen-scrape """
import cv2
import os
from glob import iglob
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from ttkthemes import ThemedTk
import pytesseract
from pytesseract import Output
import threading
import numpy as np
from PIL import ImageFont, ImageDraw, Image  

#from iOS_screenshot_cropping_script_info import *

#from thefuzz import *
#from thefuzz import process, fuzz
#from scipy import stats
#import re

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     try:
#         # PyInstaller creates a temp folder and stores path in _MEIPASS
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")

#     return os.path.join(base_path, relative_path)

# pytesseract.pytesseract.tesseract_cmd = resource_path("tesseract/tesseract.exe")

TESSERACT_LOCATION = fr'C:\Users\u255769\Tesseract-OCR\tesseract.exe'

pytesseract.pytesseract.tesseract_cmd = TESSERACT_LOCATION

script_folder = os.path.dirname(os.path.realpath(__file__))

PATCH_IMAGE_LOCATION = fr"{script_folder}/bottom_patch_image.png"
FONT_LOCATION = fr"{script_folder}/SF-Pro-Display-Medium.otf"

class iPadScreenshotCroppingApp(ThemedTk):

    def __init__(self):
        super().__init__()

        def patch_image(image_path, min_height=2160):

                current_image = cv2.imread(image_path)
                curr_height, curr_width, _ = current_image.shape

                if curr_height < min_height:

                    patching_image = cv2.imread(PATCH_IMAGE_LOCATION)
                    new_width = curr_width
                    adjusted_patch_height = min_height - curr_height
                    adjusted_patching_image = patching_image[:adjusted_patch_height, :new_width]
                    # cv2.imshow("1",adjusted_patching_image)
                    # cv2.waitKey(0)
                    new_image = np.zeros((min_height, new_width, 3), dtype=np.uint8)
                    new_image[:curr_height, :] = current_image
                    # cv2.imshow("2",new_image)
                    # cv2.waitKey(0)
                    new_image[curr_height:, :] = adjusted_patching_image

                    return new_image

                return current_image
                
        def get_directory():
            if home_dir := self.selected_directory.get():
                return home_dir
            messagebox.showwarning("Warning", "Please select a directory first.")
            return None
            
        def filter_folders(folders):
            ignore_folders = ["Cropped Images", "Do Not Use", "Battery Activity", "Parental", "iPhone"]
            return [
                f.replace("\\", "/")
                for f in folders
                if os.path.isdir(f) and all(ignored not in f for ignored in ignore_folders)
            ]

        def process_and_save_image(image_path, save_path, *args, phi_already_removed=None, **kwargs):
            cropped_image, rightmost_white_pixel = preprocess_image(image_path)
            #print(rightmost_white_pixel)
            #cv2.imshow("test", cropped_image)
            #cv2.waitKey(0)
            name, title = extract_text(cropped_image, rightmost_white_pixel)
            phi_removed_image = remove_phi(cropped_image, rightmost_white_pixel, name) if not phi_already_removed else cropped_image

            output_path = f"{save_path}/{os.path.basename(image_path)[:-4]} Cropped.png"
            #print(output_path)
            cv2.imwrite(output_path, phi_removed_image)

        def preprocess_image(image_path):
            crop_x = 1620 - 990
            crop_y = 0
            crop_w = 1620
            crop_h = 2160

            name_x = 75
            name_y = 40
            name_w = 415
            name_h = 135

            blue_low = np.array([100, 50, 50])
            blue_high = np.array([130, 255, 255])

            current_image = patch_image(image_path)

            cropped_image = current_image[crop_y:crop_h, crop_x:crop_w]

            name_roi = cropped_image[name_y:name_h, name_x:name_w]
            name_hsv = cv2.cvtColor(name_roi, cv2.COLOR_BGR2HSV)
            name_mask = cv2.inRange(name_hsv, blue_low, blue_high)

            white_pixels = np.argwhere(name_mask > 200)
            if white_pixels.any():
                rightmost_white_pixel = list(white_pixels[np.argmax(white_pixels[:, 1])])[1] + name_x
            else:
                rightmost_white_pixel = name_w

            return cropped_image, rightmost_white_pixel

        def extract_text(cropped_image, rightmost_white_pixel):
            name_x = 75
            name_y = 40
            name_h = 135

            title_x = 325
            title_y = 50
            title_w = 800
            title_h = 125

            name = ""
            title = ""

            name_find = pytesseract.image_to_data(cropped_image[name_y:name_h, name_x - 20:rightmost_white_pixel + 10], config='--psm 7 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.+"', output_type=Output.DICT)
            #print(name_find)

            for i in range(len(name_find["level"])):
                if len(name_find["text"][i]) > 2:
                    name = f'{name} {name_find["text"][i]}'.lstrip()
                    #print(name)

            if name not in ("ScreenTime", "", "SereenTime", "Sereen Time" "reel"):
                title_find = pytesseract.image_to_data(cropped_image[title_y:title_h, rightmost_white_pixel + 10:title_w], config='--psm 7 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.+"', output_type=Output.DICT)
                for i in range(len(title_find["level"])):
                    if len(title_find["text"][i]) > 2:
                        title = f'{title} {title_find["text"][i]}'.lstrip()
                        title = "Total " if title == "" else f"{title} "
            return name, title

        def remove_phi(cropped_image, rightmost_white_pixel, name):
            if name in ("ScreenTime", "", "SereenTime", "Sereen Time", "reel"):
                title_roi = cropped_image[50:125, rightmost_white_pixel + 10:800]
                title_replace_color = get_most_common_color(title_roi)
                image_with_title_removed = cv2.rectangle(
                    cropped_image,
                    [rightmost_white_pixel + 10, 50],
                    [800, 125],
                    title_replace_color,
                    -1,
                )
                return draw_text_on_image(image_with_title_removed, "Daily Total", [cropped_image.shape[1]//2-90, 140//2])
            else:
                name_roi = cropped_image[40:135, 75:rightmost_white_pixel]
                name_replace_color = get_most_common_color(name_roi)
                return cv2.rectangle(
                    cropped_image,
                    [75, 40],
                    [rightmost_white_pixel, 135],
                    name_replace_color,
                    -1,
                )

        def draw_text_on_image(image, text, location):

            # Convert the image to RGB (OpenCV uses BGR) 
            cv2_im_rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)  
            
            # Pass the image to PIL  
            pil_im = Image.fromarray(cv2_im_rgb)  
            
            draw = ImageDraw.Draw(pil_im)  
            # use a truetype font  
            font = ImageFont.truetype(FONT_LOCATION, 40)
            
            x, y = location

            # Draw the text  
            draw.text((x, y), text, font=font, fill=(0,0,0,0))  
            
            # Get back the image to OpenCV  
            return cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

        def get_most_common_color(title_roi):
            unq, count = np.unique(title_roi.reshape(-1, title_roi.shape[-1]), axis=0, return_counts=True)
            sort = np.argsort(count)
            return unq[sort][-1].tolist()

        def do_crop():
            if not (main_folder_path := get_directory()):
                return
            cropped_image_folder = f"{main_folder_path}/Cropped Images/"
            image_types = ["PNG", "JPG", "png", "jpg"]

            participant_folders = filter_folders(iglob(f"{main_folder_path}*/*", recursive=True))
            #print(participant_folders)

            for participant_folder in participant_folders:

                phi_already_removed = False

                if "PHI Already Removed" in participant_folder:
                    phi_already_removed = True

                base_participant_folder = participant_folder.replace(f"{main_folder_path}/", "")
                cropped_participant_folder = cropped_image_folder + base_participant_folder + " Cropped"
                if not os.path.isdir(cropped_participant_folder):
                    os.makedirs(cropped_participant_folder)
                    #print(cropped_participant_folder)
                
                day_folders = filter_folders(iglob(f"{participant_folder}/*", recursive=True))
                #print(day_folders)

                for day_folder in day_folders:
                    base_day_folder = day_folder.replace(f"{participant_folder}", "")
                    #print(base_day_folder)
                    cropped_day_folder = cropped_participant_folder + base_day_folder# + " Cropped"
                    if not os.path.isdir(cropped_day_folder):
                        os.makedirs(cropped_day_folder)
                        #print(cropped_day_folder)

                    images = [f for f in iglob(day_folder + "**/*", recursive=True) if os.path.isfile(f) and (f[-3:] in image_types)]
                    for image_path in images:
                        try:
                            process_and_save_image(image_path, cropped_day_folder, phi_already_removed=phi_already_removed)
                        except Exception as e:
                            print(f"An error occured while processing {image_path}: {e}")
                            continue

            # Rest of your original code
            self.progress_bar.stop()
            self.deiconify()
            self.attributes('-topmost', 1)
            self.attributes('-topmost', 0)
            messagebox.showinfo('', 'Automatic cropping completed.\nYou must double-check to ensure that all PHI was removed.')
            self.run_button.config(state="normal")
            self.select_button.config(state="normal")

        def select_directory():
            home_dir = filedialog.askdirectory().replace("\\","/")
            self.selected_directory.set(home_dir)
            self.directory_label.config(text=home_dir)  # Update the label text

        def start_app():
            self.run_button.config(state="disabled")
            self.select_button.config(state="disabled")
            self.progress_bar.start(10)
            threading.Thread(target=do_crop).start()

        self.style = ttk.Style(self)
        self.style.theme_use("arc")
        self.style.configure('.',font=('Helvetica', 12))
        self.style.configure('TButton', font=('Helvetica', 12, 'bold'), foreground='black')
        self.style.configure('TLabel', font=('Helvetica', 10, 'bold'), background='white')
        self.style.configure("TProgressbar", thickness=30)

        self.title("Auto Crop for iPad Screenshots")

        # Set the window size and position
        self.window_width = 375
        self.window_height = 275
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        x = (self.screen_width - self.window_width) // 2
        y = (self.screen_height - self.window_height) // 2
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        # Create a frame to hold the widgets
        self.frame = tk.Frame(self, padx=20, pady=20)
        self.frame.pack()

        self.selected_directory = tk.StringVar()

        # Select Directory Button
        self.select_button = ttk.Button(self.frame, text="Select Directory", command=select_directory, style='TButton')
        self.select_button.pack(pady=10)

        # Directory Label
        self.directory_label = ttk.Label(self.frame, text="No directory selected", wraplength=325)
        self.directory_label.pack(pady=10)

        # Run App Button
        self.run_button = ttk.Button(self.frame, text="Start Cropping", command=start_app, state="disabled")
        self.run_button.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self.frame, style="TProgressbar", mode="indeterminate", length="125")
        self.progress_bar.pack(pady=10)

        # Update the state of the Run App button when the directory selection changes
        self.selected_directory.trace_add("write", lambda *args: self.run_button.config(state="normal") if self.selected_directory.get() else self.run_button.config(state="disabled"))

if __name__ == "__main__":
    app = iPadScreenshotCroppingApp()
    app.mainloop()

