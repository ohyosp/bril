import json
import sys
import collections
import graphviz

TERMINATOR_OPS = 'jmp', 'br', 'ret'      

"""
Input: list of instructions (each instruction is a dict)
Output: list of lists of instructions (each list is a basic block)
 - Basic blocks terminate from TERMINATOR_OPS or end of program
 - Labels are always at the beginning of a basic block
    - A basic block may or may not begin with a label
 - Basic blocks are not guaranteed to be maximal
 - Basic blocks are guaranteed to be non-empty
"""
def get_basic_blocks(instructions):
    basic_blocks = []
    block = []
    for instr in instructions:
        if 'op' in instr:
            block.append(instr)
            if instr['op'] in TERMINATOR_OPS:
                basic_blocks.append(block)
                block = []
        if 'label' in instr:
            if not block:
                block.append(instr)
            else:
                basic_blocks.append(block)
                block = []
                block.append(instr)
    if block:
        basic_blocks.append(block)
    return basic_blocks


"""
Input: a list of basic blocks (lists of instructions)
Output: a dictionary mapping (tuples of) labels to basic blocks
 - Blocks without labels are assigned a label using their position within the BB list
 - Labels will be removed from basic blocks
 - Blocks consisting of only a label will be put in a tuple with the label(s) of the next block
"""
def labels2blocks(basic_blocks):
    label_block_map = collections.OrderedDict()
    unlabeled_index = 0
    carry_list = []
    for block in basic_blocks:
        first_instr = block[0]
        if 'label' in first_instr:
            label = first_instr['label']
            block = block[1:]
        else:
            label = 'block' + str(unlabeled_index)
            unlabeled_index += 1
        if block:
            carry_list.append(label)
            label_block_map[tuple(carry_list)] = block
            carry_list = []
        else:
            carry_list.append(label)
    return label_block_map
    
"""
Helper function to get tuple of labels all pointing to same BB
"""
def get_label_alias(label_block_map, label):
    for label_set in label_block_map.keys():
        if label in label_set:
            return label_set


"""
Input: map from labels (aliased tuples) to basic blocks
Output: CFG (set of directed edges, represented as a dict)
 - Program entry and exit represented by ('START',) and ('TERM',)
"""
def create_cfg(label_block_map):
    cfg = {}
    if label_block_map:
        cfg[('START',)] = [list(label_block_map.keys())[0]]
    else:
        cfg[('START',)] = [('TERM',)]
    for i, (label, block) in enumerate(label_block_map.items()):
        dest = []
        last_instr = block[-1]
        if 'op' in last_instr:  # redundant?
            if last_instr['op'] in TERMINATOR_OPS:
                match last_instr['op']:
                    case 'jmp':
                        dest.append(get_label_alias(label_block_map, last_instr['labels'][0]))
                    case 'br':
                        dest.extend([get_label_alias(label_block_map, l) for l in last_instr['labels']])
                    case 'ret':
                        dest.append(('TERM',))
                cfg[label] = dest
                continue
        if i + 1 < len(label_block_map):
            dest.append(list(label_block_map.keys())[i+1])
        if not dest:
            dest.append(('TERM',))
        cfg[label] = dest
    return cfg

def group_maximal_blocks(cfg):
    # I don't know...
    return                

"""
Input: a CFG
Output: creates a graphviz Graph of the CFG
 - Branches labeled with predicate (T/F)
"""
def create_graphviz(function_name, cfg):
    dot = graphviz.Digraph(function_name)
    for label in cfg.keys():
        dot.node(str(label))
    dot.node(str(('TERM',)))
    for label, successor in cfg.items():
        if len(successor) == 2:
            dot.edge(str(label), str(successor[0]), 'T')
            dot.edge(str(label), str(successor[1]), 'F')
        else:
            dot.edge(str(label), str(successor[0]))
    dot.format = 'pdf'
    # dot.render('cfg.pdf')
    print(dot.source)


if __name__ == "__main__":
    program = json.load(sys.stdin)
    for function in program['functions']:
        basic_blocks = get_basic_blocks(function['instrs'])
        label_block_map = labels2blocks(basic_blocks)
        cfg = create_cfg(label_block_map)
        create_graphviz(function['name'], cfg)