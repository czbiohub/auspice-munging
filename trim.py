#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy

def trim_tree(tree, county, filter, scale):
    if scale is None:
        return tree

    tree = copy.deepcopy(tree)

    if county:
        print(f'Filtering leaves to county {county}')
        leaves = tree.filter_nodes('county', county)
    elif filter:
        print(f'Filtering leaves to those matching {filter[0]}: {filter[1]}')
        leaves = tree.filter_nodes(filter[0], filter[1])

    if scale == 'local':
        nodes_to_keep = walk_to_root(leaves)
    elif scale == 'ancestors':
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
    parser.add_argument('--county',
                        help='County to filter on. If no county is specified,'
                             'no filtering will be done.', default=None)
    parser.add_argument('--filter',
                        help='[Key] [Value] Arbitrary key/value', default=None, nargs=2)
    parser.add_argument('--scale',
                        help='Sets scale of analysis. `local` will show only '
                             'sequences from the county. `ancestors` will show '
                             'sequences from county and plausible '
                             'ancestors. ',
                        default=None)
    parser.add_argument('--output',
                        help='Output file. If none, the format will be'
                             ' COUNTY_SCALE.json',
                        default=None)

    args = parser.parse_args()

    with open(args.json, 'r') as fp:
        js = json.load(fp)
    tree = Tree(js['tree'])

    tree = trim_tree(tree, args.county, args.filter, args.scale)

    if args.county:
        js['meta']['title'] = 'COVID Tracker CA: ' + args.county

    if args.output is None:
        outfile = (os.path.dirname(args.json) + '/'
                   + ("_".join(args.county.split()) if args.county else "all")
                   + '_'
                   + str(args.scale)
                   + '.json')
        print(outfile)
    else:
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
