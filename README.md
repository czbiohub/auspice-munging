# Auspice Munging

Sometimes it is necessary to postprocess an auspice JSON to add additional metadata or prune to a more focused subtree.

* `tree.py` contains a class for turning the JSON tree into a python object.
* `meta_munge.py` contains functions for modifying foibles of the GISAID metadata (such as the Grand Princess cruise ship, or various spellings of the same county).

Usage:

```
python munge.py \
            --json ~/src/covidtracker/internal/200605/ncov_with_accessions.json \
            --external-codes ~/src/covidtracker/internal/200601/external_codes_metadata_tsv.tsv \
            --county 'Santa Clara' \
            --node-name Accession_ID \
            --scale ancestors
```
