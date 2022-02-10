import pathlib
import os

"""
This script takes a single svg image (5.5in x 8.5in; 139.7mm x 215.9mm) with three layers and creates two 11in x 17in 
(279.4mm x 431.8mm) composites with 1 layer with 4 copies of the card, one in each corner. 

It expects an svg of size 5.5in x 8.5in (139.7mm x 215.9mm) with 3 layers: Layers 1 and 2 are the geometries to be printed
and layer 3 is a bounding box used for position that gets optionally deleted right at the end. Note, I'm not
sure the line merging and simplifying does much of anything, and on top of that, I'm using saxi to plot them
which does some optimization of its own. I figure it couldn't hurt.

Notes about code:
- After light effort, I couldn't figure out how to use the vpype Python module, so this script
builds vpype commands and uses os.system() to run everything.
- This code should be run from the root directory of this project.
"""

def main():
    # Path of the source svg with 3 layers
    svg_filename = pathlib.Path.cwd() / 'outside' / '11x17' / 'individual' / 'card-outside-with-border.svg'

    for i in range(2):
        
        # Delete the layer you do not want to include (the layer that isn't the name above)
        layer_to_delete = "ldelete "+ str(2-i)

        # Merging
        """Not sure what this does, but it is worth trying"""    
        merge = "splitall linemerge --tolerance 1.2mm"

        # Simplify
        """simplifying greater than .2mm gives poor geometries"""
        simplify = "linesimplify --tolerance 0.2mm"

        # Arrange final layout
        """Layout the file to be written on 11x17
        The command in full looks like this: "layout -l -h left -v top rotate 90 11inx17in"
        This method of making the final output requires saving 4 separate files with the svgs positioned 
        in corners, then running another vpype command to read in the 4 options and save a final output
        The variables below set up a string builder that is later iterated through.
        """
        horizontal_placement_options = ["left", "right"]
        vertical_placement_options = ["top", "bottom"]

        arrange1 = "rotate 270 layout -l -h"
        arrange2 = "-v"
        arrange3 = "11inx17in"

        # Show or hide bounding box
        # show_hide_box = ""  # uncomment this and comment the next line to show bounding box for correcting alignment
        show_hide_box = "ldelete 3"  # uncomment this and comment the line above to hide bounding box for printing

        # Create 4 positions
        """Iterate through the 4 placement options saving each file and keeping track of the 4 file names to later merge
        and creates a separate file for each of the 4 positions, then merges them all together in the end."""
        list_of_files_to_merge = []
        for horizontal_placement in horizontal_placement_options:
            for vertical_placement in vertical_placement_options:
                                
                output_filename = pathlib.Path.cwd() / 'outside' / '11x17' / 'individual' / ('outside-11x17-one-per-page-11x17' + "-layer" + str(i+1) + "-" + horizontal_placement + "-" + vertical_placement + ".svg")
                list_of_files_to_merge.append(output_filename)
                write_output = "write " + str(output_filename)

                command = " ".join(["vpype read", str(svg_filename), "pagesize 5.5inx8.5in", layer_to_delete, merge, simplify, arrange1, horizontal_placement, arrange2, vertical_placement, arrange3, show_hide_box, write_output])

                os.system(command)

        # Combine the individual files
        command = "vpype "
        for file_to_read in list_of_files_to_merge:
            command += "read " + str(file_to_read) + " "

        command += "linesort write " + str(pathlib.Path.cwd() / 'outside' / '11x17' / 'combined' / ('outside-11x17-combined-layer' + str(i+1) + ".svg"))
        
        os.system(command)


if __name__ == '__main__':
    main()