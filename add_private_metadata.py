#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy

def read_table(filename):
    if filename.endswith('csv'):
        return pd.read_csv(filename, dtype=str)
    if filename.endswith('tsv'):
        return pd.read_csv(filename, sep = '\t', dtype=str)
    if filename.endswith('xls') or filename.endswith('xlsx'):
        return pd.read_excel(filename, dtype=str)
    else:
        raise NotImplementedError

def update_json_meta(js, tree, df, county):
    for key in list(df.columns):
        if key == 'age':
            continue
        order_type = 'categorical'
        # if key in ['n_alt', 'n_ref', 'log_n_alt', 'log_n_ref', 'log_diff']:
        # order_type = 'continuous'
        coloring = {'key': key, 'title': key.capitalize(), 'type': order_type}
        js['meta']['colorings'].insert(0, coloring)
        js['meta']['filters'].insert(0, key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json',
                        help='auspice json')
    parser.add_argument('--submitted-sequences',
                        help='CSV with GISAID ID, CZB_ID')
    parser.add_argument('--dph-ids',
                        help='CSV with DPH ID, CZB_ID')
    parser.add_argument('--metadata',
                        help='External metadata')
    parser.add_argument('--county',
                        help='Restrict metadata additions to county. If no county '
                             'is specified, add metadata to all entries.', default=None)
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

    gisaid_to_czb = read_table(args.submitted_sequences)
    gisaid_to_czb['strain'] = gisaid_to_czb['gisaid_name'].apply(lambda x: x[8:] if isinstance(x, str) else x)
    gisaid_to_czb.rename({'CZB_ID': 'czb_id'}, axis = 1, inplace=True)

    czb_to_dph = read_table(args.dph_ids)

    df = gisaid_to_czb[['strain', 'czb_id']].merge(
            czb_to_dph[['czb_id', 'external_accession']],
            on='czb_id',
            how='left')

    if args.metadata:
        metadata = read_table(args.metadata)
        metadata.rename({col: '_'.join(col.split()) for col in metadata.columns}, axis=1,
                  inplace=True)
        if 'external_accession' in metadata.columns:
            key = 'external_accession'
        elif 'strain' in metadata.columns:
            key = 'strain'
        else:
            raise ValueError
        df = df.merge(metadata, on=key, how='left')

        for field in metadata.columns:
            if field not in ['strain', 'external_accession', 'czb_id']:
                coloring = {'key': field, 'title': field.capitalize(),
                            'type': 'categorical'}
                js['meta']['colorings'].insert(0, coloring)
                js['meta']['filters'].insert(0, field)

    if args.county:
        samples_to_add_metadata_to = [n.name for n in tree.filter_nodes('county', args.county)]
        df = df[df['strain'].isin(samples_to_add_metadata_to)]
    tree.add_metadata(df)

    if args.node_name:
        tree.rename_nodes(args.node_name, save_attr='GISAID_ID')

    if args.output is None:
        outfile = (os.path.dirname(args.json) + '/'
                   + 'tree_with_metadata_for_'
                   + ("_".join(args.county.split()) if args.county else "all")
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
