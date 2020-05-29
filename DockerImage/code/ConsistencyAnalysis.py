#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import csv
import dill as pickle
import json
import codecs
import re
import os
import pandas as pd
import TermPreprocessor2 as tprep
import spacy
import Consistency as con

import ConsistencyDatabase as conDB

USE_DOCKER = True 
ROOT_DIR='/ext/' if USE_DOCKER else '../../ext/'

def fixEntityLemma(txt, nlp):
	def getLemma(tok):
		return tok.lemma_ if tok.lemma_ != u'-PRON-' else tok.text
	doc = nlp(txt)
	return ' '.join([getLemma(t) for t in doc if t.pos != spacy.symbols.DET ])

def LOG_ERROR(outputfilename, message, outputDir='output/log_data'):
	outputDir = os.path.join(ROOT_DIR, outputDir)
	with codecs.open(os.path.join(outputDir, outputfilename), 'a', 'utf-8') as logfile:
		logfile.write(message)
		logfile.write('\n')

def ensureUnicode(s):
	return s.decode('utf-8') if type(s) == str else s


def loadFlowResults(filename, packageName, cdb, subsetNum):
	column_names = ['package_name', 'app_name', 'version_name', 'version_code', 'data_type', 'dest_domain', 'dest_ip', 'arb_number', 'privacy_policy']

	events_df = pd.read_csv(filename, header = 0, names = column_names, dtype={'app_name': unicode, 'privacy_policy': unicode})
	events_df.fillna(u'', inplace=True)

	dataMap = {
		u'aaid' : u'advertising identifier',
		u'fingerprint' : None,
		u'androidid' : u'android id',
		u'geolatlon' : u'geographical location',
		u'hwid' : u'serial number',
		u'routerssid' : u'router ssid',
		u'routermac' : u'mac address',
		u'imei' : u'imei',
		u'phone' : u'phone number',
		u'email' : u'email address',
		u'wifimac' : u'mac address',
		u'invasive' : None,
		u'package_dump' : u'application instal',
		u'simid' : u'sim serial number',
		u'real_name' : u'person name',
		u'gsfid' : u'gsfid'
	}

	pNameNoVers = re.sub(r'-[0-9]+$', '', packageName)

	flows = []
	for _,package_name, app_name, version_name, version_code, data_type, dest_domain, dest_ip, arb_number, privacy_policy in events_df.itertuples():
		if package_name != pNameNoVers:
			continue
		if dest_domain == '':
			dest_domain = dest_ip
		#TODO check if URL is first party or second party
		resolvedEntity = tprep.resolveUrl(dest_domain, package_name, privacy_policy)
		resolvedData = dataMap[data_type]

		if resolvedData is None:
			# log and continue
			LOG_ERROR('SkippedDataFlows_{}.log'.format(subsetNum), '{},{}'.format(data_type,packageName))
			continue
		if resolvedEntity not in con.Entity.ontology.nodes:#TODO log
			LOG_ERROR('SkippedEntityFlows_{}.log'.format(subsetNum), '{},{}'.format(dest_domain,packageName))
			continue
		if resolvedData not in con.DataObject.ontology.nodes:
			LOG_ERROR('SkippedDataFlowsOnt_{}.log'.format(subsetNum), '{},{}'.format(data_type,packageName))
			continue

		# TODO Don't put a duplicates...
		dflow = con.DataFlow((resolvedEntity, resolvedData))
		if dflow not in flows:
			flows.append(dflow)
			cdb.insertDataFlow(resolvedEntity, resolvedData)

		cdb.insertAppDataFlow(packageName, resolvedEntity, resolvedData, dest_domain, data_type)
	print '\tLoaded {} flows for {}'.format(len(flows), pNameNoVers)
	return flows


def shouldIgnoreSentence(s):
	mentionsChildRegex = re.compile(r'\b(child(ren)?|kids|from\sminor(s)?|under\s1[0-9]+|under\s(thirteen|fourteen|fifteen|sixteen|seventeen|eighteen)|age(s)?(\sof)?\s1[0-9]+|age(s)?(\sof)?\s(thirteen|fourteen|fifteen|sixteen|seventeen|eighteen))\b', flags=re.IGNORECASE)
	mentionsUserChoiceRegex = re.compile(r'\b(you|user)\s(.*\s)?(choose|do|decide|prefer)\s.*\s(provide|send|share|disclose)\b', flags=re.IGNORECASE)
	mentionsUserChoiceRegex2 = re.compile(r'\b((your\schoice)|(you\sdo\snot\shave\sto\sgive))\b', flags=re.IGNORECASE)
	# TODO remove false positives that discuss "except as discussed in this privacy policy / below"
	mentionsExceptInPrivacyPol1 = re.compile(r'\b(except\sas\s(stated|described|noted))\b', flags=re.IGNORECASE)
	mentionsExceptInPrivacyPol2 = re.compile(r'\b(except\sin(\sthose\slimited)?\s(cases))\b', flags=re.IGNORECASE)

	if mentionsChildRegex.search(s) or mentionsUserChoiceRegex.search(s) or mentionsUserChoiceRegex2.search(s) or mentionsExceptInPrivacyPol1.search(s) or mentionsExceptInPrivacyPol2.search(s):
		return True
	return False


def loadPrivacyPolicyResults(filename, packageName, cdb, nlp, subsetNum):
	if not os.path.isfile(filename):
		return []
	policy = []
	for e,c,d,s,aLemma in pickle.load(open(filename, 'rb')):
		e = ensureUnicode(e)
		c = ensureUnicode(c)
		d = ensureUnicode(d)
		s = ensureUnicode(s)

		if c == 'not_collect' and shouldIgnoreSentence(s):
			continue

		eproc = tprep.preprocess(fixEntityLemma(e, nlp))
		if eproc in [u'user', u'you', u'person', u'consumer', u'participant']:
			continue

		#TODO Should we try to resolve company name or ignore entity all together?
		# u'we_implicit'
		if eproc in [u'we', u'i', u'us', u'me'] or eproc in [u'app', u'mobile application', u'mobile app', u'application', u'service', u'website', u'web site', u'site'] or (e.startswith('our') and eproc in [u'app', u'mobile application', u'mobile app', u'application', u'service', u'company', u'business', u'web site', u'website', u'site']):
			eproc = u'we'

		if eproc == u'third_party_implicit' or eproc == u'we_implicit' or eproc == u'anyone':
			continue


#		if eproc == u'third_party_implicit':
#			eproc = u'third party'
		dproc = tprep.preprocess(d)

		ents = []
		if eproc not in con.Entity.ontology.nodes:
			res = re.sub(r'\b(and|or|and/or|\/|&)\b', u'\n', eproc)
			foundAnEnt = False
			for e in res.split('\n'):
				e = e.strip()
				if e == u'third_party_implicit' or e == u'we_implicit' or e == u'anyone':
					continue

				if e not in con.Entity.ontology.nodes:#This should really never happen...
					LOG_ERROR('/ext/SkippedPolicyEntities_{}.log'.format(subsetNum), e)
					continue
				ents.append(e)
		else:
			ents = [eproc]

		if len(ents) == 0:
			LOG_ERROR('/ext/SkippedPolicyEntities_{}.log'.format(subsetNum), eproc)
			continue

		if dproc in con.DataObject.ontology.nodes:
			if dproc in con.DataObject.ontology.nodes and dproc != con.DataObject.root:
				for e in ents:
					cdb.insertPolicy(e, c, dproc)
					cdb.insertAppPolicySentence(s, (e, c, dproc), packageName)
					policy.append((e, c, dproc, s))
		else:
			res = re.sub(r'\b(and|or|and/or|\/|&)\b', u'\n', dproc)
			for d in res.split('\n'):
				d = d.strip()
				if d not in con.DataObject.ontology.nodes or d == con.DataObject.root:#This should really never happen...
					LOG_ERROR('/ext/SkippedPolicyDataObjects_{}.log'.format(subsetNum), d)
					continue
				for e in ents:
					if e == con.Entity.root:
						continue
					cdb.insertPolicy(e, c, d)
					cdb.insertAppPolicySentence(s, (e, c, d), packageName)
					policy.append((e, c, d, s))

	return policy


def getPackageName(policyFilename):
	fname,_ = os.path.splitext(os.path.basename(policyFilename))
	return fname	

def doFilesExist(filelist):
	return all(os.path.exists(f) for f in filelist)

def main(argv):
	subsetNum = argv[1]
	#Assumes a number as input...
	consistency_database_path = os.path.join(ROOT_DIR, 'output/db/consistency_results_{}.db'.format(subsetNum))
	inputDataFilename = os.path.join(ROOT_DIR, 'datasets/{}.txt'.format(subsetNum))
	progressFilename = os.path.join(ROOT_DIR, 'output/log_data/{}.log'.format(subsetNum))

	cdb = conDB.ConsistencyDB(consistency_database_path)#'consistency_results.db'
	con.init(dataOntologyFilename=u'data_ontology.pickle', entityOntologyFilename=u'entity_ontology.pickle')
#	con.init_static()
	nlp = spacy.load('/ext/NlpFinalModel')
	cdb.createTables()
	# Let's walk the policy directory now...
	progress_file = codecs.open(progressFilename, 'a', 'utf-8')
	
	files = [ line.strip() for line in codecs.open(inputDataFilename, 'r', 'utf-8') ]
	for polPath in files:
		print 'Starting', polPath
		progress_file.write('Starting {}\n'.format(polPath))
		packageName = getPackageName(polPath)
		policy = loadPrivacyPolicyResults(os.path.join(ROOT_DIR, polPath), packageName, cdb, nlp, subsetNum)
		policy = [con.PolicyStatement(p) for p in set(policy) ]
		flows = loadFlowResults('/ext/data/flows.csv', packageName, cdb, subsetNum)
		print '\tLoaded {} policy statements for {}'.format(len(policy), packageName)


		#PolicyLint Analysis...
		policyContradictions = con.getContradictions(policy, packageName)
		for (p0, p1), contradictionIndex in policyContradictions:
			print p0,p1,contradictionIndex, packageName
			print cdb.insertContradiction(contradictionIndex, packageName, p0.getTuple(), p1.getTuple())		
		

		#PoliCheck Analysis...
		if len(flows) == 0:
			LOG_ERROR('SkippedAppsNoFlows_{}.log'.format(subsetNum), packageName)
			continue

		consistencyResults = con.checkConsistency(policy, flows)
		for cres in consistencyResults:
			flow = cres['flow']
			isConsistent,policies,contradictions = cres['consistency']

			cdb.insertConsistencyResult(flow.entity.entity, flow.data.data, packageName, isConsistent)

			numContradictions = 0
			if policies is not None:
				for i,p in enumerate(policies):
					pTuple = (p.entity.entity, p.action.action, p.data.data)
					if contradictions is not None and contradictions[i] is not None:
						for c,cnum in contradictions[i]:
							numContradictions += 1
							cTuple = (c.entity.entity, c.action.action, c.data.data)
							cdb.insertConsistencyData(flow.entity.entity, flow.data.data, packageName, pTuple, cTuple, cnum)
					else:
						cdb.insertConsistencyData(flow.entity.entity, flow.data.data, packageName, pTuple, None, -1)

			numPolicies = len(policies) if policies is not None else 0
			print '\tFlow: {}\n\t\tIs Consistent: {}\n\t\tNum Policies: {}\n\t\tNum Contradictions: {}\n'.format(flow, isConsistent, numPolicies, numContradictions)
	
		print 'Ending', polPath



if __name__ == '__main__':
	main(sys.argv)

