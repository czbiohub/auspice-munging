#!/usr/bin/env python3

import argparse
import pandas as pd
import os
from tree import *
import copy


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

    au = Auspice(args.json)

    with open(args.ids, 'r') as fp:
        names_to_drop = fp.read().splitlines()

    au.tree.drop_by_name(names_to_drop, verbose=True)

    au.write(args.output)

if __name__ == '__main__':
    main()
