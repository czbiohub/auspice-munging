import json
from enum import Enum
import json
import pandas as pd

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
        if 'branch_attrs' in d:
            self.branch_attrs = d['branch_attrs']
        if 'node_attrs' in d:
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


    def check(self, conditions):
        """Check if the node satisfies conditions, encoded as
        {attr: value} elements in a dict."""
        for attr in conditions.keys():
            if self.get_attr(attr) != conditions[attr]:
                return False
        return True

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
            node.node_attrs[attr] = state

    def subset_tree(self, nodes_to_keep):
        for node in self.nodes:
            node.children = [c for c in node.children if c in nodes_to_keep]
        self.nodes = nodes_to_keep

    def trim_terminal_nodes(self):
        nodes_to_keep = [node for node in self.nodes if
                        node.type == NodeType.LEAF or len(node.children) > 0]
        self.subset_tree(nodes_to_keep)

    def add_metadata(self, df):
        """Merge metadata file containing a 'strain' column."""
        df.rename({col: '_'.join(col.split()) for col in df.columns},
                  axis=1,
                  inplace=True)
        df = df.set_index('strain')

        for node in self.nodes:
            if node.name in df.index:
                for col in df.columns:
                    val = df.loc[node.name, col]
                    try:
                        if not pd.isnull(val):
                            node.set_attr(col, val)
                    except:
                        print("bad value")
                        print(col, val)
                        continue

    def filter_nodes(self, attr, value):
        return [node for node in self.nodes if
                node.get_attr(attr) == value]

    def rename_nodes(self, attr, save_attr=None, filter=None):
        """Reset name to value of attr field.
        If save_attr is specified, save current name to that field."""
        for node in self.nodes:
            val = node.get_attr(attr)
            if filter and not node.check(filter):
                continue
            if val and val != "None":
                sanitized_val = "-".join(val.split())
                print("renaming node ", node.name, " to ", sanitized_val)
                if save_attr:
                    node.set_attr(save_attr, node.name)
                node.name = sanitized_val

    def drop_by_name(self, names_to_drop, verbose=False):
        if verbose:
            n_leaves_before = self.n_leaves()

        nodes_to_keep = [n for n in self.nodes if n.type == NodeType.LEAF and
                         n.name not in names_to_drop]
        nodes_to_keep = walk_to_root(nodes_to_keep)
        if self.root not in nodes_to_keep:
            nodes_to_keep.append(self.root)

        self.subset_tree(nodes_to_keep)

        if verbose:
            n_leaves_after = self.n_leaves()

            print("Removing ", n_leaves_before - n_leaves_after,
                  " of ", n_leaves_before, " genomes.")

    def n_leaves(self):
        return len([n for n in self.nodes if n.type == NodeType.LEAF])


def walk_to_root(nodes):
    stack = nodes.copy()
    done = []
    while stack:
        node = stack.pop()
        if node.parent and node.parent not in stack and node.parent not in done:
            stack.append(node.parent)
        done.append(node)
    return done


def walk_to_leaves(nodes):
    stack = nodes.copy()
    done = []
    while stack:
        node = stack.pop()
        for child in node.children:
            if child not in stack and child not in done:
                stack.append(child)
        done.append(node)
    return done


def walk_down(nodes, mode = "steps", depth = 1, filter = None):
    if mode == 'steps':
        levels = [nodes.copy()]
        for i in range(depth):
            next_level = []
            for node in levels[-1]:
                next_level.extend(node.children)
            levels.append(next_level)
        done = [node for level in levels for node in level]
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

    if filter:
        done = [n for n in done if filter(n)]

    return done

def num_mutations(node):
    if 'mutations' in node.branch_attrs:
        if 'nuc' in node.branch_attrs['mutations']:
            return len(node.branch_attrs['mutations']['nuc'])
    return 0


class Auspice():
    def __init__(self, filename):
        self.tree = None
        self.js = None
        self.read(filename)

    def read(self, filename):
        with open(filename, 'r') as fp:
            self.js = json.load(fp)
        self.tree = Tree(self.js['tree'])

    def write(self, filename):
        with open(filename, 'w') as fp:
            json.dump(
                {"meta": self.js['meta'],
                 "version": self.js['version'],
                 "tree": self.tree.to_dict() if self.tree else self.js['tree']},
                fp,
                indent=2
            )