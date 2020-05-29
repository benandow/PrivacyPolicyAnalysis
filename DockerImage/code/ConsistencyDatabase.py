#!/usr/bin/env python
from __future__ import unicode_literals
import sqlite3

class ConsistencyDB:
	def __init__(self, dbfilename):
		self.conn = sqlite3.connect(dbfilename)

	def createTables(self):
		c = self.conn.cursor()

		c.execute('DROP TABLE IF EXISTS Policy')
		c.execute("""CREATE TABLE Policy (policyId INTEGER PRIMARY KEY,
										entity TEXT NOT NULL,
										collect TEXT NOT NULL,
										data TEXT NOT NULL,
										UNIQUE(entity, collect, data))""")

		c.execute('DROP TABLE IF EXISTS AppPolicySentences')
		c.execute("""CREATE TABLE AppPolicySentences (id INTEGER PRIMARY KEY,
										sentenceId TEXT NOT NULL,
										policyId INTEGER NOT NULL,
										appId TEXT NOT NULL,
										FOREIGN KEY(policyId) REFERENCES Policy(policyId),
										UNIQUE(sentenceId, policyId, appId)
										)""")

		c.execute('DROP TABLE IF EXISTS DataFlows')
		c.execute("""CREATE TABLE DataFlows (flowId INTEGER PRIMARY KEY,
										flowEntity TEXT NOT NULL,
										flowData TEXT NOT NULL,
										UNIQUE(flowEntity, flowData)
										)""")

		c.execute('DROP TABLE IF EXISTS AppDataFlows')
		c.execute("""CREATE TABLE AppDataFlows (appFlowId INTEGER PRIMARY KEY,
										flowId INTEGER NOT NULL,
										appId TEXT NOT NULL,
										rawEntity TEXT NOT NULL,
										rawData TEXT NOT NULL,
										FOREIGN KEY(flowId) REFERENCES DataFlows(flowId),
										UNIQUE(flowId, appId, rawEntity, rawData)
										)""")

		c.execute('DROP TABLE IF EXISTS ConsistencyResult')
		c.execute("""CREATE TABLE ConsistencyResult (consistId INTEGER PRIMARY KEY,
													flowId INTEGER NOT NULL,
													appId TEXT NOT NULL,
													isConsistent TEXT NOT NULL,
													FOREIGN KEY(flowId) REFERENCES DataFlows(flowId),
													UNIQUE(flowId, appId))""")

		c.execute('DROP TABLE IF EXISTS ConsistencyData')
		c.execute("""CREATE TABLE ConsistencyData (cdid INTEGER PRIMARY KEY,
													consistId INTEGER NOT NULL,
													policyStatement INTEGER NOT NULL,
													contradictingStatement INTEGER,
													contradictionNum INTEGER,
													FOREIGN KEY(consistId) REFERENCES ConsistencyResult(consistId),
													FOREIGN KEY(policyStatement) REFERENCES Policy(policyId),
													FOREIGN KEY(contradictingStatement) REFERENCES Policy(policyId),
													UNIQUE(consistId, policyStatement, contradictingStatement, contradictionNum))""")


		c.execute('DROP TABLE IF EXISTS Contradiction')
		c.execute("""CREATE TABLE Contradiction (contrId INTEGER PRIMARY KEY,
												contradictionId INTEGER NOT NULL,
												appId TEXT NOT NULL,
												policyId1 INTEGER NOT NULL,
												policyId2 INTEGER NOT NULL,
												FOREIGN KEY(policyId1) REFERENCES Policy(policyId),
												FOREIGN KEY(policyId2) REFERENCES Policy(policyId),
												UNIQUE(contradictionId, appId, policyId1, policyId2))""")


		self.conn.commit()


	def getKeyFromTable(self, query, params):
		# We already have the key...
		if params is None or type(params) != tuple:
			return params
		try:
			c = self.conn.cursor()
			res = c.execute(query, params)
			for r in res:
				return r[0]
		except:
			pass
		return None

	def execInsertStatement(self, query, params):
		try:
			c = self.conn.cursor()
			c.execute(query, params)
			self.conn.commit()
		except sqlite3.IntegrityError as e:
			#print e, query
			return False
		return True


	def insertPolicy(self, entity, collect, data):
		if self.getPolicyId(( entity, collect, data)) is not None:
			return True
		return self.execInsertStatement('INSERT INTO Policy (entity, collect, data) VALUES (?,?,?)', (entity, collect, data))

	def getPolicyId(self, params):
		return self.getKeyFromTable('SELECT policyId FROM Policy WHERE entity=? AND collect=? AND data=?', params)

	def insertAppPolicySentence(self, sentenceId, policy, appId):
		policyId = self.getPolicyId(policy)
		if self.getAppPolicySentenceKey((sentenceId, policyId, appId)) is not None:
			return True
		return self.execInsertStatement('INSERT INTO AppPolicySentences (sentenceId, policyId, appId) VALUES (?,?,?)', (sentenceId, policyId, appId))

	def getAppPolicySentenceKey(self, params):#sentenceId, policyId, appId
		return self.getKeyFromTable('SELECT id FROM AppPolicySentences WHERE sentenceId=? AND policyId=? AND appId=?', params)

	
	def insertDataFlow(self, flowEntity, flowData):
		if self.getDataFlowKey((flowEntity, flowData)) is not None:
			return True
		return self.execInsertStatement('INSERT INTO DataFlows (flowEntity, flowData) VALUES (?,?)', (flowEntity, flowData))


	def getDataFlowKey(self, params):
		return self.getKeyFromTable('SELECT flowId FROM DataFlows WHERE flowEntity=? AND flowData=?', params)


	def insertAppDataFlow(self, appId, flowEntity, flowData, rawEntity, rawData):#TODO insert test case...
		flowId = self.getDataFlowKey((flowEntity, flowData))
		if self.getAppDataFlowKey((flowId, appId, rawEntity, rawData)) is not None:
			return True
		return self.execInsertStatement('INSERT INTO AppDataFlows (flowId, appId, rawEntity, rawData) VALUES (?,?,?,?)', (flowId, appId, rawEntity, rawData))

	def getAppDataFlowKey(self, params):#TODO insert test case...
		return self.getKeyFromTable('SELECT appFlowId FROM AppDataFlows WHERE flowId=? AND appId=? AND rawEntity=? AND rawData=?', params)

	
	def insertConsistencyResult(self, flowEntity, flowData, appId, isConsistent):#TODO insert test case...
		flowId = self.getDataFlowKey((flowEntity, flowData))
		isConsistent = "TRUE" if isConsistent else "FALSE"
		if self.getConsistencyKey((flowId,appId)) is not None:
			return True
		res = self.execInsertStatement('INSERT INTO ConsistencyResult (flowId, appId, isConsistent) VALUES (?,?,?)', (flowId, appId, isConsistent))
		return res

	def getConsistencyKey(self, params):#TODO insert test case...
		return self.getKeyFromTable('SELECT consistId FROM ConsistencyResult WHERE flowId=? AND appId=?', params)

	
	def insertConsistencyData(self, flowEntity, flowData, appId, policy1, contradictPolicy, contradictionNum):#TODO insert test case...
		flowId = self.getDataFlowKey((flowEntity, flowData))
		policyId = self.getPolicyId(policy1)
		contrPolicyId = self.getPolicyId(contradictPolicy)
		consistId = self.getConsistencyKey((flowId, appId))
		if self.getConsistencyDataKey((consistId, policyId, contrPolicyId)):
			return True
		return self.execInsertStatement('INSERT INTO ConsistencyData (consistId, policyStatement, contradictingStatement, contradictionNum) VALUES (?,?,?,?)', (consistId, policyId, contrPolicyId, contradictionNum))

	def getConsistencyDataKey(self, params):#TODO insert test case...
		return self.getKeyFromTable('SELECT cdid FROM ConsistencyData WHERE consistId=? AND policyStatement=? AND contradictingStatement=?', params)


	def insertContradiction(self, contradictionId, appId, policy1, policy2):
		policy1 = self.getPolicyId(policy1) if policy1 is not None else None
		policy2 = self.getPolicyId(policy2) if policy2 is not None else None
		return self.execInsertStatement('INSERT INTO Contradiction (contradictionId, appId, policyId1, policyId2) VALUES (?,?,?,?)', (contradictionId, appId, policy1, policy2))



