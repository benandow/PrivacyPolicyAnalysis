#!/usr/bin/env python
from __future__ import unicode_literals
import spacy


def dumpParseTree(root, tabdepth='\t'):
	print tabdepth, root.text, root.pos_, root.dep_
	for c in root.children:
		dumpParseTree(c, tabdepth + '\t')

def getDepTreeRoot(sentence):
	return sentence.root

def getConjunctions(np):
	def getConjunctionNPInternal(np, conjs):
		if np is None:
			return

		for c in np.children:
			if c.dep == spacy.symbols.conj or c.dep == spacy.symbols.appos: # sometimes mislabeled as appositional modifier
				conjs.append(c)
				getConjunctionNPInternal(c, conjs)

	#########################
	conjs = []
	getConjunctionNPInternal(np, conjs)
	return conjs


def getTokenByDep(token, dependency):
	toks = [ t for t in token.children if t.dep == dependency ]
	return toks if len(toks) > 0 else None

def getSubjects(verb):
	def getSubjectsInternal(token):
		subj = getTokenByDep(token, spacy.symbols.nsubj)
		return subj if subj is not None else getTokenByDep(token, spacy.symbols.nsubjpass)

	#########################
	subj = getSubjectsInternal(verb)
	if subj is None:# and sverb.dep == spacy.symbols.conj:
		# If coordinating conjunction, get subject from above.. TODO should probably check if verb...
		subj = getSubjectsInternal(verb.head)
		if subj is None and verb.head != verb:
			return getSubjects(verb.head)
	return subj


def getDirectObjects(verb):
	# Get direct object...
	def getDObjectsInternal(self, token):
		dobjs = []
		for t in token.children:
			if t.dep == spacy.symbols.dobj:
				dobjs.append(t)
		return dobjs if len(dobjs) > 0 else None

	#########################
	dobj = getDObjectsInternal(verb)
	if dobj is None:
		# Recurse downward until we get the object...
		for v in getVerbs(verb):
			if v.dep == spacy.symbols.conj: # Get conjunction verbs...
				dobj = getDObjectsInternal(v)
				if dobj is not None:
					break
	# Get conjunctions of dobj
	if dobj is not None:
		conjs = []
		for d in dobj:
			getConjunctions(d, conjs)
		for c in conjs:			
			dobj.append(c)
	return dobj




def isVerb(token):
	return token.pos == spacy.symbols.VERB

def isVerbNegated(token):
	neg = getTokenByDep(token, spacy.symbols.neg) is not None
	# If verb conjunction, check for negation above in previous verb...
	# TODO should probably check for presence of conjunction...
	if not neg:
		tok = token
		while isVerb(tok.head) and tok.head != tok:
			neg = getTokenByDep(tok.head, spacy.symbols.neg) is not None
			if neg:
				break
			tok = tok.head
	return neg

def getVerbs(token):
	def getVerbsInternal(token, verbList):
		for t in token.children:
			if isVerb(t) and t.dep == spacy.symbols.conj:
				verbList.append(t)
				getVerbsInternal(t, verbList)

	#########################
	verbList = []
	getVerbsInternal(token, verbList)
	return verbList


