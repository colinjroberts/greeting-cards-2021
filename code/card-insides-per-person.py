import pathlib
import os
import csv

"""
This script uses a csv of card recipients and their data as well as custom map files for each person to produce
two files per person: one file contains the map file and the other contains the card text and the arc connecting
the source location to the card destination. The custom map files are expected to be (5.5in x 8.5in; 139.7mm x 215.9mm)
the whole inside of the card including blank space for the text. The two generated files per person are each 11in x 17in 
(279.4mm x 431.8mm) in which the card is rotated and arranged in one corner of the page. Later, the script aggregates
up to 4 of those files onto a single page.

Notes:
- In each input file, it expects 3 layers. Layers 1 and two have all of the geometry to print. Layer 3 is a 
bounding box used for position that gets optionally deleted right at the end.
- It does a little line merging and very little simplifying, but I'm not sure that does much of anything.
- This code should be run from the root folder of the project
- vpype's text method might only handle ASCII characters, it skipped characters with accents. In production, I used 
ASCII letters and added diacritics by hand
- After light effort, I couldn't figure out how to use the vpype Python module, so this script
builds vpype commands and uses os.system() to run everything.
- The extra code for Seattle was to handle a map that was vertical and placed off to the left of the upper part of the card.

This script takes a single svg image (5.5in x 8.5in; 139.7mm x 215.9mm) with three layers and creates an 11in x 17in 
(279.4mm x 431.8mm) composite with 2 layers with 4 copies of the card, one in each corner. Layer 1 has all of the geometry to 
print, Layer 3 is a bounding box used for position that gets optionally deleted right at the end. Note, I'm not
sure the line merging and simplifying does much of anything, and on top of that, I'm using saxi to plot them
which does some optimization of its own. I figure it couldn't hurt.

"""

def build_vpype_command_one_card_insides_map(map_filename, page_layout_location, show_hide_box, output_filename):
    
    layer_to_remove = "ldelete 2"
    rotate = "rotate 270"
    write_output = "linesort write " + output_filename

    # Merging Settings
    """Not sure what this does, but it is worth trying"""    
    merge = "splitall linemerge --tolerance 1.2mm"

    # Simplify Settings
    """simplifying greater than .2mm gives poor geometries"""
    simplify = "linesimplify --tolerance 0.2mm"

    command = " ".join(["vpype read", map_filename, "pagesize 5.5inx8.5in", layer_to_remove, merge, simplify, rotate, page_layout_location, show_hide_box, write_output])

    return command


def build_vpype_command_one_card_insides_arctext(map_filename, map_type, distance, units, name, message_text, page_layout_location, show_hide_box, output_filename):
    layer_to_remove = "ldelete 1"
    rotate = "rotate 270"
    write_output = "linesort write " + str(output_filename)
    text = ""
    if str(map_type).endswith("seattle"):
        text = f'text --font scripts --position 320 115 --align left --size 26 --wrap 100  "This card travelled at least {distance} {units} to get to you" \
                text --font cursive --position 35 500 --align left --size 28 --wrap 430  "{name}," \
                text --font cursive --position 35 535 --align left --size 28 --wrap 430 "{message_text}" \
                text --font cursive --position 35 715 --align left --size 28 --wrap 430  "Best," \
                text --font cursive --position 35 740 --align left --size 28 --wrap 430  "Colin and Ian" ' 
        
    else:
        text = f'text --font scripts --position 75 330 --align center --size 26 --wrap 375 "This card travelled at least {distance} {units} to get to you"  \
                text --font cursive --position 40 500 --align left --size 28 --wrap 430   "{name},"  \
                text --font cursive --position 40 535 --align left --size 28 --wrap 430  "{message_text}"\
                text --font cursive --position 40 715 --align left --size 28 --wrap 430  "Best," \
                text --font cursive --position 40 740 --align left --size 28 --wrap 430  "Colin and Ian" '

    command = " ".join(["vpype read", map_filename, "pagesize 5.5inx8.5in", layer_to_remove, text, rotate, page_layout_location, show_hide_box, write_output])

    return command


def build_vpype_command_11x17compile(list_of_filenames, output_filename):
    # Combine the individual files
    combining_command = "vpype "

    for file_to_read in list_of_filenames:
        combining_command += "read " + str(file_to_read) + " "

    combining_command += " write " + output_filename

    return combining_command


def main(print_instead_of_run = True):
    # Name files to import
    data_source = pathlib.Path.cwd() / 'data' / 'card-recipients.csv'
    source = pathlib.Path.cwd() / 'inside' / 'person-maps'

    maps_and_files = []
    with open(data_source) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        for row in csv_reader:
            maps_and_files.append((row[0], row[1], (source / pathlib.Path(row[2])), row[3], row[4], row[5]))
            # (salutation name, map-template, name of person's custom map, message, distance, units)

    # Check file paths for validity
    for person in maps_and_files:
        if not os.path.exists(person[2]):
            raise FileNotFoundError(f"Incorrect file path: {person[2]}")

    # Arrange final layout
    """Layout the file to be written on 11x17
    The command in full looks like this: "layout -l -h left -v top rotate 90 11inx17in"
    This method of making the final output requires saving 4 separate files with the svgs positioned 
    in corners, then running another vpype command to read in the 4 options and save a final output
    The variables below set up a string builder that is later iterated through.
    """

    layout_options = ["layout -l -h left -v top 11inx17in", "layout -l -h left -v bottom 11inx17in", "layout -l -h right -v top 11inx17in", "layout -l -h right -v bottom 11inx17in"]
    show_hide_box = "ldelete 3"

    # Create cards in batches of 4, then combine them into one 11x17 page
    # This whole process happens twice, once for the map, then again for the location arc and text
    """Iterate through the 4 placement options saving each file and keeping track of the 4 file names to later merge"""
    for j in range(2):
        # j == 0 - map
        # j == 1 - arctext

        # Process all files, pausing every 4 to merge
        list_of_files_to_merge = []
        iterations = len(maps_and_files)

        for i in range(iterations):
            command = ""
            # if four images have been gathered, combine them
            if (i > 0 and i % 4 == 0):

                if j == 0:
                    this_filename = 'insides-map-11x17-' + str((i-1)//4) + ".svg"
                else:
                    this_filename = 'insides-arctext-11x17-' + str((i-1)//4) + ".svg"

                command = build_vpype_command_11x17compile(list_of_files_to_merge, str(pathlib.Path.cwd() / 'inside' / '11x17' / 'combined' / this_filename))
                
                if print_instead_of_run:
                    print(command)
                else: 
                    os.system(command)
                list_of_files_to_merge = []

            # Create name of output file for this one card
            if j == 0:
                output_filename = "insides-map-onecard-11x17" + "-" + str(i) + ".svg"
            else:
                output_filename = "insides-arctext-onecard-11x17" + "-" + str(i) + ".svg"

            output_filename = str(pathlib.Path.cwd() / 'inside' / '11x17' / 'individual' / output_filename)
    
            # Save image to merge list, then output
            list_of_files_to_merge.append(output_filename)

            # Build the command 
            if j == 0:
                command = build_vpype_command_one_card_insides_map(str(maps_and_files[i][2]), layout_options[i%4], show_hide_box, str(output_filename))
            else:
                command = build_vpype_command_one_card_insides_arctext(str(maps_and_files[i][2]), maps_and_files[i][1], maps_and_files[i][4], maps_and_files[i][5], maps_and_files[i][0], maps_and_files[i][3], layout_options[i%4], show_hide_box, str(output_filename))

            if print_instead_of_run:
                print(command)
            else: 
                os.system(command)

            # if it is the last iteration, and there is at least one image left to combine, do it!
            if i == iterations-1 and len(list_of_files_to_merge)>0: 
                if j == 0:
                    this_filename = 'insides-map-11x17-' + str((i-1)//4) + ".svg"
                else:
                    this_filename = 'insides-arctext-11x17-' + str((i-1)//4) + ".svg"

                command = build_vpype_command_11x17compile(list_of_files_to_merge, str(pathlib.Path.cwd() / 'inside' / '11x17' / 'combined' / this_filename))
                
                if print_instead_of_run:
                    print(command)
                else: 
                    os.system(command)


if __name__ == '__main__':
    main(False)
    

