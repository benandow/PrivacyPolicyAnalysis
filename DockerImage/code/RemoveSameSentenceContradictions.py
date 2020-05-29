#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals
import os
import csv
import sqlite3
import sys
import networkx as nx
import pandas as pd
import dill as pickle

# Convert SQLite DB to CSV
def dumpTable(conn, query, fname, directory, header):
	table = [ data for data in conn.cursor().execute(query) ]
	outputfile = open(os.path.join(directory, fname), 'w')
	csvfile = csv.writer(outputfile, delimiter=str(','))
	csvfile.writerow(header)
	for row in table:
		csvfile.writerow(row)
	outputfile.close()

def dbToCsv(dbPath, output_dir = "/ext/combined_tables"):
	conn =  sqlite3.connect(dbPath)
	dumpTable(conn, 'SELECT policyId,entity,collect,data FROM Policy', "Policy.csv", output_dir, ("policyId", "entity", "action", "data"))
	dumpTable(conn, 'SELECT id,sentenceId,policyId,appId FROM AppPolicySentences', "PolicySentences.csv", output_dir, ["id", "sentenceId", "policyId", "appId"])
	dumpTable(conn, 'SELECT flowId,flowEntity,flowData FROM DataFlows', "DataFlows.csv", output_dir, ["flowId", "flowEntity", "flowData"])
	dumpTable(conn, 'SELECT appFlowId,flowId,appId,rawEntity,rawData FROM AppDataFlows', "AppDataFlows.csv", output_dir, ["appFlowId", "flowId", "appId", "rawEntity", "rawData"])
	dumpTable(conn, 'SELECT consistId,flowId,appId,isConsistent FROM ConsistencyResult', "ConsistencyResult.csv", output_dir, ["consistId", "flowId", "appId", "isConsistent"])
	dumpTable(conn, 'SELECT cdid,consistId,policyStatement,contradictingStatement,contradictionNum FROM ConsistencyData', "ConsistencyData.csv", output_dir, ["cdid", "consistId", "policyStatement", "contradictingStatement", "contradictionNum"])
	dumpTable(conn, 'SELECT contrId,contradictionId,appId,policyId1,policyId2 FROM Contradiction', "Contradiction.csv", output_dir, ["cid", "contrId", "packageName", "policyStatement", "contradictingStatement"])
	conn.close()

dbToCsv(os.path.join('/ext/output/db/', 'consistency_results_{}.db'.format(sys.argv[1])))

output_dir = "/ext/combined_tables"
policyCsv = os.path.join(output_dir, "Policy.csv")
policyDf = pd.read_csv(policyCsv, 
			usecols=["policyId","entity","action","data"],
			dtype = {
				"policyId" : int, "entity" : str,"action" : str,"data" : str
			},
			skip_blank_lines=True)
policyDf.fillna({
				"policyId" : -1, "entity" : '', "action" : '' ,"data" : ''
			}, inplace = True)

dataflowCsv = os.path.join(output_dir, "DataFlows.csv")
dataflowDf = pd.read_csv(dataflowCsv,
			usecols=["flowId", "flowEntity", "flowData"],
			dtype = {
				"flowId" : int, "flowEntity" : str, "flowData" : str
			},
			skip_blank_lines=True)
dataflowDf.fillna({
				"flowId" : -1, "flowEntity" : '', "flowData" : ''
			}, inplace = True)

appDataflowCsv = os.path.join(output_dir, "AppDataFlows.csv")
appDataflowDf = pd.read_csv(appDataflowCsv,
			usecols=["appFlowId", "flowId", "appId", "rawEntity", "rawData"],
			dtype = {
				"appFlowId" : int, "flowId" : int, "appId" : str, "rawEntity" : str, "rawData" : str
			},
			skip_blank_lines=True)
appDataflowDf.fillna({
				"appFlowId" : -1, "flowId" : -1, "appId" : '', "rawEntity" : '', "rawData" : ''
			}, inplace = True)



policySentencesCsv = os.path.join(output_dir, "PolicySentences.csv")
policySentencesDf = pd.read_csv(policySentencesCsv,
			usecols=["id", "sentenceId", "policyId", "appId"],
			dtype = {
				"id" : int, "sentenceId" : str, "policyId" : int, "appId" : str
			},
			skip_blank_lines=True)
policySentencesDf.fillna({
				"id" : -1, "sentenceId" : '', "policyId" : -1, "appId" : ''
			}, inplace = True)

consistencyResultCsv = os.path.join(output_dir, "ConsistencyResult.csv")
conResDf = pd.read_csv(consistencyResultCsv,
			usecols=["consistId", "flowId", "appId", "isConsistent"],
			dtype = {
				"consistId" : int, "flowId" : int, "appId" : str, "isConsistent" : str
			},
			skip_blank_lines=True)
conResDf.fillna({
				"consistId" : -1, "flowId" : -1, "appId" : '', "isConsistent" : ''
			}, inplace = True)


contradictionMap = {
	-1 : None, 0  : "C1", 1  : "C2", 2  : "N1", 3  : "C6", 4  : "C3", 5  : "C4", 6  : "N2", 7  : "C7", 8  : "N3", 
	9  : "C5", 10 : "N4", 11 : "C8", 12 : "C9", 13 : "C10", 14 : "C11", 15 : "C12",
}


consistencyDataCsv = os.path.join(output_dir, "ConsistencyData.csv")
conDataDf = pd.read_csv(consistencyDataCsv,
			usecols=["cdid", "consistId", "policyStatement", "contradictingStatement", "contradictionNum"],
			dtype = {
				"cdid" : int, "consistId" : int, "policyStatement" : int,
				"contradictingStatement" : float, "contradictionNum" : int,
			}, 
			skip_blank_lines=True)
conDataDf.fillna({
				"cdid" : -1, "consistId" : -1, "policyStatement" : -1,
				"contradictingStatement" : -1, "contradictionNum" : -1
			}, inplace = True)

conDataDf["contradictionNum"] = conDataDf["contradictionNum"].replace(contradictionMap)
conDataDf[["contradictingStatement"]] = conDataDf[["contradictingStatement"]].apply(pd.to_numeric, downcast='integer')



contradictionDataCsv = os.path.join(output_dir, "Contradiction.csv")
contrDataDf = pd.read_csv(contradictionDataCsv,
			usecols=["cid", "contrId", "packageName", "policyStatement", "contradictingStatement"],
			dtype = {
				"cid" : int, "contrId" : int, "packageName" : str, "policyStatement" : float,
				"contradictingStatement" : float,
			}, 
			skip_blank_lines=True)
contrDataDf.fillna({
				"cid" : -1, "contrId" : -1,  "packageName" : '', "policyStatement" : -1,
				"contradictingStatement" : -1,
			}, inplace = True)

contrDataDf["contrId"] = contrDataDf["contrId"].replace(contradictionMap)
contrDataDf[["policyStatement"]] = contrDataDf[["policyStatement"]].apply(pd.to_numeric, downcast='integer')
contrDataDf[["contradictingStatement"]] = contrDataDf[["contradictingStatement"]].apply(pd.to_numeric, downcast='integer')


def getSentences(policyId, appId):
	res = policySentencesDf.loc[(policySentencesDf["appId"] == appId) & (policySentencesDf["policyId"] == policyId)]
	return set([ sentenceText for _, _, sentenceText, _, _ in res.itertuples() ])


def resolvePolicyStatement(pid):
	if pid is None or pid == -1:
		return (None, None, None)
	_,pEntity,pSentiment,pData = policyDf.loc[ policyDf["policyId"] == pid ].values[0]
	return (pEntity,pSentiment,pData)

def writeCsvHeader(csvfile):
	csvfile.writerow(("packageName", "policyEntity", "policyAction", "policyData", "policySentences", "contradictionNum", "contradictoryEntity", "contradictoryAction", "contradictoryData", "contradictionSentences"))

def writeCsvRow(csvfile, packageName, policyEntity, policyAction, policyData, policySentences, contradictionNum, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences):
	csvfile.writerow((packageName, policyEntity, policyAction, policyData, policySentences.encode("utf-8") if policySentences is not None else None, contradictionNum, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences.encode("utf-8") if contradictionSentences is not None else None))

#Let's just make a new CSV...
outputfile = open('/ext/policylint_results.csv', 'w')
csvfile = csv.writer(outputfile, delimiter=str(','))
writeCsvHeader(csvfile)

#Remove self-contradictory sentences...
for _, cid, contrId, packageName, policyStatement, contradictingStatement in contrDataDf.itertuples():
	sentences1 = getSentences(policyStatement, packageName)
	sentences2 = getSentences(contradictingStatement, packageName)
	# Skip because the contradiction is drawn from the same sentences...
	# Note this may be overly aggressive in a corner case where EACH sentence is self-contradictory
	if len(sentences1) == 0 or len(sentences2) == 0 or sentences1 == sentences2 or sentences1.issubset(sentences2) or sentences2.issubset(sentences1):
		continue
	pEntity,pSentiment,pData = resolvePolicyStatement(policyStatement)
	cEntity,cSentiment,cData = resolvePolicyStatement(contradictingStatement)
	writeCsvRow(csvfile, packageName, pEntity, pSentiment, pData, "||".join(list(sentences1-sentences2)), contrId, cEntity, cSentiment, cData, "||".join(list(sentences2-sentences1)))

outputfile.close()

# Get all rows with pids / cids...
# Resolve sentences as above, if empty, skip
# If equal or one is a complete subset of another, choose most specific
# If has unique items in sentences, then keep

dataOnt = pickle.load(open('data_ontology.pickle', 'rb'))
entOnt = pickle.load(open('entity_ontology.pickle', 'rb'))

def getDistanceBetweenNodes(flowNode, policyNode, ont):
	return len(nx.shortest_path(ont, source=policyNode, target=flowNode)) - 1

def isDirectMatch(flowEntity, flowData, policyEntity, policyData):
	return flowEntity == policyEntity and flowData == policyData

def resolveNearestPolicy(flowEntity, flowData, policies):
	rankedList = []
	for pid,e,c,d in policies:
		if isDirectMatch(flowEntity, flowData, e, d):
			print(pid)
			return (0, 0, pid, e, c, d)
		entityDistance = getDistanceBetweenNodes(flowEntity, e, entOnt)
		dataDistance = getDistanceBetweenNodes(flowData, d, dataOnt)
		rankedList.append((entityDistance, dataDistance, pid, e, c, d))
	rankedList = sorted(rankedList)
	print(rankedList)
	return rankedList[0]

def resolvePolicyStatement(pid):
	if pid is None or pid == -1:
		return (None, None, None)
	_,pEntity,pSentiment,pData = policyDf.loc[ policyDf["policyId"] == pid ].values[0]
	return (pid, pEntity, pSentiment, pData)


for _, consistId, flowId, appId, isConsistent in conResDf.itertuples():
	cdata = conDataDf.loc[ (conDataDf["consistId"] == consistId) ]
	_,flowEntity,flowData = dataflowDf.loc[ dataflowDf["flowId"] == flowId ].values[0]
	#Select those from conDataDf with consistId...
	for index, cdid, _, policyStatement, contradictingStatement, ctype in cdata.itertuples():
		if policyStatement == -1 or policyStatement is None or contradictingStatement == -1 or contradictingStatement is None:
			continue
	
		psen = getSentences(policyStatement, packageName)
		csen = getSentences(contradictingStatement, packageName)
		if len(psen) == 0 or len(csen) == 0:#Should not happen...
			continue

		if psen == csen:
			#REMOVE contradiction completely. Keep most specific...
			_,_,xpid,_,_,_ = resolveNearestPolicy(flowEntity, flowData, [resolvePolicyStatement(policyStatement), resolvePolicyStatement(contradictingStatement)])
			print(flowEntity, flowData, resolvePolicyStatement(policyStatement), resolvePolicyStatement(contradictingStatement), xpid, policyStatement, contradictingStatement)
			if xpid == policyStatement:
				#Remove contradiction...
				conDataDf.at[index, "contradictingStatement"] = None
				conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]
			elif xpid == contradictingStatement:
				#Remove policy statement
				conDataDf.at[index, "policyStatement"] = contradictingStatement
				conDataDf.at[index, "contradictingStatement"] = None
				conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]
			else:
				print("Error resolving nearest statement in RemoveSameSentenceContradictions.py...")
		elif len(psen-csen) > 0 and len(csen-psen) > 0:
			#Do nothing...
			pass
		elif psen.issubset(csen):#issubset not equal based on above
			#Remove psen, keep csen....
			conDataDf.at[index, "policyStatement"] = conDataDf.at[index, "contradictingStatement"]
			conDataDf.at[index, "contradictingStatement"] = None
			conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]
		elif csen.issubset(psen):#issubset not equal based on above
			#Remove csen, keep psen...
			conDataDf.at[index, "contradictingStatement"] = None
			conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]


#Reverse mapping back so the next step does not mess up...
contradictionInvMap = { v : k for k,v in contradictionMap.iteritems() }
conDataDf["contradictionNum"] = conDataDf["contradictionNum"].replace(contradictionInvMap)

#Rewrite ConsistencyData.csv
header = ["cdid", "consistId", "policyStatement", "contradictingStatement", "contradictionNum"]
output_dir = "/ext/combined_tables"
outputfile = open(os.path.join(output_dir, "ConsistencyData_wo_samesencontr.csv"), 'w')
csvfile = csv.writer(outputfile, delimiter=str(','))
csvfile.writerow(header)
for index, cdid, consistId, policyStatement, contradictingStatement, contradictionNum in conDataDf.itertuples():
	csvfile.writerow((cdid, consistId, policyStatement, contradictingStatement, contradictionNum))
outputfile.close()
