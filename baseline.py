from copy import deepcopy
from math import ceil
from random import randint, uniform

# blocks number and size
blocks = {'1': [0.85, 0.85], '2': [0.85, 0.43], '3': [0.43, 0.85], '4': [0.43, 0.43],
          '5': [0.22, 0.22], '6': [0.43, 0.22], '7': [0.22, 0.43], '8': [0.85, 0.22],
          '9': [0.22, 0.85], '10': [1.68, 0.22], '11': [0.22, 1.68],
          '12': [2.06, 0.22], '13': [0.22, 2.06]}

# blocks number and name
# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_names = {'1': "SquareHole", '2': "RectFat", '3': "RectFat", '4': "SquareSmall",
               '5': "SquareTiny", '6': "RectTiny", '7': "RectTiny", '8': "RectSmall",
               '9': "RectSmall", '10': "RectMedium", '11': "RectMedium",
               '12': "RectBig", '13': "RectBig"}

# additional objects number and name
additional_objects = {'1': "TriangleHole", '2': "Triangle", '3': "Circle", '4': "CircleSmall"}

# additional objects number and size
additional_object_sizes = {'1': [0.82, 0.82], '2': [0.82, 0.82], '3': [0.8, 0.8], '4': [0.45, 0.45]}

# blocks number and probability of being selected
probability_table_blocks = {'1': 0.08, '2': 0.08, '3': 0.08, '4': 0.08,
                            '5': 0.08, '6': 0.08, '7': 0.08, '8': 0.08,
                            '9': 0.08, '10': 0.08, '11': 0.08,
                            '12': 0.08, '13': 0.04}

# materials that are available
materials = ["wood", "stone", "ice"]

# bird types number and name
bird_names = {'1': "BirdRed", '2': "BirdBlue", '3': "BirdYellow", '4': "BirdBlack", '5': "BirdWhite"}

# bird types number and probability of being selected
bird_probabilities = {'1': 0.35, '2': 0.2, '3': 0.2, '4': 0.15, '5': 0.1}

TNT_block_probability = 0.3

pig_size = [0.5, 0.5]    # size of pigs

platform_size = [0.62, 0.62]     # size of platform sections

edge_buffer = 0         # buffer uesd to push edge blocks further into the structure center (increases stability)

absolute_ground = -3.5          # the position of ground within level

max_peaks = 5           # maximum number of peaks a structure can have (up to 5)
min_peak_split = 10     # minimum distance between two peak blocks of structure
max_peak_split = 50     # maximum distance between two peak blocks of structure

minimum_height_gap = 3.5        # y distance min between platforms
platform_distance_buffer = 0.4  # x_distance min between platforms / y_distance min between platforms and ground structures

# defines the levels area (ie. space within which structures/platforms can be placed)
level_width_min = -3.0
level_width_max = 9.0
level_height_min = -2.0         # only used by platforms, ground structures use absolute_ground to determine their lowest point
level_height_max = 15.0

pig_precision = 0.01                # how precise to check for possible pig positions on ground

min_ground_width = 2.5                      # minimum amount of space allocated to ground structure
ground_structure_height_limit = ((level_height_max - minimum_height_gap) - absolute_ground)/1.5    # desired height limit of ground structures

max_attempts = 100                          # number of times to attempt to place a platform before abandoning it


# generates a list of all possible subsets for structure bottom

def generate_subsets(current_tree_bottom):
    current_distances = []
    subsets = []
    current_point = 0
    while current_point < len(current_tree_bottom)-1:
        current_distances.append(current_tree_bottom[current_point+1][1] - current_tree_bottom[current_point][1])
        current_point = current_point + 1

    # remove similar splits causesd by floating point imprecision
    for i in range(len(current_distances)):
        current_distances[i] = round(current_distances[i], 10)

    split_points = list(set(current_distances))         # all possible x-distances between bottom blocks

    for i in split_points:      # subsets based on differences between x-distances
        current_subset = []
        start_point = 0
        end_point = 1
        for j in current_distances:
            if j >= i:
                current_subset.append(current_tree_bottom[start_point:end_point])
                start_point = end_point
            end_point = end_point + 1

        current_subset.append(current_tree_bottom[start_point:end_point])

        subsets.append(current_subset)

    subsets.append([current_tree_bottom])

    return subsets


# finds the center positions of the given subset

def find_subset_center(subset):
    if len(subset) % 2 == 1:
        return subset[(len(subset)-1)//2][1]
    else:
        return (subset[len(subset)//2][1] - subset[(len(subset)//2)-1][1])/2.0 + subset[(len(subset)//2)-1][1]


# finds the edge positions of the given subset

def find_subset_edges(subset):
    edge1 = subset[0][1] - (blocks[str(subset[0][0])][0])/2.0 + edge_buffer
    edge2 = subset[-1][1] + (blocks[str(subset[-1][0])][0])/2.0 - edge_buffer
    return[edge1, edge2]


# checks that positions for new block dont overlap and support the above blocks

def check_valid(grouping, choosen_item, current_tree_bottom, new_positions):

    # check no overlap
    i = 0
    while i < len(new_positions)-1:
        if (new_positions[i] + (blocks[str(choosen_item)][0])/2) > (new_positions[i+1] - (blocks[str(choosen_item)][0])/2):
            return False
        i = i + 1

    # check if each structural bottom block's edges supported by new blocks
    for item in current_tree_bottom:
        edge1 = item[1] - (blocks[str(item[0])][0])/2
        edge2 = item[1] + (blocks[str(item[0])][0])/2
        edge1_supported = False
        edge2_supported = False
        for new in new_positions:
            if ((new - (blocks[str(choosen_item)][0])/2) <= edge1 and (new + (blocks[str(choosen_item)][0])/2) >= edge1):
                edge1_supported = True
            if ((new - (blocks[str(choosen_item)][0])/2) <= edge2 and (new + (blocks[str(choosen_item)][0])/2) >= edge2):
                edge2_supported = True
        if edge1_supported == False or edge2_supported == False:
            return False
    return True


# check if new block can be placed under center of bottom row blocks validly

def check_center(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_center(subset))
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)


# check if new block can be placed under edges of bottom row blocks validly

def check_edge(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_edges(subset)[0])
        new_positions.append(find_subset_edges(subset)[1])
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)


# check if new block can be placed under both center and edges of bottom row blocks validly

def check_both(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_edges(subset)[0])
        new_positions.append(find_subset_center(subset))
        new_positions.append(find_subset_edges(subset)[1])
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)


# choose a random item/block from the blocks dictionary based on probability table

def choose_item(table):
    ran_num = uniform(0.0, 1.0)
    selected_num = 0
    while ran_num > 0:
        selected_num = selected_num + 1
        ran_num = ran_num - table[str(selected_num)]
    return selected_num


# finds the width of the given structure

def find_structure_width(structure):
    min_x = 999999.9
    max_x = -999999.9
    for block in structure:
        if round((block[1]-(blocks[str(block[0])][0]/2)), 10) < min_x:
            min_x = round((block[1]-(blocks[str(block[0])][0]/2)), 10)
        if round((block[1]+(blocks[str(block[0])][0]/2)), 10) > max_x:
            max_x = round((block[1]+(blocks[str(block[0])][0]/2)), 10)
    return (round(max_x - min_x, 10))


# finds the height of the given structure

def find_structure_height(structure):
    min_y = 999999.9
    max_y = -999999.9
    for block in structure:
        if round((block[2]-(blocks[str(block[0])][1]/2)), 10) < min_y:
            min_y = round((block[2]-(blocks[str(block[0])][1]/2)), 10)
        if round((block[2]+(blocks[str(block[0])][1]/2)), 10) > max_y:
            max_y = round((block[2]+(blocks[str(block[0])][1]/2)), 10)
    return (round(max_y - min_y, 10))


# remove random pigs until number equals the desired amount

def remove_unnecessary_pigs(number_pigs, final_pig_positions):
    removed_pigs = []
    while len(final_pig_positions) > number_pigs:
        remove_pos = randint(0, len(final_pig_positions)-1)
        removed_pigs.append(final_pig_positions[remove_pos])
        final_pig_positions.pop(remove_pos)
    return final_pig_positions, removed_pigs


# add pigs on the ground until number equals the desired amount

def add_necessary_pigs(number_pigs):
    while len(final_pig_positions) < number_pigs:
        test_position = [uniform(level_width_min, level_width_max), absolute_ground]
        pig_width = pig_size[0]
        pig_height = pig_size[1]
        valid_pig = True
        for i in complete_locations:
            if ( round((test_position[0] - pig_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                 round((test_position[0] + pig_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                 round((test_position[1] + pig_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                 round((test_position[1] - pig_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10)):
                valid_pig = False
        for i in final_pig_positions:
            if ( round((test_position[0] - pig_width/2), 10) < round((i[0] + (pig_width/2)), 10) and
                 round((test_position[0] + pig_width/2), 10) > round((i[0] - (pig_width/2)), 10) and
                 round((test_position[1] + pig_height/2), 10) > round((i[1] - (pig_height/2)), 10) and
                 round((test_position[1] - pig_height/2), 10) < round((i[1] + (pig_height/2)), 10)):
                valid_pig = False
        if valid_pig == True:
            final_pig_positions.append(test_position)
    return final_pig_positions


# choose the number of birds based on the number of pigs and structures present within level

def choose_number_birds(final_pig_positions, number_ground_structures, number_platforms):
    number_birds = int(ceil(len(final_pig_positions)/2))
    if (number_ground_structures + number_platforms) >= number_birds:
        number_birds = number_birds + 1
    number_birds = number_birds + 1         # adjust based on desired difficulty
    return number_birds


# identify all possible triangleHole positions on top of blocks

def find_trihole_positions(complete_locations):
    possible_trihole_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        trihole_width = additional_object_sizes['1'][0]
        trihole_height = additional_object_sizes['1'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < trihole_width:
            test_positions = [ [round(block[1], 10), round(block[2] + (trihole_height/2) + (block_height/2), 10)]]
        else:
            test_positions = [ [round(block[1], 10), round(block[2] + (trihole_height/2) + (block_height/2), 10)],
                               [round(block[1] + (block_width/3), 10), round(block[2] + (trihole_height/2) + (block_height/2), 10)],
                               [round(block[1] - (block_width/3), 10), round(block[2] + (trihole_height/2) + (block_height/2), 10)] ]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if ( round((test_position[0] - trihole_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[0] + trihole_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[1] + trihole_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                     round((test_position[1] - trihole_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if ( round((test_position[0] - trihole_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + trihole_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + trihole_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - trihole_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if ( round((test_position[0] - trihole_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + trihole_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + trihole_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - trihole_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if ( round((test_position[0] - trihole_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                         round((test_position[0] + trihole_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                         round((test_position[1] + platform_distance_buffer + trihole_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                         round((test_position[1] - platform_distance_buffer - trihole_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_trihole_positions.append(test_position)

    return possible_trihole_positions


# identify all possible triangle positions on top of blocks

def find_tri_positions(complete_locations):
    possible_tri_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        tri_width = additional_object_sizes['2'][0]
        tri_height = additional_object_sizes['2'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < tri_width:
            test_positions = [ [round(block[1], 10), round(block[2] + (tri_height/2) + (block_height/2), 10)]]
        else:
            test_positions = [ [round(block[1], 10), round(block[2] + (tri_height/2) + (block_height/2), 10)],
                               [round(block[1] + (block_width/3), 10), round(block[2] + (tri_height/2) + (block_height/2), 10)],
                               [round(block[1] - (block_width/3), 10), round(block[2] + (tri_height/2) + (block_height/2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if ( round((test_position[0] - tri_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[0] + tri_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[1] + tri_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                     round((test_position[1] - tri_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if ( round((test_position[0] - tri_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + tri_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + tri_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - tri_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if ( round((test_position[0] - tri_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + tri_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + tri_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - tri_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if ( round((test_position[0] - tri_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                         round((test_position[0] + tri_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                         round((test_position[1] + platform_distance_buffer + tri_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                         round((test_position[1] - platform_distance_buffer - tri_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False

            if blocks[str(block[0])][0] < tri_width:      # as block not symmetrical need to check for support
                valid_position = False
            if valid_position == True:
                possible_tri_positions.append(test_position)

    return possible_tri_positions


# identify all possible circle positions on top of blocks (can only be placed in middle of block)

def find_cir_positions(complete_locations):
    possible_cir_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        cir_width = additional_object_sizes['3'][0]
        cir_height = additional_object_sizes['3'][1]

        # only checks above block's center
        test_positions = [ [round(block[1], 10), round(block[2] + (cir_height/2) + (block_height/2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if ( round((test_position[0] - cir_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[0] + cir_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[1] + cir_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                     round((test_position[1] - cir_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if ( round((test_position[0] - cir_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + cir_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + cir_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - cir_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if ( round((test_position[0] - cir_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + cir_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + cir_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - cir_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if ( round((test_position[0] - cir_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                         round((test_position[0] + cir_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                         round((test_position[1] + platform_distance_buffer + cir_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                         round((test_position[1] - platform_distance_buffer - cir_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_cir_positions.append(test_position)

    return possible_cir_positions


# identify all possible circleSmall positions on top of blocks

def find_cirsmall_positions(complete_locations):
    possible_cirsmall_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        cirsmall_width = additional_object_sizes['4'][0]
        cirsmall_height = additional_object_sizes['4'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < cirsmall_width:
            test_positions = [ [round(block[1], 10), round(block[2] + (cirsmall_height/2) + (block_height/2), 10)]]
        else:
            test_positions = [ [round(block[1], 10), round(block[2] + (cirsmall_height/2) + (block_height/2), 10)],
                               [round(block[1] + (block_width/3), 10), round(block[2] + (cirsmall_height/2) + (block_height/2), 10)],
                               [round(block[1] - (block_width/3), 10), round(block[2] + (cirsmall_height/2) + (block_height/2), 10)] ]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if ( round((test_position[0] - cirsmall_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[0] + cirsmall_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[1] + cirsmall_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                     round((test_position[1] - cirsmall_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if ( round((test_position[0] - cirsmall_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + cirsmall_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + cirsmall_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - cirsmall_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if ( round((test_position[0] - cirsmall_width/2), 10) < round((j[0] + (pig_size[0]/2)), 10) and
                     round((test_position[0] + cirsmall_width/2), 10) > round((j[0] - (pig_size[0]/2)), 10) and
                     round((test_position[1] + cirsmall_height/2), 10) > round((j[1] - (pig_size[1]/2)), 10) and
                     round((test_position[1] - cirsmall_height/2), 10) < round((j[1] + (pig_size[1]/2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if ( round((test_position[0] - cirsmall_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                         round((test_position[0] + cirsmall_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                         round((test_position[1] + platform_distance_buffer + cirsmall_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                         round((test_position[1] - platform_distance_buffer - cirsmall_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_cirsmall_positions.append(test_position)

    return possible_cirsmall_positions


# finds possible positions for valid additional block types

def find_additional_block_positions(complete_locations):
    possible_trihole_positions = []
    possible_tri_positions = []
    possible_cir_positions = []
    possible_cirsmall_positions = []
    if trihole_allowed == True:
        possible_trihole_positions = find_trihole_positions(complete_locations)
    if tri_allowed == True:
        possible_tri_positions = find_tri_positions(complete_locations)
    if cir_allowed == True:
        possible_cir_positions = find_cir_positions(complete_locations)
    if cirsmall_allowed == True:
        possible_cirsmall_positions = find_cirsmall_positions(complete_locations)
    return possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions


# combine all possible additonal block positions into one set

def add_additional_blocks(possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions):
    all_other = []
    for i in possible_trihole_positions:
        all_other.append(['1', i[0], i[1]])
    for i in possible_tri_positions:
        all_other.append(['2', i[0], i[1]])
    for i in possible_cir_positions:
        all_other.append(['3', i[0], i[1]])
    for i in possible_cirsmall_positions:
        all_other.append(['4', i[0], i[1]])

    # randomly choose an additional block position and remove those that overlap it
    # repeat untill no more valid position

    selected_other = []
    while (len(all_other) > 0):
        chosen = all_other.pop(randint(0, len(all_other)-1))
        selected_other.append(chosen)
        new_all_other = []
        for i in all_other:
            if ( round((chosen[1] - (additional_object_sizes[chosen[0]][0]/2)), 10) >= round((i[1] + (additional_object_sizes[i[0]][0]/2)), 10) or
                 round((chosen[1] + (additional_object_sizes[chosen[0]][0]/2)), 10) <= round((i[1] - (additional_object_sizes[i[0]][0]/2)), 10) or
                 round((chosen[2] + (additional_object_sizes[chosen[0]][1]/2)), 10) <= round((i[2] - (additional_object_sizes[i[0]][1]/2)), 10) or
                 round((chosen[2] - (additional_object_sizes[chosen[0]][1]/2)), 10) >= round((i[2] + (additional_object_sizes[i[0]][1]/2)), 10)):
                new_all_other.append(i)
        all_other = new_all_other

    return selected_other


# remove restricted block types from the available selection

def remove_blocks(restricted_blocks):
    total_prob_removed = 0.0
    new_prob_table = deepcopy(probability_table_blocks)
    for block_name in restricted_blocks:
        for key, value in block_names.items():
            if value == block_name:
                total_prob_removed = total_prob_removed + probability_table_blocks[key]
                new_prob_table[key] = 0.0
    new_total = 1.0 - total_prob_removed
    for key, value in new_prob_table.items():
        new_prob_table[key] = value/new_total
    return new_prob_table


# add TNT blocks based on removed pig positions

def add_TNT(potential_positions):
    final_TNT_positions = []
    for position in potential_positions:
        if (uniform(0.0, 1.0) < TNT_block_probability):
            final_TNT_positions.append(position)
    return final_TNT_positions


# write level out in desired xml format

def write_level_xml(folder, complete_locations, selected_other, final_pig_positions, final_TNT_positions, final_platforms, number_birds, current_level, restricted_combinations):

    f = open(folder+"/level-%02d.xml" % current_level, "w")

    f.write('<?xml version="1.0" encoding="utf-16"?>\n')
    f.write('<Level width ="2">\n')
    f.write('<Camera x="0" y="2" minWidth="20" maxWidth="30">\n')
    f.write('<Birds>\n')
    for i in range(number_birds):   # bird type is chosen using probability table
        f.write('<Bird type="%s"/>\n' % bird_names[str(choose_item(bird_probabilities))])
    f.write('</Birds>\n')
    f.write('<Slingshot x="-8" y="-2.5">\n')
    f.write('<GameObjects>\n')

    for i in complete_locations:
        material = materials[randint(0, len(materials)-1)]       # material is chosen randomly
        while [material, block_names[str(i[0])]] in restricted_combinations:     # if material if not allowed for block type then pick again
            material = materials[randint(0, len(materials)-1)]
        rotation = 0
        if (i[0] in (3, 7, 9, 11, 13)):
            rotation = 90
        f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="%s" />\n' % (block_names[str(i[0])], material, str(i[1]), str(i[2]), str(rotation)))

    for i in selected_other:
        material = materials[randint(0, len(materials)-1)]       # material is chosen randomly
        while [material, additional_objects[str(i[0])]] in restricted_combinations:       # if material if not allowed for block type then pick again
            material = materials[randint(0, len(materials)-1)]
        if i[0] == '2':
            facing = randint(0, 1)
            f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="%s" />\n' % (additional_objects[i[0]], material, str(i[1]), str(i[2]), str(facing*90.0)))
        else:
            f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="0" />\n' % (additional_objects[i[0]], material, str(i[1]), str(i[2])))

    for i in final_pig_positions:
        f.write('<Pig type="BasicSmall" material="" x="%s" y="%s" rotation="0" />\n' % (str(i[0]), str(i[1])))

    for i in final_platforms:
        for j in i:
            f.write('<Platform type="Platform" material="" x="%s" y="%s" />\n' % (str(j[0]), str(j[1])))

    for i in final_TNT_positions:
        f.write('<TNT type="" material="" x="%s" y="%s" rotation="0" />\n' % (str(i[0]), str(i[1])))

    f.write('</GameObjects>\n')
    f.write('</Level>\n')

    f.close()
