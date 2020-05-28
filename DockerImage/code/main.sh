#!/bin/bash

mkdir -p /ext/input/policySubsets/
mkdir -p /ext/output/policy
mkdir -p /ext/output/analytics
find /ext/plaintext_policies -type f > /ext/input/policySubsets/1.txt
python2 PatternExtractionNotebook.py 1

mkdir -p /ext/datasets/
mkdir -p /ext/output/db/
mkdir -p /ext/output/log_data
find /ext/output/policy -type f > /ext/datasets/1.txt

python2 ConsistencyAnalysis.py 1

mkdir /ext/combined_tables
python2 1AggregatePoliCheckDatabases.py
python2 2DisclosureClassification.py
