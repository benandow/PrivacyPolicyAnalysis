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

		c.execute('DROP TABLE IF EXISTS AppFlows')
		c.execute("""CREATE TABLE AppFlows (id INTEGER PRIMARY KEY,
										flowEntity TEXT NOT NULL,
										flowData TEXT NOT NULL,
										appId TEXT NOT NULL,
										isSkipped INTEGER NOT NULL,
										UNIQUE(flowEntity, flowData, appId, isSkipped)
										)""")

		c.execute('DROP TABLE IF EXISTS ConsistencyResult')
		c.execute("""CREATE TABLE ConsistencyResult (consistId INTEGER PRIMARY KEY,
													flowEntity TEXT NOT NULL,
													flowData TEXT NOT NULL,
													appId TEXT NOT NULL,
													permissive INTEGER,
													strict INTEGER,
													strictContradiction INTEGER,
													intermediate INTEGER,
													intermediateContradiction INTEGER,
													FOREIGN KEY(permissive) REFERENCES Policy(policyId),
													FOREIGN KEY(strict) REFERENCES Policy(policyId),
													FOREIGN KEY(strictContradiction) REFERENCES Policy(policyId),
													FOREIGN KEY(intermediate) REFERENCES Policy(policyId),
													FOREIGN KEY(intermediateContradiction) REFERENCES Policy(policyId),
													UNIQUE(flowEntity, flowData, appId))""")

		c.execute('DROP TABLE IF EXISTS contradiction')
		c.execute("""CREATE TABLE Contradiction (contrId INTEGER PRIMARY KEY,
												flowEntity TEXT,
												flowData TEXT,
												contradictionId INTEGER NOT NULL,
												appId TEXT NOT NULL,
												policyId1 INTEGER NOT NULL,
												policyId2 INTEGER NOT NULL,
												FOREIGN KEY(policyId1) REFERENCES Policy(policyId),
												FOREIGN KEY(policyId2) REFERENCES Policy(policyId),
												UNIQUE(flowEntity, flowData, contradictionId, appId, policyId1, policyId2))""")
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
		except sqlite3.IntegrityError:
			return False
		return True

	def insertAppPolicySentence(self, sentenceId, policyId, appId):
		policyId = self.getPolicyId(policyId)
		return self.execInsertStatement('INSERT INTO AppPolicySentences (sentenceId, policyId, appId) VALUES (?,?,?)', (sentenceId, policyId, appId))

	def getAppPolicySentenceKey(self, params):#sentenceId, policyId, appId
		return self.getKeyFromTable('SELECT id FROM AppPolicySentences WHERE sentenceId=? AND policyId=? AND appId=?', params)

	def insertAppFlow(self, flowEntity, flowData, appId, isSkipped=False):#TODO insert test case...
		return self.execInsertStatement('INSERT INTO AppFlows (flowEntity, flowData, appId, isSkipped) VALUES (?,?,?,?)', (flowEntity, flowData, appId, 'true' if isSkipped else 'false'))

	def insertPolicy(self, entity, collect, data):
		return self.execInsertStatement('INSERT INTO Policy (entity, collect, data) VALUES (?,?,?)', (entity, collect, data))

	def getPolicyId(self, params):
		return self.getKeyFromTable('SELECT policyId FROM Policy WHERE entity=? AND collect=? AND data=?', params)

	def insertConsistencyResult(self, flowEntity, flowData, appId, permissive, strict, strictContradiction, intermediate, intermediateContradiction):
		permissive = self.getPolicyId(permissive) if permissive is not None else None
		strict = self.getPolicyId(strict) if strict is not None else None
		strictContradiction = self.getPolicyId(strictContradiction) if strictContradiction is not None else None
		intermediate = self.getPolicyId(intermediate)  if intermediate is not None else None
		intermediateContradiction = self.getPolicyId(intermediateContradiction) if intermediateContradiction is not None else None
		return self.execInsertStatement('INSERT INTO ConsistencyResult (flowEntity, flowData, appId, permissive, strict, strictContradiction, intermediate, intermediateContradiction) VALUES (?,?,?,?,?,?,?,?)', (flowEntity, flowData, appId, permissive, strict, strictContradiction, intermediate, intermediateContradiction))

	def insertContradiction(self, flowEntity, flowData, contradictionId, appId, policy1, policy2):
		policy1 = self.getPolicyId(policy1) if policy1 is not None else None
		policy2 = self.getPolicyId(policy2) if policy2 is not None else None
		return self.execInsertStatement('INSERT INTO Contradiction (flowEntity, flowData, contradictionId, appId, policyId1, policyId2) VALUES (?,?,?,?,?,?)', (flowEntity, flowData, contradictionId, appId, policy1, policy2))



