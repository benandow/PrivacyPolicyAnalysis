#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

# In[7]:


import sqlite3
import os
import re
import pickle
import networkx as nx
import csv


# In[8]:


databasePath = '/ext/output/db/'
def getDatabaseFilenames(path):
	res = []
	for root,dirs,files in os.walk(path):
		for f in files:
			res.append(os.path.join(root, f))
	return res

dbFiles = getDatabaseFilenames(databasePath)
print(dbFiles)


# In[9]:


#CREATE TABLE Policy (policyId INTEGER PRIMARY KEY,
#						entity TEXT NOT NULL,
#						collect TEXT NOT NULL,
#						data TEXT NOT NULL,
#						UNIQUE(entity, collect, data)
#						);
#CREATE TABLE AppPolicySentences (id INTEGER PRIMARY KEY,
#								sentenceId TEXT NOT NULL,
#								policyId INTEGER NOT NULL,
#								appId TEXT NOT NULL,
#								FOREIGN KEY(policyId) REFERENCES Policy(policyId),
#								UNIQUE(sentenceId, policyId, appId)
#								);
#CREATE TABLE DataFlows (flowId INTEGER PRIMARY KEY,
#						flowEntity TEXT NOT NULL,
#						flowData TEXT NOT NULL,
#						UNIQUE(flowEntity, flowData)
#						);
#CREATE TABLE AppDataFlows (appFlowId INTEGER PRIMARY KEY,
#							flowId INTEGER NOT NULL,
#							appId TEXT NOT NULL,
#							rawEntity TEXT NOT NULL,
#							rawData TEXT NOT NULL,
#							FOREIGN KEY(flowId) REFERENCES DataFlows(flowId),
#							UNIQUE(flowId, appId, rawEntity, rawData)
#							);
#CREATE TABLE ConsistencyResult (consistId INTEGER PRIMARY KEY,
#								flowId INTEGER NOT NULL,
#								appId TEXT NOT NULL,
#								isConsistent TEXT NOT NULL,
#								FOREIGN KEY(flowId) REFERENCES DataFlows(flowId),
#								UNIQUE(flowId, appId)
#								);
#CREATE TABLE ConsistencyData (cdid INTEGER PRIMARY KEY,
#								consistId INTEGER NOT NULL,
#								policyStatement INTEGER NOT NULL,
#								contradictingStatement INTEGER,
#								contradictionNum INTEGER,
#								FOREIGN KEY(consistId) REFERENCES ConsistencyResult(consistId),
#								FOREIGN KEY(policyStatement) REFERENCES Policy(policyId),
#								FOREIGN KEY(contradictingStatement) REFERENCES Policy(policyId),
#								UNIQUE(consistId, policyStatement, contradictingStatement, contradictionNum));

def connectToDatabase(dbFilename):
	conn = sqlite3.connect(dbFilename)
	return conn

def getPolicies(conn):
	result = {}
	for policyId,entity,collect,data in conn.cursor().execute('SELECT policyId,entity,collect,data FROM Policy'):
		pid = int(policyId)
		if pid in result:
			print("Error: Duplicate Policy id...")
		result[pid] = { "entity" : entity, "action" : collect, "data" : data }
	return result

def getAppPolicySentences(conn):
	result = {}
	for apsid,sentenceId,policyId,appId in conn.cursor().execute('SELECT id,sentenceId,policyId,appId FROM AppPolicySentences'):
		pid = int(apsid)
		if pid in result:
			print("Error: Duplicate AppPolicySentences id...")
		result[pid] = { "sentence_text" : sentenceId, "policy_id" : policyId, "package_name" : appId }
	return result

def getDataFlows(conn):
	result = {}
	for flowId,flowEntity,flowData in conn.cursor().execute('SELECT flowId,flowEntity,flowData FROM DataFlows'):
		fid = int(flowId)
		if fid in result:
			print("Error: Duplicate DataFlows id...")
		result[fid] = { "entity" : flowEntity, "data" : flowData }
	return result

def getAppDataFlows(conn):
	result = {}
	for appFlowId,flowId,appId,rawEntity,rawData in conn.cursor().execute('SELECT appFlowId,flowId,appId,rawEntity,rawData FROM AppDataFlows'):
		fid = int(appFlowId)
		if fid in result:
			print("Error: Duplicate AppDataFlows id...")
		result[fid] = {"flow_id" : int(flowId), "package_name" : appId, "raw_entity" : rawEntity, "raw_data" : rawData}
	return result

def getConsistencyResult(conn):
	result = {}
	for consistId,flowId,appId,isConsistent in conn.cursor().execute('SELECT consistId,flowId,appId,isConsistent FROM ConsistencyResult'):
		cid = int(consistId)
		if cid in result:
			print("Error: Duplicate AppDataFlows id...")
		result[cid] = {"flow_id" : int(flowId), "package_name" : appId, "is_consistent" : True if isConsistent == "TRUE" else False}
	return result

def getConsistencyData(conn):
	result = {}
	for cdid,consistId,policyStatement,contradictingStatement,contradictionNum in conn.cursor().execute('SELECT cdid,consistId,policyStatement,contradictingStatement,contradictionNum FROM ConsistencyData'):
		cid = int(cdid)
		if cid in result:
			print("Error: Duplicate AppDataFlows id...")
		result[cid] = {"conres_id" : int(consistId), "policy" : policyStatement, "con_policy" : contradictingStatement, "con_num" : contradictionNum}
	return result


# In[10]:


# Let's aggregate the database into one new database...
# First let's load EVERYTHING!!!
def loadAllData(dbFiles):
	result = []
	for db in dbFiles:
		conn = connectToDatabase(db)
		result.append({
			"policy" : getPolicies(conn),
			"policy_sentences" : getAppPolicySentences(conn),
			"data_flows" : getDataFlows(conn),
			"app_data_flows" : getAppDataFlows(conn),
			"consistency_result" : getConsistencyResult(conn),
			"consistency_data" : getConsistencyData(conn)})
		conn.close()
	return result

data = loadAllData(dbFiles)


# In[11]:


def buildTranslationMap(translationMap, lookupMap, data, i, newId, keyName, keyGenFunct, opts=None):
	for identifier in data[i][keyName]:# Old primary key of table
		res = data[i][keyName][identifier] # Values under old primary key
		key = keyGenFunct(res, opts) # Unique attributes of old table
		if key not in lookupMap:
			lookupMap[key] = newId
			newId += 1
		translationMap[(i, identifier)] = (lookupMap[key], key)
	return newId

def genDataFlowKey(res, opts=None):
	return (res["entity"], res["data"])

def genPolicyKey(res, opts=None):
	return (res["entity"], res["action"], res["data"])

def getConsistencyKey(res, opts):
	i,ftmap = opts
	newFlowId = ftmap[(i,res["flow_id"])][0]
	return (newFlowId, res["package_name"], res["is_consistent"])

def getAppPolicySentenceKey(res, opts):
	i,ptmap = opts
	newPolicyId = ptmap[(i, res["policy_id"])][0]
	return (res["sentence_text"], newPolicyId, res["package_name"])

def genAppDataFlowKey(res, opts):
	i,ftmap = opts
	newFlowId = ftmap[(i, res["flow_id"])][0]
	return (newFlowId, res["package_name"], res["raw_entity"], res["raw_data"])

def genConsistencyDataKey(res, opts):
	i,(ptmap, crtmap) = opts
	newConResId = crtmap[(i, res["conres_id"])][0]
	newPolicyId = ptmap[(i, res["policy"])][0]
	newConPolicyId = ptmap[(i, res["con_policy"])][0] if res["con_policy"] is not None else None
	return (newConResId, newPolicyId, newConPolicyId, res["con_num"])

def getTranslationMap(data, keyName, keyGenFunct, keyTranslationMaps=None):
	translationMap = {}
	lookupMap = {}
	newIdentifier = 1
	for i,_ in enumerate(data):
		newIdentifier = buildTranslationMap(translationMap, lookupMap, data, i, newIdentifier, keyName, keyGenFunct, opts=(i, keyTranslationMaps))
	return translationMap

def getTranslationMaps(data):
	ptmap = getTranslationMap(data, "policy", genPolicyKey)
	psmap = getTranslationMap(data, "policy_sentences", getAppPolicySentenceKey, keyTranslationMaps=ptmap)
	ftmap = getTranslationMap(data, "data_flows", genDataFlowKey)
	aftmap = getTranslationMap(data, "app_data_flows", genAppDataFlowKey, keyTranslationMaps=ftmap)
	crtmap = getTranslationMap(data, "consistency_result", getConsistencyKey, keyTranslationMaps=ftmap)
	cdtmap = getTranslationMap(data, "consistency_data", genConsistencyDataKey, keyTranslationMaps=(ptmap, crtmap))
	return (ptmap, psmap, ftmap, aftmap, crtmap, cdtmap)

ptmap, psmap, ftmap, aftmap, crtmap, cdtmap = getTranslationMaps(data)


# In[12]:


def genTuple(newKey, rowVals):
	res = [newKey]
	for r in rowVals:
		res.append(r)
	return tuple(res)

def genTable(tmap):
	return sorted(list(set([ genTuple(tmap[key][0], tmap[key][1]) for key in tmap ])))

def dumpTable(table, fname, directory, header):
	outputfile = open(os.path.join(directory, fname), 'w')
	csvfile = csv.writer(outputfile, delimiter=',')
	csvfile.writerow(header)
	for row in table:
		csvfile.writerow(row)
	outputfile.close()

output_dir = "/ext/combined_tables"

policyTable = genTable(ptmap)
dumpTable(policyTable, "Policy.csv", output_dir, ("policyId", "entity", "action", "data"))

policySentenceTable = genTable(psmap)
dumpTable(policySentenceTable, "PolicySentences.csv", output_dir, ["id", "sentenceId", "policyId", "appId"])

flowTable = genTable(ftmap)
dumpTable(flowTable, "DataFlows.csv", output_dir, ["flowId", "flowEntity", "flowData"])

appFlowTable = genTable(aftmap)
dumpTable(appFlowTable, "AppDataFlows.csv", output_dir, ["appFlowId", "flowId", "appId", "rawEntity", "rawData"])

consistencyResTable = genTable(crtmap)
dumpTable(consistencyResTable, "ConsistencyResult.csv", output_dir, ["consistId", "flowId", "appId", "isConsistent"])

consistencyDataTable = genTable(cdtmap)
dumpTable(consistencyDataTable, "ConsistencyData.csv", output_dir, ["cdid", "consistId", "policyStatement", "contradictingStatement", "contradictionNum"])



