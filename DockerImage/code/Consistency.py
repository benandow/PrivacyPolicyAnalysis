#!/usr/bin/env python
from __future__ import unicode_literals
import OntologyOps as ontutils
import networkx as nx

# Input flow=(entity, data object), policies=[(entity, collect/not_collect, data object), ...]

class Entity:
	def __init__(self, entity):
		self.entity = entity

	@staticmethod
	def loadOntology(filename, ontology=None, rootNode=u'anyone'):
		Entity.ontology = ontutils.loadEntityOntology(filename) if ontology is None else ontology
		Entity.root = rootNode

	@staticmethod
	def loadStaticOntology():
		edges = [
			(u'anyone', u'third_party'),
			(u'anyone', u'we'),
			(u'third_party', u'advertising_network'),
			(u'third_party', u'analytic_provider'),
			(u'third_party', u'social_network'),
			(u'advertising_network', u'google'),
			(u'analytic_provider', u'google'),
			(u'google', u'crashlytics'),
			(u'google', u'google ads'),

			(u'analytic_provider', u'appsflyer'),
			(u'advertising_network', u'facebook'),
			(u'analytic_provider', u'facebook'),
			(u'social_network', u'facebook'),
			(u'advertising_network', u'verizon'),
			(u'analytic_provider', u'verizon'),
			(u'verizon', u'flurry'),
			(u'analytic_provider', u'branch'),
			(u'advertising_network', u'unity'),
			(u'analytic_provider', u'unity'),
			(u'analytic_provider', u'adjust'),
			(u'analytic_provider', u'kochava'),
			(u'advertising_network', u'mopub'),
			(u'analytic_provider', u'mopub'),
			(u'advertising_network', u'ironsource'),
			(u'advertising_network', u'adcolony'),
		]
		Entity.ontology = nx.DiGraph()
		Entity.ontology.add_edges_from(edges)
		Entity.root = u'anyone'

	@staticmethod
	def isOntologyLoaded():
		return hasattr(Entity, 'ontology')

	def getDirectAncestors(self):
		if Entity.isOntologyLoaded():
			return [ Entity(r) for r in ontutils.getDirectAncestors(Entity.ontology, self.entity) ]
		return NotImplemented

	def isRoot(self):
		return self.entity == Entity.root

	def isEquiv(self, other):
		if isinstance(other, Entity) and Entity.isOntologyLoaded():
			return ontutils.isSemanticallyEquiv(Entity.ontology, self.entity, other.entity)
		return NotImplemented		

	def isApprox(self, other):
		if isinstance(other, Entity) and Entity.isOntologyLoaded():
			return ontutils.isSemanticallyApprox(Entity.ontology, self.entity, other.entity, Entity.root)
		return NotImplemented		

	# TODO we can do synonyms here...
	def __hash__(self):
		return hash(self.entity)

	def __eq__(self, other):
		if isinstance(other, Entity):
			return other.entity == self.entity
		return NotImplemented

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result

	def __lt__(self, other):#subsumes
		if isinstance(other, Entity) and Entity.isOntologyLoaded():
			return ontutils.isSubsumedUnder(Entity.ontology, self.entity, other.entity)
		return NotImplemented

	def __le__(self, other):#subsumes
		if isinstance(other, Entity) and  Entity.isOntologyLoaded():
			return ontutils.isSubsumedUnderOrEq(Entity.ontology, self.entity, other.entity)
		return NotImplemented


	def __gt__(self, other):
		if isinstance(other, Entity) and Entity.isOntologyLoaded():
			return ontutils.isSubsumedUnder(Entity.ontology, other.entity, self.entity)
		return NotImplemented


	def __ge__(self, other):
		if isinstance(other, Entity) and  Entity.isOntologyLoaded():
			return ontutils.isSubsumedUnderOrEq(Entity.ontology, other.entity, self.entity)
		return NotImplemented

	def __str__(self):
		return self.entity

class Action:
	def __init__(self, action):
		self.action = action
		self.positiveTerm = u'collect'
		self.negativeTerm = u'not_collect'
		self.domain = [self.positiveTerm, self.negativeTerm]

	def isPositiveSentiment(self):
		if self.action not in self.domain:
			raise ValueError('Action ({}) was not in domain {}'.format(self.action, self.domain))
		return True if self.action == self.positiveTerm else False

	def isNegativeSentiment(self):
		if self.action not in self.domain:
			raise ValueError('Action ({}) was not in domain {}'.format(self.action, self.domain))
		return True if self.action == self.negativeTerm else False

	def __hash__(self):
		return hash(self.action)

	def __eq__(self, other):
		if isinstance(other, Action):
			return (self.isPositiveSentiment() and other.isPositiveSentiment()) or (self.isNegativeSentiment() and other.isNegativeSentiment())
		return NotImplemented

	def __lt__(self, other):#subsumes
		return NotImplemented

	def __le__(self, other):#subsumes
		return NotImplemented

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result

	def __gt__(self, other):
		return NotImplemented

	def __ge__(self, other):
		return NotImplemented

	def __str__(self):
		return self.action

class DataObject:
	def __init__(self, data):
		self.data = data
	
	@staticmethod
	def loadOntology(filename, ontology=None, rootNode=u'information'):
		DataObject.ontology = ontutils.loadDataOntology(filename) if ontology is None else ontology
		DataObject.root = rootNode

	@staticmethod
	def loadStaticOntology():
		edges = [
			(u'information', u'pii'),
			(u'pii', u'email address'),#pii
			(u'pii', u'person name'),#pii
			(u'pii', u'phone number'),#pii
			(u'pii', u'device information'),#pii
			(u'information', u'non-pii'),
			(u'non-pii', u'geographical location'),
			(u'non-pii', u'geographical location'),
			(u'non-pii', u'device information'),#pii
			(u'device information', u'identifier'),#pii
			(u'identifier', u'device identifier'),#pii
			(u'identifier', u'mac address'),#pii
			(u'device information', u'router name'),#
			(u'device identifier', u'advertising identifier'),#pii
			(u'device identifier', u'android identifier'),#pii
			(u'device identifier', u'imei'),#pii
			(u'device identifier', u'gsfid'),#pii
		]
		DataObject.ontology = nx.DiGraph()
		DataObject.ontology.add_edges_from(edges)
		DataObject.root = u'information'

	@staticmethod
	def isOntologyLoaded():
		return hasattr(DataObject, 'ontology')

	def getDirectAncestors(self):
		if DataObject.isOntologyLoaded():
			return [ DataObject(r) for r in ontutils.getDirectAncestors(DataObject.ontology, self.data) ]
		return NotImplemented

	def isRoot(self):
		return self.data == DataObject.root

	def isEquiv(self, other):
		if isinstance(other, DataObject) and DataObject.isOntologyLoaded():
			return ontutils.isSemanticallyEquiv(DataObject.ontology, self.data, other.data)
		return NotImplemented		

	def isApprox(self, other):
		if isinstance(other, DataObject) and DataObject.isOntologyLoaded():
			return ontutils.isSemanticallyApprox(DataObject.ontology, self.data, other.data, DataObject.root)
		return NotImplemented

	# TODO we can do synonyms here...
	def __hash__(self):
		return hash(self.data)

	def __eq__(self, other):
		if isinstance(other, DataObject):
			return other.data == self.data
		return NotImplemented

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result

	def __lt__(self, other):#subsumes
		if isinstance(other, DataObject) and DataObject.isOntologyLoaded():
			return ontutils.isSubsumedUnder(DataObject.ontology, self.data, other.data)
		return NotImplemented

	def __le__(self, other):#subsumes
		if isinstance(other, DataObject) and  DataObject.isOntologyLoaded():
			return ontutils.isSubsumedUnderOrEq(DataObject.ontology, self.data, other.data)
		return NotImplemented


	def __gt__(self, other):
		if isinstance(other, DataObject) and DataObject.isOntologyLoaded():
			return ontutils.isSubsumedUnder(DataObject.ontology, other.data, self.data)
		return NotImplemented

	def __ge__(self, other):
		if isinstance(other, DataObject) and  DataObject.isOntologyLoaded():
			return ontutils.isSubsumedUnderOrEq(DataObject.ontology, other.data, self.data)
		return NotImplemented

	def __str__(self):
		return self.data


class DataFlow:
	def __init__(self, flow):
		self.entity = Entity(flow[0])
		self.data = DataObject(flow[1])

	def getTuple(self):
		return (self.entity.entity, self.data.data)

	def __eq__(self, other):
		if isinstance(other, DataFlow):
			return other.data == self.data and other.entity == self.entity
		return NotImplemented

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result

	def __lt__(self, other):
		return NotImplemented

	def __le__(self, other):
		return NotImplemented

	def __gt__(self, other):
		return NotImplemented

	def __ge__(self, other):
		return NotImplemented

	def __str__(self):
		return u'({}, {})'.format(self.entity, self.data)


class PolicyStatement:
	def __init__(self, policyStatement):
		self.entity = Entity(policyStatement[0])
		self.action = Action(policyStatement[1])
		self.data = DataObject(policyStatement[2])
	
	def getTuple(self):
		return (self.entity.entity, self.action.action, self.data.data)

	def isDiscussingRootTerms(self):
		return self.data.isRoot() or self.entity.isRoot()

	def isDiscussingAllRootTerms(self):
		return self.data.isRoot() and self.entity.isRoot()

	def isEquiv(self, other):
		if isinstance(other, DataObject):
			return self.data.isEquiv(other)
		elif isinstance(other, Entity):
			return self.entity.isEquiv(other)
		elif isinstance(other, PolicyStatement) or isinstance(other, DataFlow):
			return self.data.isEquiv(other.data) and self.entity.isEquiv(other.entity)	
		return NotImplemented

	def isApprox(self, other):
		if isinstance(other, DataObject):
			return self.data.isApprox(other)
		elif isinstance(other, Entity):
			return self.entity.isApprox(other)
		elif isinstance(other, PolicyStatement) or isinstance(other, DataFlow):
			return self.data.isApprox(other.data) and self.entity.isApprox(other.entity)	
		return NotImplemented

	def __eq__(self, other):
		if isinstance(other, PolicyStatement):
			return other.data == self.data and other.entity == self.entity and other.action == self.action
		return NotImplemented

	def __ne__(self, other):
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result

	def __lt__(self, other):
		return NotImplemented

	def __le__(self, other):
		return NotImplemented

	def __gt__(self, other):
		return NotImplemented

	def __ge__(self, other):
		return NotImplemented

	def __str__(self):
		return u'({}, {}, {})'.format(self.entity, self.action, self.data)	


class Consistency:
	@staticmethod
	def flowSubsumedUnderPolicy(flow, pol):
		return flow.data <= pol.data and flow.entity <= pol.entity

	@staticmethod
	def checkPermissive(policyStatements, flow):
		for pol in policyStatements:
			if Consistency.flowSubsumedUnderPolicy(flow, pol) and pol.action.isPositiveSentiment() and not pol.isDiscussingRootTerms():
				return (True, pol, None)
		return (False, None, None)


	@staticmethod
	def checkStrict(policyStatements, flow):
		def getNegativeContradiction(pol, flow, policyStatements):
			for cpol in policyStatements:
				if Consistency.flowSubsumedUnderPolicy(flow, cpol) and cpol.action.isNegativeSentiment() and not cpol.isDiscussingRootTerms():
					return (True, cpol)
			return (False, None)

		def hasPositiveSentimentStatement(P):
			return len([ p for p in P if p.action.isPositiveSentiment()]) > 0

		def hasNegativeSentimentStatement(P):
			return len([ p for p in P if p.action.isNegativeSentiment()]) > 0


		#Get all relevant policy statements		
		relP = [ p for p in policyStatements if Consistency.flowSubsumedUnderPolicy(flow, p) ] #and not pol.isDiscussingRootTerms()

		if len(relP) == 0: # No justification
			return (False, None, None)

		# Exists a positive sentiment statement, does not exist a negative sentiment
		consistencyResult = hasPositiveSentimentStatement(relP) and not hasNegativeSentimentStatement(relP)

		if consistencyResult:
			return (consistencyResult, relP, None)

		contradictions = []
		for p1 in relP:
			contrResults = []
			#Ensure p1 is positive sentiment or we'll potentially double count...
			if p1.action.isPositiveSentiment():
				for p2 in relP:
					if not p2.action.isNegativeSentiment():
						continue
					for cindex,conmethod in enumerate(contradictionMethods):
						if conmethod(p1, p2):# If contradiction between policies...
							contrResults.append((p2, cindex))
			contradictions.append(contrResults if len(contrResults) > 0 else None)
		return (consistencyResult, relP, contradictions)

	@staticmethod
	def getDirectAncestors(cobj):
		result = set()
		for o in cobj:
			for k in o.getDirectAncestors():
				result.add(k)
		return result


	@staticmethod
	def findContradictionsForStatements(policyStatements, pMatches):
		if pMatches is None or len(pMatches) == 0:
			return (False, False, None, None)

		resultDecision = False
		hasNegativeSent = False
		cpols = []
		for p in pMatches:
			if p.action.isNegativeSentiment():
				hasNegativeSent = True
			if p.action.isPositiveSentiment():
				resultDecision = True

			contrResults = []
			for p1 in policyStatements:
				for cindex,conmethod in enumerate(contradictionMethods):
					if conmethod(p, p1):# If contradiction between policies...
						# Check number of flows that would have been accepted if we ignored contradiction...
						contrResults.append(p1)
			cpols.append(contrResults)
		return (False if hasNegativeSent else resultDecision, hasNegativeSent, pMatches, cpols)

	@staticmethod
	def checkNearestEntityMatch(policyStatements, flow):
		def findNearestMatch(policyStatements, flow):
			def findDataMatch(policyStatements, data, entity):
				while len(data) > 0:
					pMatches = [ p for p in policyStatements if p.data in data and p.entity in entity ]
					if len(pMatches) > 0:
						return pMatches
					data = Consistency.getDirectAncestors(data)
				return None

			#########################
			# Get "nearest" match
			data = set([flow.data])
			entity = set([flow.entity])
			while len(entity) > 0:
				pMatches = findDataMatch(policyStatements, data, entity)
				if pMatches is None:
					entity = Consistency.getDirectAncestors(entity)
					continue
				return pMatches
			return None
		#########################
		pMatches = findNearestMatch(policyStatements, flow)
		return Consistency.findContradictionsForStatements(policyStatements, pMatches)

	@staticmethod
	def checkNearestDataMatch(policyStatements, flow):
		def findNearestMatch(policyStatements, flow):
			def findEntityMatch(policyStatements, data, entity):
				while len(entity) > 0:
					pMatches = [ p for p in policyStatements if p.data in data and p.entity in entity ]
					if len(pMatches) > 0:
						return pMatches
					entity = Consistency.getDirectAncestors(entity)
				return None
			#########################
			# Get "nearest" match
			data = set([flow.data])
			entity = set([flow.entity])
			while len(data) > 0:
				pMatches = findEntityMatch(policyStatements, data, entity)
				if pMatches is None:
					data = Consistency.getDirectAncestors(data)
					continue
				return pMatches
			return None
		#########################
		pMatches = findNearestMatch(policyStatements, flow)
		return Consistency.findContradictionsForStatements(policyStatements, pMatches)


	@staticmethod
	def checkIntermediate(policyStatements, flow):
		def isContradicted(pol, cpol):
			return Contradictions.checkContradiction1(pol, cpol) or Contradictions.checkContradiction3(pol, cpol) or \
				Contradictions.checkContradiction4(pol, cpol) or Contradictions.checkContradiction7(pol, cpol) or \
				Contradictions.checkContradiction8(pol, cpol) or Contradictions.checkContradiction9(pol, cpol) or \
				Contradictions.checkContradiction11(pol, cpol) or Contradictions.checkContradiction12(pol, cpol) or \
				Contradictions.checkContradiction13(pol, cpol) or Contradictions.checkContradiction15(pol, cpol) or \
				Contradictions.checkContradiction16(pol, cpol)

		def getNegativeContradiction(pol, policyStatements):
			for cpol in policyStatements:
				if cpol.action.isNegativeSentiment() and Consistency.flowSubsumedUnderPolicy(flow, cpol) and not cpol.isDiscussingRootTerms() and isContradicted(pol, cpol):
					return (True, cpol)
			return (False, None)

		#################
		hitContr = False
		for pol in policyStatements:
			if Consistency.flowSubsumedUnderPolicy(flow, pol) and pol.action.isPositiveSentiment() and not pol.isDiscussingRootTerms():
				contradictionExists,cpol = getNegativeContradiction(pol, policyStatements)
				if contradictionExists: # TODO Do we really just return here? Is it exists or forall? IS there a difference
					hitContr = True
					#return (False, pol, cpol)
					continue
				return (True, pol, None)
		return (False, None, None)

class Contradictions:
	@staticmethod
	def checkContradiction1(p1, p2):
		return p1.data == p2.data and p1.entity == p2.entity and p1.action != p2.action

	@staticmethod
	def checkContradiction2(p1, p2):
		return p1.data < p2.data and p1.entity == p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction3(p1, p2):
		return p1.data > p2.data and p1.entity == p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction4(p1, p2):
		return p1.data.isApprox(p2.data) and p1.entity == p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction5(p1, p2):
		return p1.data == p2.data and p1.entity < p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction6(p1, p2):
		return p1.data < p2.data and p1.entity < p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction7(p1, p2):
		return p1.data > p2.data and p1.entity < p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction8(p1, p2):
		return p1.data.isApprox(p2.data) and p1.entity < p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction9(p1, p2):
		return p1.data == p2.data and p1.entity > p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction10(p1, p2):
		return p1.data < p2.data and p1.entity > p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction11(p1, p2):
		return p1.data > p2.data and p1.entity > p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()
	
	@staticmethod
	def checkContradiction12(p1, p2):
		return  p1.data.isApprox(p2.data) and p1.entity > p2.entity and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()	
	@staticmethod
	def checkContradiction13(p1, p2):
		return  p1.data == p2.data and p1.entity.isApprox(p2.entity) and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()

	@staticmethod
	def checkContradiction14(p1, p2):
		return  p1.data < p2.data and p1.entity.isApprox(p2.entity) and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()

	@staticmethod
	def checkContradiction15(p1, p2):
		return  p1.data > p2.data and p1.entity.isApprox(p2.entity) and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()

	@staticmethod
	def checkContradiction16(p1, p2):
		return  p1.data.isApprox(p2.data) and p1.entity.isApprox(p2.entity) and p1.action.isPositiveSentiment() and p2.action.isNegativeSentiment()


contradictionMethods = [
				Contradictions.checkContradiction1, Contradictions.checkContradiction2,
				Contradictions.checkContradiction3, Contradictions.checkContradiction4,
				Contradictions.checkContradiction5, Contradictions.checkContradiction6,
				Contradictions.checkContradiction7, Contradictions.checkContradiction8,
				Contradictions.checkContradiction9, Contradictions.checkContradiction10,
				Contradictions.checkContradiction11, Contradictions.checkContradiction12,
				Contradictions.checkContradiction13, Contradictions.checkContradiction14,
				Contradictions.checkContradiction15, Contradictions.checkContradiction16,
			]

def getRawContradictionStats(policies, flows):
	results = []
	for index0,p0 in enumerate(policies):
		if p0.isDiscussingRootTerms():
			continue
		for index1,p1 in enumerate(policies):
			if index0 == index1 or p1.isDiscussingRootTerms():
				continue
			for cindex,conmethod in enumerate(contradictionMethods):
				if conmethod(p0, p1):# If contradiction between policies...
					# Check number of flows that would have been accepted if we ignored contradiction...
					conImpact = [ f for f in flows if Consistency.flowSubsumedUnderPolicy(f, p0) and Consistency.flowSubsumedUnderPolicy(f, p1) ]
					results.append(((p0, p1), cindex, conImpact))
	return results

def checkConsistency(policies, flows):
	return [ { 'flow' : f, 'consistency' : Consistency.checkStrict(policies, f) } for f in flows ]

#def checkConsistency(policies, flows, packageName, calcRawStats=False):
#	results = []
#	for f in flows:
		#TODO integrate raw stats calculation here...
#		pRes = Consistency.checkPermissive(policies, f)
#		iRes = Consistency.checkIntermediate(policies, f)
#		sRes = Consistency.checkStrict(policies, f)
#		results.append({'permissive' : pRes, 'intermediate' : iRes, 'strict' : sRes})
#	return (results, getRawContradictionStats(policies, flows)) if calcRawStats else results


def getContradictions(policies, packageName, calcRawStats=False):
	results = []
	for index0,p0 in enumerate(policies):
		if p0.isDiscussingRootTerms():
			continue
		for index1,p1 in enumerate(policies):
			if index0 == index1 or p1.isDiscussingRootTerms():
				continue
			for cindex,conmethod in enumerate(contradictionMethods):
				if conmethod(p0, p1):# If contradiction between policies...
					results.append(((p0, p1), cindex))
	return results

def init(dataOntologyFilename=u'data_ontology3.pickle', entityOntologyFilename=u'entity_ontology_graph.pickle'):
	Entity.loadOntology(entityOntologyFilename)
	DataObject.loadOntology(dataOntologyFilename)

def init_static():
	Entity.loadStaticOntology()
	DataObject.loadStaticOntology()

########################################################
def createDummyEntityOntology():
	edges = [
				(u'public', u'first party'),
				(u'public', u'third party'),
				(u'third party', u'third party provider'),
				(u'third party provider', u'advertiser'),
				(u'third party provider', u'analytic provider'),
				(u'advertiser', u'companyX'),
				(u'advertiser', u'google admob'),
				(u'analytic provider', u'companyX'),
				(u'analytic provider', u'google analytics'),
			]
	ontology = nx.DiGraph()
	ontology.add_edges_from(edges)
	return ontology

def createDummyDataOntology():
	edges = [
				(u'information', u'personal information'),
				(u'personal information', u'account credential'),
				(u'personal information', u'medical treatment information'),
				(u'account credential', u'biometric information'),
				(u'biometric information', u'fingerprint'),
				(u'biometric information', u'heart rate'),
				(u'account credential', u'username'),
				(u'medical treatment information', u'medical_health information'),
				(u'medical_health information', u'blood glucose'),
				(u'medical_health information', u'heart rate'),
			]
	ontology = nx.DiGraph()
	ontology.add_edges_from(edges)
	return ontology

def runTestCases():#FIXME test cases are broken since returning contradicting policies!
	def testContradictions(pol, flow, expContradictions, expIntermediate, expPermissive, expStrict=None):
		assert(len(contradictionMethods) == len(expContradictions))
		assert(len(pol) == 2)

		for index,conmethod in enumerate(contradictionMethods):
			assert(conmethod(pol[0], pol[1]) == expContradictions[index]), 'Contradiction failed for case {} and policies ({}, {})'.format(index, pol[0], pol[1])


		message = 'Failed {} check for ({}, {}) and flow ({}). Expected = {}, Result = {}'
		pRes = Consistency.checkPermissive(pol, flow)
		assert(pRes == expPermissive), message.format('permissive', pol[0], pol[1], flow, expPermissive, pRes)
		iRes = Consistency.checkIntermediate(pol, flow)
		assert(iRes == expIntermediate), message.format('intermediate', pol[0], pol[1], flow, expIntermediate, iRes)
		sRes = Consistency.checkStrict(pol, flow)
		assert(sRes == expStrict), message.format('strict', pol[0], pol[1], flow, expStrict, sRes)


	def createBoolArr(inverseValueIndex=None, defaultValue=False, length=16):
		arr = [ defaultValue ] * length
		if inverseValueIndex is not None:
			arr[inverseValueIndex] = not arr[inverseValueIndex]
		return arr

	Entity.loadOntology(ontology=createDummyEntityOntology())
	DataObject.loadOntology(ontology=createDummyDataOntology())

	flow1 = DataFlow((u'companyX', u'heart rate'))
	flow2 = DataFlow((u'companyX', u'blood glucose'))

	p0 = [PolicyStatement((u'companyX', u'collect', u'heart rate')),
		PolicyStatement((u'companyX', u'not_collect', u'heart rate'))]
	p0ExpCon = createBoolArr(0)
	testContradictions(p0, flow1, p0ExpCon, None, p0[0], None)
	testContradictions(p0, flow2, p0ExpCon, None, None, None)

	p1 = [PolicyStatement((u'companyX', u'collect', u'heart rate')),
		PolicyStatement((u'companyX', u'not_collect', u'medical_health information'))]
	p1ExpCon = createBoolArr(1)

	testContradictions(p1, flow1, p1ExpCon, p1[0], p1[0], None)
	testContradictions(p1, flow2, p1ExpCon, None, None, None)

	p2 = [PolicyStatement((u'companyX', u'collect', u'medical_health information')),
		PolicyStatement((u'companyX', u'not_collect', u'heart rate'))]
	p2ExpCon = createBoolArr(2)
	testContradictions(p2, flow1, p2ExpCon, None, p2[0], None)
	testContradictions(p2, flow2, p2ExpCon, p2[0], p2[0], p2[0])

	p3 = [PolicyStatement((u'companyX', u'collect', u'medical_health information')),
		PolicyStatement((u'companyX', u'not_collect', u'biometric information'))]
	p3ExpCon = createBoolArr(3)
	testContradictions(p3, flow1, p3ExpCon, None, p3[0], None)
	testContradictions(p3, flow2, p3ExpCon, p3[0], p3[0], p3[0])

	p4 = [PolicyStatement((u'companyX', u'collect', u'heart rate')),
		PolicyStatement((u'advertiser', u'not_collect', u'heart rate'))]
	p4ExpCon = createBoolArr(4)
	testContradictions(p4, flow1, p4ExpCon, p4[0], p4[0], None)
	testContradictions(p4, flow2, p4ExpCon, None, None, None)

	p5 = [PolicyStatement((u'companyX', u'collect', u'heart rate')),
		PolicyStatement((u'advertiser', u'not_collect', u'medical_health information'))]
	p5ExpCon = createBoolArr(5)
	testContradictions(p5, flow1, p5ExpCon, p5[0], p5[0], None)
	testContradictions(p5, flow2, p5ExpCon, None, None, None)

	p6 = [PolicyStatement((u'companyX', u'collect', u'medical_health information')),
		PolicyStatement((u'advertiser', u'not_collect', u'heart rate'))]
	p6ExpCon = createBoolArr(6)
	testContradictions(p6, flow1, p6ExpCon, None, p6[0], None)
	testContradictions(p6, flow2, p6ExpCon, p6[0], p6[0], p6[0])

	p7 = [PolicyStatement((u'companyX', u'collect', u'medical_health information')),
		PolicyStatement((u'advertiser', u'not_collect', u'biometric information'))]
	p7ExpCon = createBoolArr(7)
	testContradictions(p7, flow1, p7ExpCon, None, p7[0], None)
	testContradictions(p7, flow2, p7ExpCon, p7[0], p7[0], p7[0])

	p8 = [PolicyStatement((u'advertiser', u'collect', u'heart rate')),
		PolicyStatement((u'companyX', u'not_collect', u'heart rate'))]
	p8ExpCon = createBoolArr(8)
	testContradictions(p8, flow1, p8ExpCon, None, p8[0], None)
	testContradictions(p8, flow2, p8ExpCon, None, None, None)

	p9 = [PolicyStatement((u'advertiser', u'collect', u'heart rate')),
		PolicyStatement((u'companyX', u'not_collect', u'medical_health information'))]
	p9ExpCon = createBoolArr(9)
	testContradictions(p9, flow1, p9ExpCon, p9[0], p9[0], None)
	testContradictions(p9, flow2, p9ExpCon, None, None, None)

	p10 = [PolicyStatement((u'advertiser', u'collect', u'medical_health information')),
		PolicyStatement((u'companyX', u'not_collect', u'heart rate'))]
	p10ExpCon = createBoolArr(10)
	testContradictions(p10, flow1, p10ExpCon, None, p10[0], None)
	testContradictions(p10, flow2, p10ExpCon, p10[0], p10[0], p10[0])

	p11 = [PolicyStatement((u'advertiser', u'collect', u'medical_health information')),
		PolicyStatement((u'companyX', u'not_collect', u'biometric information'))]
	p11ExpCon = createBoolArr(11)
	testContradictions(p11, flow1, p11ExpCon, None, p11[0], None)
	testContradictions(p11, flow2, p11ExpCon, p11[0], p11[0], p11[0])

	p12 = [PolicyStatement((u'analytic provider', u'collect', u'heart rate')),
		PolicyStatement((u'advertiser', u'not_collect', u'heart rate'))]
	p12ExpCon = createBoolArr(12)
	testContradictions(p12, flow1, p12ExpCon, None, p12[0], None)
	testContradictions(p12, flow2, p12ExpCon, None, None, None)

	p13 = [PolicyStatement((u'analytic provider', u'collect', u'heart rate')),
		PolicyStatement((u'advertiser', u'not_collect', u'medical_health information'))]
	p13ExpCon = createBoolArr(13)
	testContradictions(p13, flow1, p13ExpCon, p13[0], p13[0], None)
	testContradictions(p13, flow2, p13ExpCon, None, None, None)

	p14 = [PolicyStatement((u'analytic provider', u'collect', u'medical_health information')),
		PolicyStatement((u'advertiser', u'not_collect', u'heart rate'))]
	p14ExpCon = createBoolArr(14)
	testContradictions(p14, flow1, p14ExpCon, None, p14[0], None)
	testContradictions(p14, flow2, p14ExpCon, p14[0], p14[0], p14[0])

	p15 = [PolicyStatement((u'analytic provider', u'collect', u'medical_health information')),
		PolicyStatement((u'advertiser', u'not_collect', u'biometric information'))]
	p15ExpCon = createBoolArr(15)
	testContradictions(p15, flow1, p15ExpCon, None, p15[0], None)
	testContradictions(p15, flow2, p15ExpCon, p15[0], p15[0], p15[0])

	p17 = [PolicyStatement((u'companyX', u'collect', u'heart rate')),
		PolicyStatement((u'companyX', u'not_collect', u'blood glucose'))]
	p17ExpCon = createBoolArr()
	testContradictions(p17, flow1, p17ExpCon, p17[0], p17[0], p17[0])
	testContradictions(p17, flow2, p17ExpCon, None, None, None)

	p18 = [PolicyStatement((u'companyX', u'collect', u'information')),
		PolicyStatement((u'companyX', u'not_collect', u'personal information'))]
	p18ExpCon = createBoolArr(2)
	testContradictions(p18, flow1, p18ExpCon, None, None, None)
	testContradictions(p18, flow2, p18ExpCon, None, None, None)

	p19 = [PolicyStatement((u'companyX', u'collect', u'personal information')),
		PolicyStatement((u'companyX', u'not_collect', u'information'))]
	p19ExpCon = createBoolArr(1)
	testContradictions(p19, flow1, p19ExpCon, p19[0], p19[0], None)
	testContradictions(p19, flow2, p19ExpCon, p19[0], p19[0], None)

	p20 = [PolicyStatement((u'companyX', u'collect', u'personal information')),
		PolicyStatement((u'companyX', u'collect', u'medical_health information'))]
	p20ExpCon = createBoolArr()
	testContradictions(p20, flow1, p20ExpCon, p20[0], p20[0], p20[0])
	testContradictions(p20, flow2, p20ExpCon, p20[0], p20[0], p20[0])

	p21 = [PolicyStatement((u'companyX', u'not_collect', u'personal information')),
		PolicyStatement((u'companyX', u'not_collect', u'medical_health information'))]
	p21ExpCon = createBoolArr()
	testContradictions(p21, flow1, p21ExpCon, None, None, None)
	testContradictions(p21, flow2, p21ExpCon, None, None, None)

if __name__ == '__main__':
	runTestCases()
