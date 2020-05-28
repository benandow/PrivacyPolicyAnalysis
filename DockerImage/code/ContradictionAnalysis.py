#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import csv
import dill as pickle
import json
import codecs
import re
import os

import TermPreprocessor2 as tprep
import spacy
import Consistency as con

import ContradictionDatabase as conDB

def fixEntityLemma(txt, nlp):
	def getLemma(tok):
		return tok.lemma_ if tok.lemma_ != u'-PRON-' else tok.text
	doc = nlp(txt)
	return ' '.join([getLemma(t) for t in doc if t.pos != spacy.symbols.DET ])

def LOG_ERROR(outputfilename, message, outputDir='/ext/output/log_data'):
	with codecs.open(os.path.join(outputDir, outputfilename), 'a', 'utf-8') as logfile:
		logfile.write(message)
		logfile.write('\n')

def ensureUnicode(s):
	return s.decode('utf-8') if type(s) == str else s

def loadPrivacyPolicyResults(filename, packageName, cdb, nlp, subsetNum):
	if not os.path.isfile(filename):
		return []
	policy = []
	for e,c,d,s,aLemma in pickle.load(open(filename, 'rb')):
		e = ensureUnicode(e)
		c = ensureUnicode(c)
		d = ensureUnicode(d)
		s = ensureUnicode(s)

		eproc = tprep.preprocess(fixEntityLemma(e, nlp))
		if eproc in [u'user', u'you']:
			continue

		# u'we_implicit'
		if eproc in [u'we', u'i', u'us', u'me'] or eproc in [u'app', u'mobile application', u'mobile app', u'application', u'service', u'website', u'web site', u'site'] or (e.startswith('our') and eproc in [u'app', u'mobile application', u'mobile app', u'application', u'service', u'company', u'business', u'web site', u'website', u'site']):
			eproc = u'we'
#		if eproc == u'third_party_implicit':
#			eproc = u'third party'
		dproc = tprep.preprocess(d)

		ents = []
		if eproc not in con.Entity.ontology.nodes:
			res = re.sub(r'\b(and|or|and/or|\/|&)\b', u'\n', eproc)
			foundAnEnt = False
			for e in res.split('\n'):
				e = e.strip()
				if e not in con.Entity.ontology.nodes:
					LOG_ERROR('SkippedPolicyEntities_{}.log'.format(subsetNum), e)
					continue
				ents.append(e)
		else:
			ents = [eproc]

		if len(ents) == 0:
			LOG_ERROR('SkippedPolicyEntities_{}.log'.format(subsetNum), eproc)
			continue

		if dproc in con.DataObject.ontology.nodes:
			for e in ents:
				cdb.insertPolicy(e, c, dproc)
				cdb.insertAppPolicySentence(s, (e, c, dproc), packageName)
				policy.append((e, c, dproc, s))
		else:
			res = re.sub(r'\b(and|or|and/or|\/|&)\b', u'\n', dproc)
			for d in res.split('\n'):
				d = d.strip()
				if d not in con.DataObject.ontology.nodes:#This should really never happen...
					LOG_ERROR('SkippedPolicyDataObjects_{}.log'.format(subsetNum), d)
					continue
				for e in ents:
					cdb.insertPolicy(e, c, d)
					cdb.insertAppPolicySentence(s, (e, c, d), packageName)
					policy.append((e, c, d, s))
	print(policy)
	return policy
		#return [ (tprep.preprocess(e), c, tprep.preprocess(d), s) for e,c,d,s in pickle.load(open(filename, 'r')) ]

def getPackageName(policyFilename):
	fname,_ = os.path.splitext(os.path.basename(policyFilename))
	return fname	

def doFilesExist(filelist):
	return all(os.path.exists(f) for f in filelist)

#FIXME this should be the last part of ontology construction...
def temporarilyLinkEntity():
	import networkx as nx
	con.Entity.ontology.add_edge(u'public', u'third party')
	con.Entity.ontology.add_edge(u'public', u'first party')
	con.Entity.ontology.add_edge(u'first party', u'we')
	con.Entity.ontology.add_edge(u'first party', u'i')
	con.Entity.ontology.add_edge(u'first party', u'us')


def main(argv):
	subsetNum = argv[1]
	#Assumes a number as input...
	consistency_database_path = '/ext/output/db/consistency_results_{}.db'.format(subsetNum)
	inputDataFilename = '/ext/datasets/{}.txt'.format(subsetNum)
	progressFilename = '/ext/output/log_data/{}.log'.format(subsetNum)


	cdb = conDB.ConsistencyDB(consistency_database_path)#'consistency_results.db'
	con.init(dataOntologyFilename=u'data_ontology_graph_policheck.pickle', entityOntologyFilename=u'entity_ontology_graph_policheck.pickle')
	nlp = spacy.load('NlpFinalModel')
	temporarilyLinkEntity()
	cdb.createTables()
	# Let's walk the policy directory now...
	progress_file = codecs.open(progressFilename, 'a', 'utf-8')
	
	files = [ line.strip() for line in codecs.open(inputDataFilename, 'r', 'utf-8') ]
	for polPath in files:
		print 'Starting', polPath
		progress_file.write('Starting {}\n'.format(polPath))
		packageName = getPackageName(polPath)
		policy = loadPrivacyPolicyResults(polPath, packageName, cdb, nlp, subsetNum)
		policy = [con.PolicyStatement(p) for p in set(policy) ]
		policyContradictions = con.getContradictions(policy, packageName)
		for (p0, p1), contradictionIndex in policyContradictions:
			print p0,p1,contradictionIndex, packageName
			print cdb.insertContradiction(None, None, contradictionIndex, packageName, p0.getTuple(), p1.getTuple())
		progress_file.write('Ending {}\n'.format(polPath))


if __name__ == '__main__':
	main(sys.argv)

