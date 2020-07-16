#!/usr/bin/env python3
from tree import *
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('original_json',
                        help='unfiltered auspice json')
    parser.add_argument('filtered_json',
                        help='filtered auspice json')
    parser.add_argument('county',
                        help='County to check for correct filtering')

    args = parser.parse_args()

    with open(args.original_json, 'r') as fp:
        js = json.load(fp)
    original_tree = Tree(js['tree'])

    with open(args.filtered_json, 'r') as fp:
        js = json.load(fp)
    filtered_tree = Tree(js['tree'])

    original_leaves = original_tree.filter_nodes('county', args.county)
    filtered_leaves = filtered_tree.filter_nodes('county', args.county)

    print(f'Original tree has {len(original_leaves)} samples')
    print(f'Filtered tree has {len(filtered_leaves)} samples')

    if len(original_leaves) != len(filtered_leaves):
        print('ERROR - mismatch in number of samples')
        sys.exit(1)
    

if __name__ == '__main__':
    main()
