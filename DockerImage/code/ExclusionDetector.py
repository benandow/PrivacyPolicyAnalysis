#!/usr/bin/env python2
from __future__ import unicode_literals
import spacy

#TODO this needs to be refactored, this is a giant mess of ugly....

def getLemmas(tokens):
	def getLemma(term):
		if type(term) == list:
			return getLemmas(term)
		return term if type(term) == unicode else term.lemma_
	if type(tokens) != list:
		return getLemma(tokens)	
	return u' '.join([getLemma(t) for t in tokens])

def isPrepPhraseWord(token):
	return token.lemma_ in [u'except when', u'except where', u'unless when', u'unless where', u'except for', u'except in', u'except under', u'unless for', u'unless in', u'unless under', u'apart from', u'aside from', u'with the exception of', u'other than', u'except to', u'unless to', u'unless as', u'except as']

def isNotExclusionTerm(token):
	return not isPrepPhraseWord(token) and token.lemma_ not in [u'besides', u'beside', u'except', u'without', u'exclude', u'unless']

def isPreposition(token):
	return token.pos == spacy.symbols.ADP and token.dep in [spacy.symbols.prep, spacy.symbols.agent] 

def isAcl(token):
	return token.pos == spacy.symbols.VERB and (token.dep in [spacy.symbols.acl] or token.dep_ in [u'relcl']) 

def getConjuncts(token, skipFirstElement=False): # Spacy's token.conjuncts does not work correctly
	def getConjunctsInt(token, conjunctions, skipElement=False):
		if not skipElement:
			conjunctions.append(token)
		if token is None:
			return
		for t in token.children:
			if t.dep == spacy.symbols.conj:
				getConjunctsInt(t, conjunctions, skipElement=False)
	################
	conjunctions = []
	getConjunctsInt(token, conjunctions, skipElement=skipFirstElement)
	if token is not None and (token.head.dep == spacy.symbols.prep or isPrepPhraseWord(token.head)):
		getConjunctsInt(token.head, conjunctions, skipElement=skipFirstElement)
	return conjunctions

def getPobj(tok):
	for ctok in tok.children:
		if ctok.dep in [spacy.symbols.pobj, spacy.symbols.pcomp]:
			return ctok
	return None

def getPrep(token):
	for ctok in token.children:
		if ctok.lemma_ in [u':', u';']:
			break
		if isPreposition(ctok):
			pobj = getPobj(ctok)
			if pobj is None:
				return [[ctok]]
			return [[ctok, pobj]]
	return None

def getPhrase(token, conjunctFlag=True):
	def getNounPhraseInternal(token, result):
		if token is None:
			return
		for ctok in token.children:
			if isPreposition(ctok):
				pobj = getPobj(ctok)
				if pobj is not None:
					result.extend([ token, ctok ])#TODO is this right?
					getNounPhraseInternal(pobj, result)
				else:
					result.extend([token, ctok])
				return
			elif isAcl(ctok) and isNotExclusionTerm(ctok):
				#TODO handle xcomp
				result.append(token)
				getNounPhraseInternal(ctok, result)
				return
		result.append(token)
		return token
	result = []
	getNounPhraseInternal(token, result)
	
	if conjunctFlag:
		retVal = [result]
		if len(result) > 0:
			conjuncts = [ findNounOrVerbPhrase(c) for c in getConjuncts(result[-1], True) ]
			retVal = [result]
			if conjuncts is not None and len(conjuncts) > 0:
				for c in conjuncts:
					if c is not None:
						retVal.append(c)
		return retVal
	return result

def getSubjectObject(token):
	subj = None
	dobj = None
	if token.pos == spacy.symbols.VERB:
		attr = None
		for ctok in token.children:
			if ctok.dep in [spacy.symbols.nsubj, spacy.symbols.nsubjpass]:
				subj = getPhrase(ctok)
			elif ctok.dep == spacy.symbols.dobj:
				dobj = getPhrase(ctok)
			elif ctok.dep == spacy.symbols.attr:
				attr = getPhrase(ctok)
		if dobj is None:
			dobj = getPrep(token)
		if dobj is None and attr is not None:
			dobj = attr
	return (subj, dobj)

def addSubjectsAndDobjs(subjs, verb, dobjs, results):
	def isNotNoneOrEmpty(arr):
		return arr is not None and len(arr) > 0

	def addDobjs(subj, verb, dobjs, results):
		if isNotNoneOrEmpty(dobjs):
			for d in dobjs:
				if subj is None:
					results.append([verb, d])
				else:
					results.append([subj, verb, d])
		else:
			if subj is None:
				results.append([verb])
			else:
				results.append([subj, verb])

	if isNotNoneOrEmpty(subjs):
		for s in subjs:
			addDobjs(s, verb, dobjs, results)
	else:
		addDobjs(None, verb, dobjs, results)

def getSubjectHeuristic(token):
	subj,_ = getSubjectObject(token.head)
	if subj is None:
		chead = token.head
		while chead.dep == spacy.symbols.conj:
			chead = chead.head
			subj,_ = getSubjectObject(chead)
			if subj is not None or chead.head == chead:# Ensure not root...
				break
	return subj

def getDobjHeuristic(token):
	vphr = getConjuncts(token)
	dobj = None
	if len(vphr) > 1:
		for vp in vphr[1:]:
			_,dobj = getSubjectObject(vp)
			if dobj is not None:
				break
	return dobj

def getVerbPhrase(token):
	def getVerbPhraseInternal(token, results):
		if token.pos == spacy.symbols.VERB:
			nFlag = False
			skipCond = False
			for ctok in token.children:
				if ctok.dep == spacy.symbols.mark or (not nFlag and skipCond and ctok.dep != spacy.symbols.conj):
					continue
				if nFlag or ctok.pos in [spacy.symbols.ADP]:
					nFlag = False
					#results.append(token)
					results.extend(getPhrase(token))
				elif ctok.pos in [spacy.symbols.ADV]:
					results.append([token, ctok])
				elif ctok.dep in [spacy.symbols.xcomp]:
					results.extend([ctok])#TODO this needs to be more complicated...
				elif ctok.dep == spacy.symbols.conj:
					res = getVerbPhrase(ctok)
					if res is not None:
						#results.append(token)
						results.extend(res)
				elif not skipCond and ctok.dep in [ spacy.symbols.dobj, spacy.symbols.nsubj, spacy.symbols.nsubjpass ]:
					subj,dobj = getSubjectObject(token)
					if dobj is None:
						dobj = getDobjHeuristic(token)
					if subj is None:
						subj = getSubjectHeuristic(ctok)
					# Let's break apart the subject...
					addSubjectsAndDobjs(subj, token, dobj, results)
#					results.append([subj, token, dobj])
					skipCond = True
				elif ctok.lemma_ == u':':
					nFlag = True
	
	results = []
	getVerbPhraseInternal(token, results)
	if len(results) == 0 and token.pos == spacy.symbols.VERB:
		results.append([token])
	return results

def findNounOrVerbPhrase(token):
	pobj = getPobj(token)# Check if pobj...
	if pobj is not None:
		return getPhrase(pobj)

	hasChildren = False
	for tok in token.children:
		hasChildren=True
		if isPreposition(tok):
			pobj = getPobj(tok)
			return getPhrase(pobj)
		elif tok.dep == spacy.symbols.dobj:
			return getPhrase(tok)

	# If I'm a verb...
	if not hasChildren:
		if token.pos == spacy.symbols.VERB and token.dep == spacy.symbols.acl:
			if token.head.pos == spacy.symbols.NOUN:
				return getPhrase(token.head)

	# Try without head match
	verbPhrase = findVerbPhrase(token)
	if verbPhrase is not None:
		return verbPhrase

	verbPhrase = findVerbPhrase(token, enableHeadMatch=True)
	if verbPhrase is not None:
		return verbPhrase

	return [ token ]

def findVerbPhrase(token, traverseUpwardFlag=True, skipDirectMatch=False, enableHeadMatch=False):
	if not skipDirectMatch and token.pos == spacy.symbols.VERB: #We already have the verb
		return getVerbPhrase(token)
	numChildren = len([ctok for ctok in token.children])
	if traverseUpwardFlag and numChildren == 0 and token.head != token: # Ensure has children, not root...
		#Check the head...
		if enableHeadMatch and token.head.pos == spacy.symbols.VERB:
			return getVerbPhrase(token.head)
		# Try finding children after the token...
		foundCurrentToken = False
		for ctok in token.head.children:
			if not foundCurrentToken:
				if ctok == token:
					foundCurrentToken = True
				continue
			if ctok.pos == spacy.symbols.VERB:
				if ctok.dep == spacy.symbols.conj:# Get the head instead...
					return getVerbPhrase(token.head)
				return getVerbPhrase(ctok)
	else:
		for ctok in token.children: # Search children for the verb
			if ctok.pos == spacy.symbols.VERB:
				return getVerbPhrase(ctok)
	return None

def getRelevantVerb(token):
	thead = token.head
	while thead.pos != spacy.symbols.VERB or (thead.pos == spacy.symbols.VERB and thead.dep == spacy.symbols.advcl):
		thead = thead.head
		if thead.head == thead:
			break
	return thead


def flattenException(exceptions):
	def flatten(tokens, res):
		if type(tokens) != list:
			res.append(tokens)
			return
		for t in tokens:
			if type(t) == list:
				flatten(t, res)
			else:
				res.append(t)

	flattenedExcpts = []
	for verb,excpts in exceptions:
		if excpts is None:
			continue
		for e in excpts:
			res = []
			flatten(e, res)
			flattenedExcpts.append((verb, res))
	return flattenedExcpts

def mergeExceptions(exceptions):
	newExcepts = []
	for verb,excpts in exceptions:
		if excpts is None:
			continue
		for e in excpts:
			# Flatten the tokens...
			newExcepts.append((verb, getLemmas(e)))
	return newExcepts

def dumpExceptions(exceptions):
	print '------\nExceptions:'
	for e in exceptions:
		print e
	print '------'

def isNegated(token):
	return any(ctok.dep == spacy.symbols.neg for ctok in token.children)

def checkException(sentence):
	def dumpTree(tok, tab=u''):
		print tab, tok.lemma_, tok.pos_, tok.dep_, tok.i
		for child in tok.children:
			dumpTree(child, tab + u'\t')

	exceptions = []
#	dumpTree(sentence.root)
	for tok in sentence:
		# Get nearest verb in tree...
		if tok.lemma_ in [u'except when', u'except where', u'unless when', u'unless', u'unless as', u'except as', u'unless where']:
			res = findVerbPhrase(tok)
			if res is None:
				res = findVerbPhrase(tok, enableHeadMatch=True)
			exceptions.append((getRelevantVerb(tok), res))
		elif tok.lemma_ in [u'except for', u'exclude', u'except in', u'except under', u'unless for', u'unless in', u'unless under', u'apart from', u'aside from', u'with the exception of', u'besides', u'beside', u'other than', u'except', u'except to', u'unless to', u'without'] or (tok.lemma_ in [u'include'] and isNegated(tok)):
			exceptions.append((getRelevantVerb(tok), findNounOrVerbPhrase(tok)))

	exceptions = flattenException(exceptions)
#	print exceptions
	#exceptions = mergeExceptions(exceptions)
	#dumpExceptions(exceptions)
	return exceptions


