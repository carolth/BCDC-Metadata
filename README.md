# C2M2 partial instance generation branch `c2m2_generation`

The sample manifest from 2020 **Q3**, together with project/data collection and other metadata, was used to generate some of the TSV files comprising a C2M2 Level 1 instance.

The following are not generated yet:

1. data_type.tsv
2. file.tsv
3. file_describes_biosample.tsv
4. file_format.tsv
5. file_in_collection.tsv

We may consider the workflow for data submitters:

1. Submit to archive (BIL, NeMO, DANDI).
2. Note exact files.
3. Provide a file like `file_describes_biosample.csv` to BCDC at time of providing other project metadata, in light of notes made in (2).
4. BCDC provides more complete C2M2 L1-like instance to archives for cross-institutional coordination purposes.
