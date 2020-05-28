#!/usr/bin/env python
from __future__ import unicode_literals
import networkx as nx
import dill as pickle

def loadOntology(filename):
	return pickle.load(open(filename, 'rb'))

def loadEntityOntology(filename):
	return loadOntology(filename)

def loadDataOntology(filename):
	return loadOntology(filename)

def loadOntologyTerms(filename):
	terms = set()
	tdict = loadOntology(filename)
	for t in tdict:
		terms.add(t)
		for s in tdict[t]:
			terms.add(s)
	return terms

def getAllDescendents(ontology, node):#TODO check if node in ontology...
	if node not in ontology.nodes:
		raise ValueError('Node {} is not in the ontology'.format(node))
	return [ n for n in ontology.nodes if n == node or nx.has_path(ontology, node, n) ] 

def getDirectAncestors(ontology, node):
	return [ src for src,_ in ontology.in_edges(node) ]

def isSubsumedInternal(ontology, x, y):
	return x in getAllDescendents(ontology, y)

# X is subsumed under Y
def isSubsumedUnder(ontology, x, y):
	return x != y and isSubsumedInternal(ontology, x, y)

# X is subsumed under Y or equal
def isSubsumedUnderOrEq(ontology, x, y):
	return x == y or isSubsumedInternal(ontology, x, y)

def isSemanticallyEquiv(ontology, x, y):
	return isSubsumedUnderOrEq(ontology, x, y) or isSubsumedUnderOrEq(ontology, y, x)

def isSemanticallyApprox(ontology, x, y, root):
	if isSemanticallyEquiv(ontology, x, y):
		return False

	xDescend = getAllDescendents(ontology, x)
	if root in xDescend:
		xDescend.remove(root)
	yDescend = getAllDescendents(ontology, y)
	if root in yDescend:
		yDescend.remove(root)
	
	return not isSemanticallyEquiv(ontology, x, y) and len(set(xDescend).intersection(set(yDescend))) > 0
