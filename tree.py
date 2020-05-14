import json
from enum import Enum
import copy

class NodeType(Enum):
    NODE = 0
    LEAF = 1

class Node():
    def __init__(self, data_dict = None):
        self.parent = None
        self.children = []
        self.branch_attrs = {}
        self.node_attrs = {}
        self.name = None
        self.type = None

        if data_dict:
            self.from_dict(data_dict)

    def to_dict(self):
        d = {'branch_attrs': self.branch_attrs,
             'node_attrs': self.node_attrs,
             'name': self.name}
        if self.children:
             d['children'] = [child.to_dict() for child in self.children]

        return d

    def from_dict(self, d):
        self.branch_attrs = d['branch_attrs']
        self.node_attrs = d['node_attrs']
        self.name = d['name']

        if 'children' in d and len(d['children']) > 0:
            self.children = [Node(c) for c in d['children']]
        else:
            self.children = []
        for c in self.children:
            c.parent = self

        if self.children:
            self.type = NodeType.NODE
        else:
            self.type = NodeType.LEAF

    def descendents(self):
        return self.children + [node for c in self.children for node in c.descendents()]

    def get_attr(self, attr):
        if attr in self.branch_attrs:
            if isinstance(self.branch_attrs[attr], dict):
                return self.branch_attrs[attr]['value']
            else:
                return self.branch_attrs[attr]

        if attr in self.node_attrs:
            if isinstance(self.node_attrs[attr], dict):
                return self.node_attrs[attr]['value']
            else:
                return self.node_attrs[attr]

    def set_attr(self, attr, value, attr_type='node'):
        if value is None:
            return
        if attr_type == 'node':
            self.node_attrs[attr] = {'value': value}
        else:
            self.branch_attrs[attr] = {'value': value}

class Tree():
    def __init__(self, data_dict = None):
        self.root = None
        self.nodes = []
        if data_dict:
            self.from_dict(data_dict)

    def to_dict(self):
        return self.root.to_dict()

    def from_dict(self, data_dict):
        self.root = Node(data_dict)
        self.nodes = [self.root] + self.root.descendents()

    def set_node_attr(self, attr, state):
        for node in self.nodes:
            self.node_attrs[attr] = state

    def subset_tree(self, nodes_to_keep):
        for node in self.nodes:
            node.children = [c for c in node.children if c in nodes_to_keep]
        self.nodes = nodes_to_keep

    def trim_terminal_nodes(self):
        nodes_to_keep = [node for node in self.nodes if
                        node.type == NodeType.LEAF or len(node.children) > 0]
        self.subset_tree(nodes_to_keep)

def walk_to_root(nodes):
    stack = nodes.copy()
    done = []
    while stack:
        node = stack.pop()
        if node.parent and node.parent not in stack and node.parent not in done:
            stack.append(node.parent)
        done.append(node)
    return done

def walk_down(nodes, mode = "steps", depth = 1):
    if mode == 'steps':
        levels = [nodes.copy()]
        for i in range(depth):
            next_level = []
            for node in levels[-1]:
                next_level.extend(node.children)
            levels.append(next_level)
        return [node for level in levels for node in level]
    if mode == "mutations":
        levels = [nodes.copy()] + [[]]*depth
        done = nodes.copy()
        for i in range(depth + 1):
            j = 0
            while j < len(levels[i]):
                node = levels[i][j]
                for c in node.children:
                    distance = i + num_mutations(c)
                    if distance < depth + 1:
                        if c not in done:
                            levels[distance].append(c)
                            done.append(c)
                j += 1
        return done

def num_mutations(node):
    if 'mutations' in node.branch_attrs:
        if 'nuc' in node.branch_attrs['mutations']:
            return len(node.branch_attrs['mutations']['nuc'])
    return 0
