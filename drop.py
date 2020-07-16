#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy

def trim_tree(tree, county, scale):
    if scale is None:
        return tree

    tree = copy.deepcopy(tree)

    if scale == 'local':
        leaves = tree.filter_nodes('county', county)
        nodes_to_keep = walk_to_root(leaves)
    elif scale == 'ancestors':
        leaves = tree.filter_nodes('county', county)
        nodes_to_keep = walk_to_root(leaves)
        nodes_to_keep = walk_down(nodes_to_keep, mode='mutations', depth=0)
        nodes_to_keep = walk_to_root(
            [n for n in nodes_to_keep if n.type == NodeType.LEAF])
    if tree.root not in nodes_to_keep:
        nodes_to_keep.append(tree.root)

    n_genomes = len([n for n in nodes_to_keep if n.type == NodeType.LEAF])
    print("Subsetting tree to ", n_genomes, " genomes.")
    tree.subset_tree(nodes_to_keep)
    return tree

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json',
                        help='auspice json')
    parser.add_argument('--ids',
                        help='Drop all ids in the list.',
                        )
    parser.add_argument('--output',
                        help='Output file. If none, the format will be'
                             ' COUNTY_SCALE.json',
                        )

    args = parser.parse_args()

    with open(args.json, 'r') as fp:
        js = json.load(fp)
    tree = Tree(js['tree'])

    n_genomes_before = len([n for n in tree.nodes if n.type == NodeType.LEAF])

    with open(args.ids, 'r') as fp:
        ids_to_drop = fp.read().splitlines()

    nodes_to_keep = [n for n in tree.nodes if n.type == NodeType.LEAF and
                     n.name not in ids_to_drop]
    nodes_to_keep = walk_to_root(nodes_to_keep)
    if tree.root not in nodes_to_keep:
        nodes_to_keep.append(tree.root)

    tree.subset_tree(nodes_to_keep)

    n_genomes_after = len([n for n in tree.nodes if n.type == NodeType.LEAF])

    print("Removing ", n_genomes_before - n_genomes_after,
          " of ", n_genomes_before, " genomes.")

    outfile = args.output
    with open(outfile, 'w') as fp:
        json.dump(
            {"meta": js['meta'],
             "version": js['version'],
             "tree": tree.to_dict()},
            fp,
            indent=2)


if __name__ == '__main__':
    main()
