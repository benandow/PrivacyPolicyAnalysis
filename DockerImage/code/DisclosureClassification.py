#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import pickle
import networkx as nx
import pandas as pd
import csv
import sqlite3
import sys
output_dir = "/ext/combined_tables"



# In[2]:


policyCsv = os.path.join(output_dir, "Policy.csv")
policyDf = pd.read_csv(policyCsv, 
			usecols=["policyId","entity","action","data"],
			dtype = {
				"policyId" : int, "entity" : str,"action" : str,"data" : str
			},
			skip_blank_lines=True)
policyDf.fillna({
				"policyId" : -1,"entity" : '',"action" : '',"data" : ''
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

policySentencesDf["shouldIgnore"] = False

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

consistencyDataCsv = os.path.join(output_dir, "ConsistencyData_wo_samesencontr.csv")
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


# In[3]:

#Heuristic to remove broad info mentions...
corefCheck = re.compile(r"""\b(this|that|these|those|such)\s((type(s)?|kind(s)|categor(ies|y))\sof\s)?(request(ed)?\s)?(personal|personally(\s|\-)identifiable)?(information|data|content|datum|detail(s)?)\b""", re.IGNORECASE)

totalExclude = 0
for index, psid, sentenceText, policyId, appId,_ in policySentencesDf.itertuples():
	_,pEntity,pAction,pData = policyDf.loc[ policyDf["policyId"] == policyId ].values[0]
	if pData == "information" and corefCheck.search(sentenceText):
		policySentencesDf.at[index, "shouldIgnore"] = True
		totalExclude += 1
#print("Excluded ", totalExclude, 'sentences out of', len(policySentencesDf))

policySentencesDf.to_csv("PolicySentences_w_shouldIgnore.csv", sep=str(','), encoding='utf-8', index=False)


# In[4]:


psRemovedDf = policySentencesDf.loc[ policySentencesDf["shouldIgnore"] == True ]
potImpactConsistIds = set()
#Get keys of potential rows impacted...
for _,sid, sText, policyId, appId,_ in psRemovedDf.itertuples():
	crDf = conResDf.loc[ conResDf["appId"] == appId ]
	for _,consistId, flowId, _, _ in crDf.itertuples():
		cdDf = conDataDf.loc[ (conDataDf["consistId"] == consistId) ]
		for _,cdid, _, sPolicyId1, cPolicyId2, contrNum in cdDf.itertuples():
			if sPolicyId1 == policyId or cPolicyId2 == policyId:
				potImpactConsistIds.add(consistId)

#print(len(potImpactConsistIds))


# In[5]:


for _,consistId, flowId, appId, _ in conResDf.itertuples():
	# Get all policy statements that either justified or did not justify beforehand...
	cdata = conDataDf.loc[ conDataDf["consistId"] == consistId ]
	# Get all the unignored policy statements
	pids = [ a[0] for a in policySentencesDf.loc[ (policySentencesDf["appId"] == appId) & (policySentencesDf["shouldIgnore"] == False) ].groupby("policyId")["policyId"].unique().tolist() ]

	for index,cdid, _, p1, c1, ct in cdata.itertuples():
		if p1 in pids and (c1 in pids or c1 == -1):#Nothing changed...
			continue

		if p1 not in pids and c1 not in pids:# Remove entirely
			print("Remove1", c1, p1, appId)
			conDataDf.drop(index, inplace=True)
		if p1 not in pids and c1 in pids:#Remove p1 and move c1 to p1
			print("Remove2", p1, appId)
			conDataDf.at[index, "policyStatement"] = conDataDf.at[index, "contradictingStatement"]
			conDataDf.at[index, "contradictingStatement"] = -1
			conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]
		if p1 in pids and c1 != -1 and c1 not in pids:#Remove c1
			print("Remove3", c1, appId)
			conDataDf.at[index, "contradictingStatement"] = -1
			conDataDf.at[index, "contradictionNum"] = contradictionMap[-1]


# In[6]:


dataOnt = pickle.load(open('data_ontology.pickle', 'rb'))
entOnt = pickle.load(open('entity_ontology.pickle', 'rb'))

def getDistanceBetweenNodes(flowNode, policyNode, ont):
	return len(nx.shortest_path(ont, source=policyNode, target=flowNode)) - 1

def getNormalizedDistanceBetweenNodes(flowNode, policyNode, ontology, root):
	ftpDistance = float(getDistanceBetweenNodes(flowNode, policyNode, ontology))
	ptrDistance = float(getDistanceBetweenNodes(policyNode, root, ontology))
	return ftpDistance / (ftpDistance + ptrDistance)

def resolvePolicyStatement(pid):
	if pid is None or pid == -1:
		return (None, None, None)
	_,pEntity,pSentiment,pData = policyDf.loc[ policyDf["policyId"] == pid ].values[0]
	return (pEntity,pSentiment,pData)

def writeCsvRow(csvfile, packageName, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, consistencyResult, entityVagueness, entityVaguenessRaw, dataVagueness, dataVaguenessRaw, contradictionNum, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences):
	csvfile.writerow((packageName, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences.encode("utf-8") if policySentences is not None else None, consistencyResult, entityVagueness, entityVaguenessRaw, dataVagueness, dataVaguenessRaw, contradictionNum, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences.encode("utf-8") if contradictionSentences is not None else None))

def writeCsvHeader(csvfile):
	csvfile.writerow(("packageName", "flowEntity", "flowData", "policyEntity", "policyAction", "policyData", "policySentences", "consistencyResult", "entityVagueness", "entityVaguenessRaw", "dataVagueness", "dataVaguenessRaw", "contradictionNum", "contradictoryEntity", "contradictoryAction", "contradictoryData", "contradictionSentences"))

def filteredAppend(PF, p1, pEntity, pSentiment, pData, cType, cPol):
	if flowEntity == u"we" and pEntity != u'we':
		return#First party should not be "anyone"
	if cPol is not None:
		c1, cEntity, cSentiment, cData = cPol
		if flowEntity == u"we" and cEntity != u'we':
			return#Again, first party should not be "anyone"
	PF.append((p1, pEntity, pSentiment, pData, cType, cPol))

def getPolicyStatementTypes(xdata, flowEntity):
	PFP = []#Positive
	PFN = []#Negative
	PN = []#Narrowing
	PC = []#Contradictions

	for index,_, _, p1, c1,ctype in xdata.itertuples():
		pEntity,pSentiment,pData = resolvePolicyStatement(p1)
		cEntity,cSentiment,cData = resolvePolicyStatement(c1)

		if pSentiment == "collect":
			filteredAppend(PFP, p1, pEntity, pSentiment, pData, None, None)
			#PFP.append((p1, pEntity, pSentiment, pData, None, None))
		else:
			filteredAppend(PFN, p1, pEntity, pSentiment, pData, None, None)
			#PFN.append((p1, pEntity, pSentiment, pData, None, None))

		if cSentiment is not None and cSentiment == "collect":
			filteredAppend(PFP, c1, cEntity, cSentiment, cData, None, None)
			#PFP.append((c1, cEntity, cSentiment, cData, None, None))
		elif cSentiment is not None:
			filteredAppend(PFN, c1, cEntity, cSentiment, cData, None, None)
			#PFN.append((c1, cEntity, cSentiment, cData, None, None))

		if ctype is not None:
			if ctype.startswith("C"):
				filteredAppend(PC, p1, pEntity, pSentiment, pData, ctype, (c1, cEntity, cSentiment, cData))
				filteredAppend(PC, c1, cEntity, cSentiment, cData, ctype, (p1, pEntity, pSentiment, pData))
#				PC.append((p1, pEntity, pSentiment, pData, ctype, (c1, cEntity, cSentiment, cData)))
#				PC.append((c1, cEntity, cSentiment, cData, ctype, (p1, pEntity, pSentiment, pData)))
			else:
				filteredAppend(PN, p1, pEntity, pSentiment, pData, ctype, (c1, cEntity, cSentiment, cData))
				filteredAppend(PN, c1, cEntity, cSentiment, cData, ctype, (p1, pEntity, pSentiment, pData))
				#PN.append((p1, pEntity, pSentiment, pData, ctype, (c1, cEntity, cSentiment, cData)))
				#PN.append((c1, cEntity, cSentiment, cData, ctype, (p1, pEntity, pSentiment, pData)))
	return (PFP, PFN, PN, PC)

def isDirectMatch(flowEntity, flowData, policyEntity, policyData):
	return flowEntity == policyEntity and flowData == policyData

def resolveNearestPolicy(flowEntity, flowData, policies):
	rankedList = []
	for pid,e,c,d,ctype,contr in policies:
		if isDirectMatch(flowEntity, flowData, e, d):
			return (0, 0, pid, e, c, d, ctype, contr)
		entityDistance = getDistanceBetweenNodes(flowEntity, e, entOnt)
		dataDistance = getDistanceBetweenNodes(flowData, d, dataOnt)
		rankedList.append((entityDistance, dataDistance, pid, e, c, d, ctype, contr))
	rankedList = sorted(rankedList)
	return rankedList[0]

def convertToUnicode(val):
	return val
#	if type(val) == str:
#		return unicode(val, "utf-8")
#	return val

def getSentences(policyId, appId):
	sentences = []
	res = policySentencesDf.loc[(policySentencesDf["appId"] == appId) & (policySentencesDf["policyId"] == policyId) & (policySentencesDf["shouldIgnore"] == False)]
	for _, _, sentenceText, _, _,_ in res.itertuples():
		sentences.append(convertToUnicode(sentenceText))
	return u"||".join(sentences)


outputfile = open('/ext/policheck_results.csv', 'w')
csvfile = csv.writer(outputfile, delimiter=str(','))

writeCsvHeader(csvfile)

finImpactCoref = set()

for _,consistId, flowId, appId, _ in conResDf.itertuples():
	_,flowEntity,flowData = dataflowDf.loc[ dataflowDf["flowId"] == flowId ].values[0]
	cdata = conDataDf.loc[ conDataDf["consistId"] == consistId ]
	PFp, PFn, PN, PC = getPolicyStatementTypes(cdata, flowEntity)

	#If PN == 0 and PC == 0 and PFp == PFn
	if len(PN) == 0 and len(PC) == 0 and len(PFp) > 0 and len(PFn) > 0: #We had a same sentence contradiction that we removed, let's find the closest match and wipe the rest...
		_, _, pid, policyEntity, policyAction, policyData,_,_ = resolveNearestPolicy(flowEntity, flowData, PFn + PFp)
		if policyAction == 'collect':
			PFn = []
		else:
			PFp = []

	if len(PFp) == 0 and len(PFn) == 0:
		if consistId in potImpactConsistIds:
			finImpactCoref.add(consistId)
		writeCsvRow(csvfile, appId, flowEntity, flowData, None, None, None, None, "omitted", None, None, None, None, None, None, None, None, None)
		pass
	elif (len(PFp) == 0 and len(PFn) > 0):# PN and PC are empty in this case...
		# Incorrect
		_, _, pid, policyEntity, policyAction, policyData,_,_ = resolveNearestPolicy(flowEntity, flowData, PFn)
		policySentences = getSentences(pid, appId)
		writeCsvRow(csvfile, appId, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, "incorrect", None, None, None, None, None, None, None, None, None)
	elif len(PFp) > 0 and len(PFn) == 0:
		entDist, dataDist, pid, policyEntity, policyAction, policyData, _, _ = resolveNearestPolicy(flowEntity, flowData, PFp)
		if entDist == 0 and dataDist == 0:
			policySentences = getSentences(pid, appId)
			writeCsvRow(csvfile, appId, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, "clear", 0.0, 0.0, 0.0, 0.0, None, None, None, None, None)
		else:
			policySentences = getSentences(pid, appId)
			entityVagueness = getNormalizedDistanceBetweenNodes(flowEntity, policyEntity, entOnt, "anyone") if policyEntity != 'we' else 0.0
			dataVagueness = getNormalizedDistanceBetweenNodes(flowData, policyData, dataOnt, "information")
			entityVaguenessRaw = getDistanceBetweenNodes(flowEntity, policyEntity, entOnt) if policyEntity != 'we' else 0.0
			dataVaguenessRaw = getDistanceBetweenNodes(flowData, policyData, dataOnt)
			writeCsvRow(csvfile, appId, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, "vague", entityVagueness, entityVaguenessRaw, dataVagueness, dataVaguenessRaw, None, None, None, None, None)
	elif len(PC) > 0:
		# Ambiguous
		_, _, pid, policyEntity, policyAction, policyData, ctype, contr = resolveNearestPolicy(flowEntity, flowData, PC)
		contrPid,contradictoryEntity,contradictoryAction,contradictoryData = contr
		policySentences = getSentences(pid, appId)
		contradictionSentences = getSentences(contrPid, appId)
		writeCsvRow(csvfile, appId, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, "ambiguous", None, None, None, None, ctype, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences)
	elif len(PN) > 0 and len(PC) <= 0:
		_, _, pid, policyEntity, policyAction, policyData, ctype, contr = resolveNearestPolicy(flowEntity, flowData, PN)
		contrPid,contradictoryEntity,contradictoryAction,contradictoryData = contr
		policySentences = getSentences(pid, appId)
		contradictionSentences = getSentences(contrPid, appId)
		writeCsvRow(csvfile, appId, flowEntity, flowData, policyEntity, policyAction, policyData, policySentences, "incorrect", None, None, None, None, ctype, contradictoryEntity, contradictoryAction, contradictoryData, contradictionSentences)
		#Incorrect
		pass
	else:
		print("Warning: We did not classify a flow...", appId, len(PFp), len(PFn), len(PN), len(PC))
outputfile.close()


#print("Number Of rows impacted by coreference resolution: {}".format(len(finImpactCoref)))
print("Done")



