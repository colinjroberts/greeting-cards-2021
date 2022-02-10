import pathlib
import os
import csv

"""
This script takes a csv of card info and produces one envelope per person in the list with size
(4 3/8in x 5.75in; 111mm x 146mm)

Notes about code:
- After light effort, I couldn't figure out how to use the vpype Python module, so this script
builds vpype commands and uses os.system() to run everything.
- This code should be run from the root directory of this project.
"""

def build_vpype_envelopes(csv_filename, output_directory):
    """Writes an envelope for every person and address line in a csv"""
    
    list_of_lists_of_data = []
    
    with open(csv_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader, None)
            for row in csv_reader:
                list_of_lists_of_data.append(row)
                    
    # 2 - filename
    # 7 - name
    # 8-11 address lines 1-4
    
    for i, item in enumerate(list_of_lists_of_data):
        if i < 100:  
            write_output = "linesort write " + str(pathlib.Path(output_directory / str(item[2])))

            text = f'text --position 10 25 --align left --size 16 --wrap 400 "Colin and Ian"  \
text --position 10 45 --align left --size 16 --wrap 400  "Return Address 1"  \
text --position 10 65 --align left --size 16 --wrap 400  "Return Address 2" \
text --position 100 250 --align left --size 20 --wrap 430  "{item[7]}" \
text --position 100 275 --align left --size 20 --wrap 430  "{item[8]}" \
text --position 100 300 --align left --size 20 --wrap 430  "{item[9]}" \
text --position 100 325 --align left --size 20 --wrap 430  "{item[10]}" \
text --position 100 350 --align left --size 20 --wrap 430  "{item[11]}"'

            command = " ".join(["vpype pagesize 4.37inx5.75in", text, write_output])

            os.system(command)
            
            
if __name__ == "__main__":
    csv_filename = pathlib.Path.cwd() / 'data' / 'card-recipients.csv'
    output_directory = pathlib.Path.cwd() / 'envelopes'
    build_vpype_envelopes(csv_filename, output_directory)  
    # os.system(build_vpype_envelopes(csv_filename, output_directory))