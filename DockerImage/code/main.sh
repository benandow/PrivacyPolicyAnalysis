#!/bin/bash

if [ ! -e "/ext/run_config" ]; then
	echo "Error: Set /ext/run_config to either <policylint|policheck>"
	exit 1
fi

runconfig=$(cat /ext/run_config)

if [ "$runconfig" = "policylint" ]; then
	echo "Running with PolicyLint ontologies"
	cp /ext/data/data_ontology_policylint.pickle data_ontology.pickle
	cp /ext/data/entity_ontology_policylint.pickle entity_ontology.pickle
elif [ "$runconfig" = "policheck" ]; then
	echo "Running PoliCheck ontologies"
	cp /ext/data/data_ontology_policheck.pickle data_ontology.pickle
	cp /ext/data/entity_ontology_policheck.pickle entity_ontology.pickle
else
	echo "Error: Set /ext/run_config to either <policylint|policheck>"
	exit 1
fi


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
python2 RemoveSameSentenceContradictions.py 1
python2 DisclosureClassification.py

