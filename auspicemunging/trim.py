#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy

def trim_tree(tree, county=None, filter=None, scale=None):
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
            [n for n in nodes_to_keep if n.type == NodeType.LEAF]
        )


    if tree.root not in nodes_to_keep:
        nodes_to_keep.append(tree.root)

    n_genomes = len([n for n in nodes_to_keep if n.type == NodeType.LEAF])
    print("Subsetting tree to ", n_genomes, " genomes.")
    tree.subset_tree(nodes_to_keep)
    return tree


def get_mutations(node):
    mutations_by_gene = node.branch_attrs['mutations']
    return [mutation for gene, mutations in mutations_by_gene.items() for mutation in mutations]


def trim_tree_mut(tree, mutation):
    tree = copy.deepcopy(tree)

    branches_with_mutation = [node for node in tree.nodes if mutation in get_mutations(node)]
    print(len(branches_with_mutation))
    nodes_with_mutation = walk_to_leaves(branches_with_mutation)
    nodes_to_keep = walk_to_root(nodes_with_mutation)

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
    parser.add_argument('--mutation',
                        help='Trims to nodes with a specific mutation'
                             'ancestors. ',
                        default=None)
    parser.add_argument('--output',
                        help='Output file. If none, the format will be'
                             ' COUNTY_SCALE.json',
                        default=None)

    args = parser.parse_args()

    au = Auspice(args.json)

    if args.mutation:
        au.tree = trim_tree_mut(au.tree, args.mutation)
    else:
        au.tree = trim_tree(au.tree, args.county, args.filter, args.scale)

    if args.county:
        au.js['meta']['title'] = 'COVID Tracker CA: ' + args.county

    if args.output is None:
        outfile = (os.path.dirname(args.json) + '/'
                   + ("_".join(args.county.split()) if args.county else "all")
                   + '_'
                   + str(args.scale)
                   + '.json')
        print(outfile)
    else:
        outfile = args.output

    au.write(outfile)

if __name__ == '__main__':
    main()
