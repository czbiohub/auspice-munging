# Auspice Munging

Sometimes it is necessary to postprocess an auspice JSON to add additional metadata or prune to a more focused subtree.

* `tree.py` contains a class for turning the JSON tree into a python object, adding metadata, and walking.
* `add_private_metadata.py` adds Partner_IDs and other private metadata to the tree.
* `trim.py` trims the tree to focus on one county.

Usage:

```
python add_private_metadata.py \
    --json ncov_with_accessions.json \
    --submitted-sequences ~/src/covid19-submissions/to_submit/submitted_sequences.tsv \
    --dph-ids dph_czb_ids.csv \
    --county 'Santa Clara' \
    --node-name Partner_ID
```

and

```
python trim.py \
    --json tree_with_metadata_for_Santa_Clara.json \
    --county 'Santa Clara' \
    --scale ancestors
```