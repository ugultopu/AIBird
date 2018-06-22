from copy import copy, deepcopy
from pathlib import Path
from pickle import dump
from os import makedirs, remove, path
from shutil import copyfile
from time import ctime

from matlab.engine import start_matlab
from numpy import arange, dot, linalg, zeros
from pandas import DataFrame
from sympy import Abs, Piecewise, solve, symbols, sympify

from baseline import ( absolute_ground,
                       add_TNT,
                       blocks,
                       level_width_min,
                       pig_size,
                       remove_unnecessary_pigs,
                       write_level_xml )

# step
gap = 0.45

number_pigs = 4

x = symbols("x")
y = symbols("y")


class Node(object):
    def __init__(self, arg=None):
        super(Node, self).__init__()
        self.g = 0
        self.h = 0
        self.f = self.g + self.h
        self.parent = arg
        self.block = str(0)
        self.current_structure_height = 0
        self.position = 0  # left
        self.point = 0  # bottom
        self.max_height = 0
        self.is_start = 0  # test if the node is the structure's head
        self.is_head = 0  # test if the node is the row's head

    def print(self):
        print(*self.__dict__.items(), sep=' ')


def generate(structure_height):
    structures = []
    start = Node(None)
    start.g = 0
    start.h = 0
    start.is_start = 1
    start.is_head = 1
    leaf_node = []
    temp_leaf = []
    temp_leaf.append(start)
    leaf_node.append(start)
    step = 1
    height = 0
    signal = True
    while signal:
        leaf_node = copy(temp_leaf)
        temp_leaf.clear()
        print("\n\nstep:", step, "\n\n")
        for leaf in leaf_node:
            # return structure when cannot add more blocks
            print('\n', leaf.current_structure_height,
                  leaf.max_height, structure_height)
            if leaf.current_structure_height+leaf.max_height+0.22 > structure_height or (leaf.max_height == 0 and leaf.is_start != 1):
                print("\nstructure\n")
                structures.append(leaf)
                continue
            leaf.print()
            parents = []
            temp_parents = []
            x1, x2 = limit_boundary(
                leaf.current_structure_height+leaf.max_height)
            print(type(x1), x1, type(x2), x2)
            x1, x2 = round(x1, 2), round(x2, 2)
            sections = arange(x1, x2, gap)
            parents.append(leaf)
            # each position
            for position in sections:
                position = round(position, 2)
                print('\n', position)
                temp_parents.clear()
                # blocks in the same position
                print("parents", len(parents))
                for parent_node in parents:
                    childlist = generate_child(parent_node, step)
                    empty = True
                    if position != x1 and parent_node.is_head == 1:
                        print("ignore", position, x1, parent_node.is_head)
                        continue
                    for child in childlist:
                        if parent_node.is_head != 1 and parent_node.max_height != 0:
                            child.max_height = round(parent_node.max_height, 2)
                        else:
                            child.max_height = round(blocks[child.block][1], 2)

                        # initialize current_structure
                        if position == x1:
                            child.current_structure_height = round(parent_node.current_structure_height +
                                                                   parent_node.max_height, 2)
                        else:
                            child.current_structure_height = round(
                                parent_node.current_structure_height, 2)

                        child.position = round(position, 2)
                        child.point = child.current_structure_height
                        print("--------------------test-----------------\n", child.point,
                              child.block, position, child.current_structure_height)
                        print(check_stability(child, parent_node), (position+blocks[child.block][0]) <= x2, (blocks[child.block][1] <= height_limit(
                            position, child.point)-child.point), position == x1, check_overlap(child, parent_node), '\n')
                        if child.point != parent_node.current_structure_height:
                            continue
                        if check_stability(child, parent_node) and (position+blocks[child.block][0]) <= x2 and (blocks[child.block][1] <= height_limit(position, child.point)-child.point) and (position == x1 or check_overlap(child, parent_node)):
                            child.parent = parent_node
                            if position+blocks[child.block][0] > x2-0.30:
                                child.is_head = 1
                                temp_leaf.append(child)
                            temp_parents.append(child)
                            empty = False
                            child.print()
                    # if no child is suitable
                    if empty:
                        child = Node(parent_node)
                        if position == x1:
                            child.current_structure_height = round(parent_node.current_structure_height +
                                                                   parent_node.max_height, 2)
                        else:
                            child.current_structure_height = round(
                                parent_node.current_structure_height, 2)
                        child.block = str(0)
                        if parent_node.is_head != 1 and parent_node.max_height != 0:
                            child.max_height = round(parent_node.max_height, 2)
                        else:
                            child.max_height = round(0, 2)
                        child.position = round(position, 2)
                        child.point = child.current_structure_height
                        if round(position, 2)+gap >= round(x2, 2):
                            child.is_head = 1
                            temp_leaf.append(child)
                        child.print()
                        temp_parents.append(child)

                parents.clear()
                parents = copy(temp_parents)
        print("----------------------------------")
        print('temp_leaf: ', len(temp_leaf))
        if len(temp_leaf) > 15:
            temp_leaf = prune(temp_leaf, step)
        if len(temp_leaf) == 0:
            signal = False
            break
        print('temp_leaf: ', len(temp_leaf))
        leaf_node.clear()
        step += 1
    print("finished", len(structures))
    structures = prune(structures, step)
    return structures


def construct(nodes, folder):
    makedirs(folder, exist_ok=True)
    structures = []
    i = 4
    for node in nodes:
        with open(folder+'/node'+str(i), 'wb') as filehandler:
            dump(node, filehandler)
        complete_locations = []
        while node.is_start != 1:
            if node.block != str(0):
                complete_locations.append(
                    [int(node.block), round(level_width_min+node.position+round(blocks[node.block][0]/2.0, 3), 3), round(absolute_ground+node.point+round(blocks[node.block][1]/2.0, 3), 3)])
            node = node.parent
        complete_locations, final_pig_positions = find_pig_position(list(reversed(complete_locations)))
        final_pig_positions, removed_pigs = remove_unnecessary_pigs(number_pigs, final_pig_positions)
        final_TNT_positions = add_TNT(removed_pigs)
        write_level_xml(folder, complete_locations, [], final_pig_positions, final_TNT_positions, [], 5, i, [])
        i = i+1
        structures.append(complete_locations.reverse())
        print('\n')


def prune(leaves, step):
    print('\n pruning \n')
    file = Path("export.csv")
    if file.is_file():
        remove("export.csv")
    columns = []
    for leaf in leaves:
        column = []
        temp_leaf = copy(leaf)
        column.insert(0, temp_leaf)
        temp_leaf = temp_leaf.parent
        while temp_leaf.is_head != 1:  # might abort at begining
            column.insert(0, temp_leaf)
            temp_leaf = temp_leaf.parent
        columns.append(column)
    for x in columns:
        start, end = limit_boundary(
            x[0].current_structure_height)
        vectorization(x, round(start, 2), round(end, 2))
    eng = start_matlab()
    eng.calculate_k(nargout=0)
    K = int(eng.workspace['I'])
    closestIdx, Idx, centroid = eng.Structure_prune(K, nargout=3)
    parent_nodes = []
    for i in closestIdx[0]:
        parent_nodes.append(leaves[i-1])
    eng.quit()
    return parent_nodes


def cosine_simility(columns):
    start, end = limit_boundary(
        columns[0].current_structure_height)
    for index, val in enumerate(columns[1:]):
        columns[1+index] = vectorization(val, start, end)
        unit_vector = zeros(len(columns[1+index]))
        unit_vector[0] = 1
        # calculate cosine value between vector and unit vector
        columns[1+index] = dot(columns[1+index],
                                  unit_vector)/linalg.norm(columns[1+index])


def vectorization(column, start, end):
    column_vector = zeros((len(arange(start, end, gap)), 2))
    for block in column:
        if block.block != str(0):
            width = blocks[block.block][0]
            height = blocks[block.block][1]
            position = int((block.position-start)/gap)
            for x in arange(0, width, gap):
                if x+gap <= width:
                    column_vector[int(position+x/gap)][0] = round(gap, 2)
                elif x+gap > width:
                    column_vector[int(position+x/gap)][0] = round(width-x, 2)
                column_vector[int(position+x/gap)][1] = round(height, 2)
    column_vector_flatten = column_vector.flatten()
    df = DataFrame([column_vector_flatten])
    if path.isfile("export.csv"):
        with open("export.csv", 'a') as f:
            df.to_csv(f, header=False)
    else:
        df.to_csv("export.csv")


def find_least_f(openlist):
    min_num = 0
    min_f = 0
    for i, val in enurmerate(openlist):
        if val.f < min_f:
            min_num = i
            min_f = val.f
    return min_num


def check_block_type(node):
    nd = deepcopy(node)
    type_list = []
    while nd is None or nd.block is not str(0):
        if nd.block not in type_list:
            type_list.append(nd.block)
        nd = nd.parent
    return len(type_list)


# check if block overlap with other blocks

def check_overlap(node, parent):
    nd = copy(parent)
    if nd.is_head == 1:
        return True
    while nd.is_head != 1:
        if nd.block != str(0):
            if nd.position+blocks[nd.block][0] > node.position:
                return False
            else:
                return True
        nd = nd.parent
    return True


def check_stability(node, parent):
    nd = copy(parent)
    start = round(node.position, 2)
    end = round(node.position+blocks[node.block][0], 2)
    shadow_blocks = []
    contiguous_blocks = []
    if nd.is_start == 1 or node.current_structure_height == 0:
        return True

    signal = 0
    while nd.is_start != 1:
        if nd.is_head == 1:
            signal = signal+1
        if signal == 2:
            break
        if nd.block == str(0):
            nd = nd.parent
            continue
        elif nd.block != str(0) and ((round(nd.position+blocks[nd.block][0], 2) > start and round(nd.position+blocks[nd.block][0], 2) < end) or (round(nd.position, 2) > start and round(nd.position, 2) < end) or (round(nd.position, 2) <= start and round(nd.position+blocks[nd.block][0], 2) >= end)):
            shadow_blocks.append(nd)
            print("shadow_blocks", nd.block, nd.position, nd.point)
            if (round(nd.position+blocks[nd.block][0], 2) > start and round(nd.position+blocks[nd.block][0], 2) < end and round(nd.position, 2) <= start) or (round(nd.position, 2) <= start and round(nd.position+blocks[nd.block][0], 2) >= end):
                break
        nd = nd.parent

    shadow_blocks.reverse()

    contiguous_blocks = shadow_blocks
    if len(contiguous_blocks) == 1:
        contiguous_block_left_point = round(contiguous_blocks[0].position, 2)
        contiguous_block_right_point = round(
            contiguous_block_left_point+blocks[contiguous_blocks[0].block][0], 2)
        node_left_point = round(node.position, 2)
        node_right_point = round(node_left_point+blocks[node.block][0], 2)
        if (contiguous_block_left_point <= node_left_point and contiguous_block_right_point >= node_right_point) or round(node_left_point+(blocks[node.block][0])/2.0, 2) == round(contiguous_block_left_point+(blocks[contiguous_blocks[0].block][0])/2.0, 2):
            print(1)
            return True
        else:
            return False
    elif len(contiguous_blocks) >= 2:
        if round(contiguous_blocks[0].position+blocks[contiguous_blocks[0].block][0], 2) > start and contiguous_blocks[-1].position + blocks[contiguous_blocks[-1].block][0]/2.0 >= (3*end+start)/4:
            return True
        else:
            return False
    return False


def find_point(position, node, current_structure_height):
    nd = copy(node)
    while nd.is_start != 1:
        if nd.block == "0":
            nd = nd.parent
            continue
        if nd.point == current_structure_height:
            nd = nd.parent
            continue
        if nd.position < position and nd.position+blocks[nd.block][0] > position:
            return round(nd.point+blocks[nd.block][1], 2)
        nd = nd.parent
    return 0


def find_height(node):
    current_structure_height = node.current_structure_height
    nd = deepcopy(node)
    start = nd.position
    end = nd.position+blocks[nd.block][0]
    overlap_blocks = []
    contiguous_blocks = []
    nd = nd.parent
    while nd.is_start == 0:
        if nd.block == "0":
            nd = nd.parent
            continue
        if nd.point == current_structure_height:
            nd = nd.parent
            continue
        if (nd.position+blocks[nd.block][0] > start and nd.position+blocks[nd.block][0] < end) or (nd.position > start and nd.position < end):
            overlap_blocks.append(nd)
        nd = nd.parent

    overlap_blocks.sort(key=lambda x: x.point, reverse=False)

    point = 0

    for block in overlap_blocks:
        if block.point >= point:
            contiguous_blocks.append(block)
        point = block.point

    contiguous_blocks.sort(key=lambda x: x.position, reverse=False)
    return contiguous_blocks[0].point


def find_block(height):
    candidates = []
    for index, size in blocks.items():
        if height == size[1]:
            candidates.append(blocks.get(index))
    return candidates


def generate_child(parent_node, step):
    childlist = []
    for key, val in blocks.items():
        if parent_node.is_head == 0 and parent_node.max_height != 0 and round(val[1], 2) != round(parent_node.max_height, 2):
            continue
        child = Node()
        child.block = str(key)
        child.g = 0
        child.f = child.g
        childlist.append(child)
    return childlist


def find_pig_position(complete_locations):
    # identify all possible pig positions on top of blocks (maximum 2 pigs per
    # block, checks center before sides)
    possible_pig_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        pig_width = pig_size[0]
        pig_height = pig_size[1]

        # dont place block on edge if block too thin
        if blocks[str(block[0])][0] < pig_width:
            test_positions = [[round(block[1], 10), round(block[2] + (pig_height/2) + (block_height/2), 10)]]
        else:
            test_positions = [ [round(block[1], 10), round(block[2] + (pig_height/2) + (block_height/2), 10)],
                               [round(block[1] + (block_width/3), 10), round(block[2] + (pig_height/2) + (block_height/2), 10)],
                               [round(block[1] - (block_width/3), 10), round(block[2] + (pig_height/2) + (block_height/2), 10)] ]  # check above centre of block
        for test_position in test_positions:
            valid_pig = True
            for i in complete_locations:
                if ( round((test_position[0] - pig_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[0] + pig_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                     round((test_position[1] + pig_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                     round((test_position[1] - pig_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10) ):
                    valid_pig = False
            if valid_pig == True:
                possible_pig_positions.append(test_position)

    # identify all possible pig positions on ground within structure
    print('\ncomplete_locations\n', complete_locations)
    left_bottom = [complete_locations[0][0], complete_locations[0][1]]
    print('right_bottom', list(filter(lambda x: x[2] == complete_locations[0][2], complete_locations)))
    right_bottom_block = sorted(list(filter(lambda x: x[2] == complete_locations[0][2], complete_locations)), key=lambda y: y[1])[-1]
    right_bottom = [right_bottom_block[0], right_bottom_block[1]]
    test_positions = []
    x_pos = left_bottom[1]

    while x_pos < right_bottom[1]:
        test_positions.append([round(x_pos, 10), round(absolute_ground + (pig_height/2), 10)])
        x_pos = x_pos + pig_precision

    for test_position in test_positions:
        valid_pig = True
        for i in complete_locations:
            if ( round((test_position[0] - pig_width/2), 10) < round((i[1] + (blocks[str(i[0])][0])/2), 10) and
                 round((test_position[0] + pig_width/2), 10) > round((i[1] - (blocks[str(i[0])][0])/2), 10) and
                 round((test_position[1] + pig_height/2), 10) > round((i[2] - (blocks[str(i[0])][1])/2), 10) and
                 round((test_position[1] - pig_height/2), 10) < round((i[2] + (blocks[str(i[0])][1])/2), 10) ):
                valid_pig = False
        if valid_pig == True:
            possible_pig_positions.append(test_position)

    # randomly choose a pig position and remove those that overlap it, repeat
    # until no more valid positions
    final_pig_positions = []
    while len(possible_pig_positions) > 0:
        pig_choice = possible_pig_positions.pop(randint(1, len(possible_pig_positions))-1)
        final_pig_positions.append(pig_choice)
        new_pig_positions = []
        for i in possible_pig_positions:
            if ( round((pig_choice[0] - pig_width/2), 10) >= round((i[0] + pig_width/2), 10) or
                 round((pig_choice[0] + pig_width/2), 10) <= round((i[0] - pig_width/2), 10) or
                 round((pig_choice[1] + pig_height/2), 10) <= round((i[1] - pig_height/2), 10) or
                 round((pig_choice[1] - pig_height/2), 10) >= round((i[1] + pig_height/2), 10) ):
                new_pig_positions.append(i)
        possible_pig_positions = new_pig_positions

    # number of pigs present in the structure
    print("Pig number:", len(final_pig_positions))
    print("")
    return complete_locations, final_pig_positions


def read_limit(filename):
    with open(filename, "r") as file:
        l = file.readline().strip('\n').split(',')
        function_x = []
        function_y = []
        lx = []
        ly = []
        while (l != ['']):
            print(l)
            function_x.append(l[0])
            lx.append(l[1])
            l = file.readline().strip('\n').split(',')

        l = file.readline().strip('\n').split(',')
        while (l != ['']):
            print(l)
            function_y.append(l[0])
            ly.append(l[1])
            l = file.readline().strip().strip('\n').split(',')

        middle = float(file.readline().strip('\n'))
        return Piecewise(*[(sympify(f), y < float(lx)) if i != len(function_x)-1 else (sympify(f), y <= float(lx))
                           for i, (f, lx)
                           in enumerate(zip(function_x, lx))]), Piecewise(*[(sympify(f), x <= float(ly))
                                                                            for f, ly
                                                                            in zip(function_y, ly)]), float(lx[len(lx)-1]), middle
    return False


def limit_boundary(structure_height):
    startpoint = round(float(px.subs(y, structure_height)), 2)
    current_max_width = (
        middle - startpoint)*2
    print(structure_height, current_max_width)
    return startpoint, round(startpoint+float(current_max_width), 2)


def height_limit(position, point):  # limit problems
    position = middle - Abs(middle-position)
    y_limit = py.subs(x, position)
    if y_limit == 0:
        return min(list(filter(lambda x: x >= point, solve(px-position, y))))
    else:
        return min(list(filter(lambda x: x >= point, solve(px-position, y)+[y_limit])))


if __name__ == '__main__':
    px, py, m_height, middle = read_limit("limit_parameter.txt")
    print(px)
    print(py)
    print(ctime())
    structures = generate(m_height)
    construct(structures, sys.argv[1])
