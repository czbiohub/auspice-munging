import pandas as pd
import numpy as np

def get_county(node):
    divison = node.get_attr('division')
    location = node.get_attr('location')
    originating_lab = node.node_attrs.get('originating_lab')

    if divison == 'Grand Princess' or location == 'Grand Princess cruise ship':
        return 'Grand Princess Cruise Ship'

    if originating_lab and 'Santa Clara' in originating_lab:
        return 'Santa Clara'

    if divison == 'California':
        if isinstance(location, str):
            if location[-7:] == ' County':
                return location[:-7]

        return location

    return None
