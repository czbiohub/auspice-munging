#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy

def get_county(node):
    division = node.get_attr('division')
    location = node.get_attr('location')
    originating_lab = node.get_attr('originating_lab')

    if division == 'Grand Princess' or location == 'Grand Princess cruise ship':
        return 'Grand Princess Cruise Ship'

    if originating_lab and 'Santa Clara' in originating_lab:
        return 'Santa Clara'

    if division == 'California':
        if isinstance(location, str):
            if location[-7:] == ' County':
                return location[:-7]

        return location

    return None

def read_table(filename):
    if filename.endswith('csv'):
        return pd.read_csv(filename)
    if filename.endswith('tsv'):
        return pd.read_csv(filename, sep = '\t')
    if filename.endswith('xls') or filename.endswith('xlsx'):
        return pd.read_excel(filename)
    else:
        raise NotImplementedError

def trim_tree(tree, county, scale):
    if county is None:
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

def update_json_meta(js, tree, df, county):
    # Add coloring
    local_lab_coloring = {'key': 'ca_lab', 'title': 'CA Lab',
                          'type': 'categorical'}
    js['meta']['colorings'].insert(0, local_lab_coloring)
    county_coloring = {'key': 'county', 'title': 'County',
                       'type': 'categorical'}
    js['meta']['colorings'].insert(0, county_coloring)

    for key in list(df.columns):
        if key == 'age':
            continue
        order_type = 'categorical'
        # if key in ['rooms', 'num_in_hh']:
        #     order_type = 'continuous'
        coloring = {'key': key, 'title': key.capitalize(), 'type': order_type}
        js['meta']['colorings'].insert(0, coloring)
        js['meta']['filters'].insert(0, key)

    js['meta']['filters'].insert(0, 'county')
    js['meta']['filters'].append('originating_lab')
    js['meta']['filters'].append('submitting_lab')

    maintainers = [
        {'name': 'Chan Zuckerberg Biohub', 'url': 'https://www.czbiohub.org'},
        {'name': 'California Departments of Public Health',
         'url': 'https://www.cdph.ca.gov/Pages/LocalHealthServicesAndOffices.aspx#'}]
    js['meta']['maintainers'] = maintainers

    js['meta']['title'] = 'COVID Tracker CA: ' + (county if county else "")

    js['meta']['display_defaults']['color_by'] = 'County'
    js['meta']['display_defaults']['geo_resolution'] = 'location'
    js['meta']['display_defaults']['distance_measure'] = 'div'
    js['meta']['display_defaults']['panels'] = ['tree']

    with open('/Users/josh/src/covidtracker/internal/covidtrackerca.md',
              'r') as fp:
        description = fp.read()
    js['meta']['description'] = description

def set_metadata(tree):
    # Set County
    for node in tree.nodes:
        if node.type == NodeType.LEAF:
            county = get_county(node)
            node.set_attr('county', county)

    # Set Local Lab
    for node in tree.nodes:
        if node.type == NodeType.LEAF:
            local_lab = node.get_attr('submitting_lab')
            if node.get_attr('division') == 'California':
                node.set_attr('ca_lab', local_lab)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json',
                        help='auspice json')
    parser.add_argument('--external-codes',
                        help='CSV with strain, CZB_ID, Accession_ID')
    parser.add_argument('--county',
                        help='County to filter on. If no county is specified,'
                             'no filtering will be done.', default=None)
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
    parser.add_argument('--node-name',
                        help='Metadata field to rename nodes by.',
                        default=None)

    args = parser.parse_args()

    with open(args.json, 'r') as fp:
        js = json.load(fp)
    tree = Tree(js['tree'])

    df = read_table(args.external_codes)
    df.rename({col: '_'.join(col.split()) for col in df.columns}, axis=1,
              inplace=True)

    set_metadata(tree)

    tree.add_metadata(df)

    tree = trim_tree(tree, args.county, args.scale)

    if args.node_name:
        assert(args.node_name in df.columns)
        tree.rename_nodes(args.node_name, save_attr='old_name')

    update_json_meta(js, tree, df, args.county)

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
