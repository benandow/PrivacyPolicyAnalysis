#!/usr/bin/env python
from __future__ import unicode_literals
import spacy
from spacy.matcher import Matcher
import re


def isNoun(token):
	return token.pos in [spacy.symbols.NOUN, spacy.symbols.PROPN, spacy.symbols.PRON]

# mergeNounPhrasesDoc should be called before this...
def getNounPhrases(sentence):
	return [tok for tok in sentence if isNoun(tok)]

def getLemma(nphrase):
	def getLemmaInt(tok):
		return tok.text.lower() if tok.lemma_ == u'-PRON-' else tok.lemma_

	##########################################
	def getLemmaSkipDetsAndPron(nphrase):
		return u' '.join([ getLemmaInt(w) for w in nphrase if w.pos != spacy.symbols.DET ])

	##########################################
	text = getLemmaInt(nphrase[0]) if len(nphrase) <= 1 else getLemmaSkipDetsAndPron(nphrase)
	text = re.sub(r'\s+-\s+', u'-', text)
	text = re.sub(u'\s+(\'|\u2019)s', u'\'s', text)
	return text

def most_common(lst):
    return max(set(lst), key=lst.count)

#FIXME definitely a better way to do this based on dep labels...
# E.g., information about a user <--- data
def getEntType(np):
	containOrgOrPers = False
	ents = []
	for tok in np:
		if tok.ent_type_ in [u'ORG', u'PERSON']:
			containOrgOrPers = True
		if tok.ent_type_ == u'DATA':
			return u'DATA'
		if tok.ent_type_ is not None and len(tok.ent_type_) > 0:
			ents.append(tok.ent_type_)
	if containOrgOrPers:
		return u'ORG'
	return most_common(ents) if len(ents) > 0 else u''

def mergeNounPhrasesDoc(doc, vocab, skipHeadWords=False):
	def mergeNounPhrasesInternal(nphrases, fixDeps=False):
		for np in nphrases:
			# This messes up the hearst pattterns, so don't merge!!!
			if skipHeadWords and len(np) > 1 and np[0].lemma_ in [u'other', u'such', u'especially']: 
				np = doc[np[0].i + 1 : np[-1].i + 1]
			if fixDeps:
				np.merge(pos=spacy.symbols.NOUN, lemma=getLemma(np), dep=np[-1].dep, ent_type=getEntType(np))
			else:
				np.merge(pos=spacy.symbols.NOUN, lemma=getLemma(np), ent_type=getEntType(np))
				
	##########################################
	def extractNPsWithAdPositions(doc):
		def getPobj(token):
			pobjs = [ child for child in token.children if child.dep == spacy.symbols.pobj ]
			return pobjs[0] if len(pobjs) > 0 else None
		##########################################
		def getPobjsEndIndex(token, startIndex):
			if isNoun(token):
				for ctok in token.children:
					if ctok.dep == spacy.symbols.prep and ctok.lemma_ in [u'of', u'on', u'in', u'about', u'regard']:
						pobj = getPobj(ctok)
						if pobj is not None:
							# Ensure that no space...
							if ctok.i != token.i + 1 or pobj.i != ctok.i + 1: # Ensure consecutive for now...
								#print 'PROBLEM: ', doc[token.i : pobj.i + 1]
								pass
							else:
								#print 'PRINT: ', doc[token.i : pobj.i + 1], token.i, pobj.i, ctok.i
								return getPobjsEndIndex(pobj, pobj.i)
			return startIndex
		##########################################
		nphrases = []
		for sentence in doc.sents:
			index = 0
			while index < len(sentence):
				token = sentence[index]
				endIndex = getPobjsEndIndex(token, -1)
				if endIndex > 0:
					nphrases.append(doc[token.i : endIndex + 1])
					index = endIndex + 1 # Continue where we left off...
					continue

				index += 1
		return nphrases

	##########################################
	# spaCy messes up extracing noun phrases when "personally" appears at the
	# beginning of the sentence (e.g., "{Personally} {identifiable information} may
	# be shared")
	def fixSpacyNPhrase(doc, vocab):
		results = []
		##########################################
		def callback(matcher, doc, i, matches):
			for match_id, start, end in matches:
				span = doc[start:end]
				results.append(span)
		##########################################
		matcher = Matcher(vocab)
		matcher.add(1, callback,
			[	{spacy.attrs.LOWER: "personally"},
				{spacy.attrs.LOWER: "identifiable information"},
			])
		matcher.add(2,callback,
			[	{spacy.attrs.LOWER: "personally"},
				{spacy.attrs.LOWER: "identifiable data"},
			])
		matcher.add(3,callback,
			[	{spacy.attrs.LOWER: "mobile device"},
				{spacy.attrs.LOWER: "identifier"},
			])
		matcher.add(4,callback,
			[	{spacy.attrs.LOWER: "device"},
				{spacy.attrs.LOWER: "identifier"},
			])
		
		# X, credit or debit card information and other Y messes up, so let's make sure we merge these...
		# Disable this because it was caushing a crash to occur...
#		matcher.add(5,callback,
#			[	{spacy.attrs.LOWER: "credit"},
#				{spacy.attrs.POS: "CCONJ"},
#				{spacy.attrs.POS: "NOUN",  'OP': '+'}
#			])
#		matcher.add(6,callback,
#			[	{spacy.attrs.LOWER: "debit"},
#				{spacy.attrs.POS: "CCONJ"},
#				{spacy.attrs.POS: "NOUN",  'OP': '+'}
#			])

		matcher(doc)
		mergeNounPhrasesInternal(results, fixDeps=True) #Ensure dependency label is set as "identifiable information" and not "personally"...
	##########################################

	# Gets relative clauses for BROAD or non-specific information types (information that..., certain information, ...)
	def getRelativeClauses(doc):
		def getSubject(token):
			subjs = [ t for t in token.children if t.dep in [spacy.symbols.nsubj, spacy.symbols.nsubjpass] ]
			return subjs[0] if len(subjs) > 0 else None
		##########################################

		def getDirectObject(token):
			dobjs = [ t for t in token.children if t.dep == spacy.symbols.dobj ]
			return dobjs[0] if len(dobjs) > 0 else None
		##########################################

		def getRelclEndIndex(token, endIndex):
			if isNoun(token):
				for child in token.children:
					# Note spacy.symbols.relcl is not defined...
					if child.dep_ == u'relcl': #TODO check POS to ensure verb?
						subj = getSubject(child)
						if subj is not None and subj.lemma_ in [u'that', u'which']: #Do we ever really have multiple subjects?
							dobjs = getDirectObject(child)							
							if dobjs is not None:
								if subj.i != token.i + 1 and dobjs.i != subj.i + 1:
									#print 'PROBLEM3: ', doc[token.i : dobjs.i + 1]
									pass
								else:
									return getRelclEndIndex(dobjs, dobjs.i)
			return endIndex
		##########################################

		mergeList = []
		for sentence in doc.sents:
			for tok in sentence:
				endIndex = getRelclEndIndex(tok, -1)
				if endIndex > 0:
					if re.search(r'^((any|other|aggregate(d)?|various|the\s(type|kind)(s)?\sof|(small|large|wide|average)\s(amount|range)\sof|certain|specific)\s+)?(information|data|datum|anything)(\s+|$)', tok.lemma_):
						#print 'INCLUDE:', doc[tok.i : endIndex + 1]
						mergeList.append(doc[tok.i : endIndex + 1])
			#		elif re.search(r'(^|\s*)(information|datum|anything)(\s+|$)', tok.lemma_):
			#			print 'EXCLUDE:', doc[tok.i : endIndex + 1]
		return mergeList

	##########################################
	def spanContainsEgIe(span):
		for tok in span:
			if tok.text in [u'i.e.', u'e.g.']:
				return True
		return False

	##########################################

	# Merge entities...
	for e in doc.ents:
		#Let's make sure that it doesn't start with a verb...
		if e[0].pos == spacy.symbols.VERB:
			continue
		e.merge(lemma=getLemma(e))
	
	#spacy.tokens.Token.set_extension('is_country', default=False)
	# Merge first using spaCy's default
	nphrases = [ nchunk for nchunk in doc.noun_chunks if not spanContainsEgIe(nchunk) ]
	mergeNounPhrasesInternal(nphrases)

	# Fix problems with spaCy mistagging "personally" when it occurs at the beginning
	fixSpacyNPhrase(doc, vocab)

	# Now loop back through and merge using our extended approach!
	nphrases = extractNPsWithAdPositions(doc)
	mergeNounPhrasesInternal(nphrases)

	nphrases = getRelativeClauses(doc)
	mergeNounPhrasesInternal(nphrases)
