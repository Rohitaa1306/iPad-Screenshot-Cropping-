import os
import re
from datetime import datetime
from glob import iglob

# Get list of all folders in the current directory
ppt_folders = [f for f in iglob(r'C:/Users/u248361/OneDrive - Baylor College of Medicine/Desktop/GNSM Screenshots Temp/Cropped Images/*', recursive=True) if os.path.isdir(f)]
print(ppt_folders)

for ppt_folder in ppt_folders:
    # Filter out folders that don't match the pattern
    day_folders = [f.replace('\\', '/') for f in iglob(fr'{ppt_folder}/*', recursive=True) if os.path.isdir(f)]
    pattern = re.compile(r'P3-3\d{1}(\d{2})_T(\d{1})_(\d+-\d+-\d+) Cropped')
    filtered_day_folders = [f for f in day_folders if re.search(pattern, f)]
    #print(filtered_folders)

    # Sort folders by date
    filtered_day_folders.sort(key=lambda s: datetime.strptime(f'{re.search(pattern, s).group(3)}', '%m-%d-%y'))

    # Rename folders
    for i, folder in enumerate(filtered_day_folders, start=1):
        match = re.search(pattern, folder)
        replacement_pattern = rf"Week {match.group(2)} Day {i} {match.group(3).replace('-', '.')}"
        #print(folder)
        print(re.sub(pattern, replacement_pattern, folder))
        os.rename(folder, re.sub(pattern, replacement_pattern, folder))
