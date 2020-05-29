#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from lxml import etree
import re

def loadAnnotations(filename='/ext/data/synonyms.xml'):
	def getTerm(node):
		return node.get(u'term')

	def loadAnnotInternal(node, ignoreList, synAnnot):
		if node.tag == u'node':
			term = getTerm(node)
			if term not in synAnnot:
				synAnnot[term] = term
			for child in node:
				if child.tag == u'synonym':
					childTerm = getTerm(child)
					if childTerm not in synAnnot:
						synAnnot[childTerm] = term
				elif child.tag in [u'node', u'ignore']:
					loadAnnotInternal(child, ignoreList, synAnnot)
		elif node.tag == u'ignore':
			term = getTerm(node)
			ignoreList.append(term)
		elif node.tag == u'annotations':
			for child in node:
				loadAnnotInternal(child, ignoreList, synAnnot)

	ignoreList = []
	synonyms = {}
	tree = etree.parse(filename)
	root = tree.getroot()
	loadAnnotInternal(root, ignoreList, synonyms)
	return synonyms


synonymDict = loadAnnotations() # TODO make a class so we don't load it EVERY time	

def getSynonym(term):
	if term in synonymDict:
		return synonymDict[term]
	# Strip apostrophe and quotes
	t = re.sub(r'("|\'(\s*s)?)', u'', term)
	if t in synonymDict:
		return synonymDict[t]
	return term

#####
def isSafeSubstitution(term): #Don't sub if there's a chance there are multiple terms in a noun phrase
	return False if re.search(r'\b(and|or)\b', term) or re.search(r'(,|;)', term) else True

def isSimpleUsageInfoTerm(term):
	if not isSafeSubstitution(term):
		return False
	return True if re.search(r'^(information|data|datum|record|detail)\s+(about|regard|of|relate\sto)(\s+how)?\s+(you(r)?\s+)?(usage|use|uses|utilzation|activity)\s+(of|on|our)\s+.*$', term) else False

def isSimpleNonPersonalInfoTerm(term):
	if not isSafeSubstitution(term):
		return False
	if re.search(r'^(non-(pii|personally(\-|\s)identif(y|iable)\s(information|data|datum|detail)))$', term):
		return True
	return True if re.search(r'\b((information|data|datum|detail)\s.*\snot\sidentify\s(you|user|person|individual))\b', term) else False

def isSimplePersonallyIdentifiableInfoTerm(term):
	if not isSafeSubstitution(term):
		return False
#	if re.search(r'^((information|data|datum|detail)\sabout\syou)$', term):
#		return True
	if re.search(r'^(pii|personally(\-|\s)identif(y|iable)\s(information|data|datum|detail))$', term):
		return True
	return True if re.search(r'\b((information|data|datum|detail)\s.*\sidentify\s(you(rself)?|user|person|individual))\b', term) else False

def isSimpleIpAddr(term):
	if not isSafeSubstitution(term):
		return False
	return True if re.search(r'\b((ip|internet(\sprotocol)?)\saddress(es)?)\b', term) else False

def simpleSynonymSub(term):
	if not isSafeSubstitution(term):
		return term

	if isSimpleNonPersonalInfoTerm(term):
		term = u'non-personally identifiable information'
#		term = u'non-personally identifiable information'
	elif isSimplePersonallyIdentifiableInfoTerm(term):
		term = u'personally identifiable information'
#		term = u'personally identifiable information'
	elif isSimpleIpAddr(term):
		term = u'ip address'
	elif isSimpleUsageInfoTerm(term):
		term = u'usage information'
	return term

#####

def fixWhitespace(text):
	text = re.sub(r'^\s+', u'', text)
	text = re.sub(r'\s+$', u'', text)
	return re.sub(r'\s+', u' ', text)

def cleanupUnicodeErrors(term):
	# Cleanup from mistakes before... this should really be fixed during the intial parsing of the document...
	t = re.sub(u'\ufffc', u' ', term)
	t = re.sub(u'â€œ', u'', t)
	t = re.sub(u'â€\u009d', u'', t)
	t = re.sub(u'â\u0080\u0094', u'', t)
	t = re.sub(u'â\u0080\u009d', u'', t)
	t = re.sub(u'â\u0080\u009c', u'', t)
	t = re.sub(u'â\u0080\u0099', u'', t)
	t = re.sub(u'â€', u'', t)
	t = re.sub(u'äë', u'', t)
	t = re.sub(u'ä', u'', t)
	t = re.sub(u'\u0093', u'', t)
	t = re.sub(u'\u0092', u'', t)
	t = re.sub(u'\u0094', u'', t)
	t = re.sub(u'\u00a7', u'', t)#Section symbol
	t = re.sub(u'\u25cf', u'', t)#bullet point symbol
	t = re.sub(u'´', u'\'', t)
	t = re.sub(u'\u00ac', u'', t)
	t = re.sub(u'\u00ad', u'-', t)
	t = re.sub(u'\u2211', u'', t)
	t = re.sub(u'\ufb01', u'fi', t)
	t = re.sub(u'\uff0c', u', ', t)
	t = re.sub(u'\uf0b7', u'', t)
	t = re.sub(u'\u037e', u';', t)
	return t


def commonTermSubstitutions(term):
	# third-party --> third party
	term = re.sub(r'\b(third\-party)\b', u'third party', term)
	term = re.sub(r'\b(app(s)?|applications)\b', u'application', term)
	term = re.sub(r'\b(wi\-fi)\b', u'wifi', term)
	term = re.sub(r'\b(e\-\s*mail)\b', u'email', term)
	return fixWhitespace(term)

def stripIrrelevantTerms(term):
	pronRegex = re.compile(r'^(your|our|their|its|his|her|his(/|\s(or|and)\s)her)\b')
	irrevRegex = re.compile(r'^(additional|also|available|when\snecessary|obviously|technically|typically|basic|especially|collectively|certain|general(ly)?|follow(ing)?|important|limit(ed)?(\s(set|amount)\sof)?|more|most|necessary|only|optional|other|particular(ly)?|perhaps|possibl(e|y)|potential(ly)?|relate(d)?|relevant|require(d)?|select|similar|some(times)?|specific|variety\sof|various(\s(type|kind)(s)\sof)?)\b(\s*,\s*)?')
	while pronRegex.search(term) or irrevRegex.search(term):
		term = fixWhitespace(pronRegex.sub(u'', term))
		term = fixWhitespace(irrevRegex.sub(u'', term))
	return fixWhitespace(term)

def stripEtc(term):
	term = re.sub(r'\b(etc)(\.)?$', u'', term)
	return fixWhitespace(term)

def subInformation(text):
	text = re.sub(r'\b(info|datum|data)\b', u'information', text)
	#this can happen when subbing data for information
	return fixWhitespace(re.sub(r'\b(information(\s+information)+)\b', u'information', text))


def isFirstParty(package_name, dest_domain, privacy_policy):
	# Get start of packagename com.benandow.policylint --> com.benandow
	splitPackageName = package_name.split(u'.')
	rPackageName = u'{}.{}'.format(splitPackageName[0], splitPackageName[1])

	# Get root destination domain (reversed) (e.g., policylint.benandow.com --> com.benandow)
	splitDestDom = dest_domain.split(u'.')
	if len(splitDestDom) < 2:
		return False
	rDestDomRev = u'{}.{}'.format(splitDestDom[-1], splitDestDom[-2])
	
	# Check if root dest_domain (reversed) matches start of package_name
	if rPackageName == rDestDomRev:
		return True
	
	if privacy_policy is not None and type(privacy_policy) == str:
		privacy_policy = privacy_policy.decode("utf-8")

	# Check if root privacy_policy url (reversed) matches start of package name
	if privacy_policy != u'NULL' and len(privacy_policy) > 0:
		#Reverse root policy URL: https://www.benandow.com/privacy --> com.benandow
		splitDom = re.sub(r'/.*$', '', re.sub(r'http(s)?://', u'', privacy_policy)).split(u'.')
		rPolUrlRev = u'{}.{}'.format(splitDom[-1], splitDom[-2])
		# Check if the root privacy policy url matches the destination domain..
		if rPolUrlRev == rDestDomRev:
			return True
	return False

def resolveUrl(url, packageName, policyUrl):
	if isFirstParty(packageName, url, policyUrl):
		return u'we'

	if url in synonymDict:
		return synonymDict[url]
	return None

def preprocess(term):
	def subOrdinals(term):
		term = re.sub(r'\b(1st)\b', u'first', term)
		term = re.sub(r'\b(3rd)\b', u'third', term)
		return fixWhitespace(term)
    
	def stripQuotes(term):
		return fixWhitespace(re.sub(r'"', u'', term))

	def stripBeginOrEndPunct(term):
		punctRegex = re.compile(r'((^\s*(;|,|_|\'|\.|:|\-|\[|/)\s*)|((;|,|_|\.|:|\-|\[|/)\s*$))')
		andOrRegex = re.compile(r'^(and|or)\b')
		while punctRegex.search(term) or andOrRegex.search(term):
			term = fixWhitespace(punctRegex.sub(u'', term))
			term = fixWhitespace(andOrRegex.sub(u'', term))
		return term
    
	##############

	origTerm = term#REMOVEME
	term = cleanupUnicodeErrors(term)
	# Strip unbalanced parentheses
	if not re.search(r'\)', term):
		term = re.sub(r'\(', u'', term)
	if not re.search(r'\(', term):
		term = re.sub(r'\)', u'', term)

	term = stripBeginOrEndPunct(term)
	term = stripEtc(term)
	term = stripBeginOrEndPunct(term)#Do this twice since stripping etc may result in ending with punctuation...
	term = subOrdinals(term)
	term = stripQuotes(term)
	term = commonTermSubstitutions(term)
	term = stripIrrelevantTerms(term)

	term = fixWhitespace(term)
	term = simpleSynonymSub(term)
	term = subInformation(term)

	term = getSynonym(term)

	return term

def startsWithLetter(term):
	return True if re.search(r'^[a-z]', term) else False

def ignorePhrases(term):
	if re.search(r'\b(act(s)?|advantage|allegation|aspect|because|breach|change|condition(s)?|conduct|confidentiality|copyright|damage|destruction|disclosure|disposition|effectiveness|encryption|enforce(ment|ability)|example|exploitation|failure|freedom|functionality|handling|harm|illegal\sconduct|impact|impossibility|improvement|integrity|lack|law|(legal|sole)\sresponsibility|liability|limitation|loss|malfunction|misuse|(non)?infringement|privacy|policy|practice|protection|removal|right|risk(s)?|safety|sample|security|secrecy|statement|term(s)?|trademark|transfer|(unauthorized|fraudulent|illicit)\suse|violation|warranty)\s(of)\b', term):
		return True
	if re.search(r'\b(privacy(\s(policy|law(s)?|practice|statement|right|act))?|collected\sinformation|security\spractice|intellectual\sproperty(\s(right))?|information\s(handling|gathering)|encrypt(ion)?)\b', term):
		return True
	return False

def ignoreTerms(term):
	return True if re.search(r'^\s*(n\.\s*a(\.)?|et\sal|eula|etc|possible|us|includ(e|ing)|herein|llc|example|button|transfer|policy|factor|mean|agreement|widget|share|item|disclosure|jurisdiction|offering|way|warranty|violation|thing|implied|firewall|encryption|inc(\.)?|thereto|trade(\-)?\s*mark|copyright|td|wrongdoing|hereto|hereinafter|liability)\s*$', term) else False
            
def ignoreNltkStopwords(term):
	return True if re.search(r'^\s*(i|me|my|myself|we|our|ours|ourselves|you|youre|youve|youll|youd|your|yours|yourself|yourselves|he|him|his|himself|she|shes|her|hers|herself|it|its|its|itself|they|them|their|theirs|themselves|what|which|who|whom|this|that|thatll|these|those|am|is|are|was|were|be|been|being|have|has|had|having|do|does|did|doing|a|an|the|and|but|if|or|because|as|until|while|of|at|by|for|with|about|against|between|into|through|during|before|after|above|below|to|from|up|down|in|out|on|off|over|under|again|further|then|once|here|there|when|where|why|how|all|any|both|each|few|more|most|other|some|such|no|nor|not|only|own|same|so|than|too|very|s|t|can|will|just|don|dont|should|shouldve|now|d|ll|m|o|re|ve|y|ain|aren|arent|couldn|couldnt|didn|didnt|doesn|doesnt|hadn|hadnt|hasn|hasnt|haven|havent|isn|isnt|ma|mightn|mightnt|mustn|mustnt|needn|neednt|shan|shant|shouldn|shouldnt|wasn|wasnt|weren|werent|won|wont|wouldn|wouldnt)\s*$', term) else False

def ignoreWebsiteUrlLink(term):
	return True if re.search(r'\b(website_url_lnk)\b', term) else False

def isSingleLetterTerm(term):
	return True if re.search(r'^\s*[a-z]\s*$', term) else False

def startsWithOrEndsWithPrep(term):
	return True if re.search(r'^\s*(of|at|in|with|by|on|as|if|to|for)\s', term) or re.search('\s(of|at|in|on|with|by|as|if|to|for)\s*$', term) else False

def checkOntIgnoreList(term, negativeTermRegex, generalIgnoreRegex):
	if negativeTermRegex.search(term):
		return True
	return True if generalIgnoreRegex.search(term) else False

def startsWithCoref(term):
	return True if re.search(r'^\s*(this|that|such)\b', term) else False

def potentialConjunction(term):
	if re.search(r',', term): # If it contains a comma, it could be two words together.
		return True
	if re.search(r'/', term):
		return True
	return True if re.search(r'\b(and|or)\b', term) else False

def shouldIgnoreTerm(term, generalIgnoreRegex = None, ontIgnoreRegex=None, preprocessFlag=True):
	if preprocessFlag:
		term = preprocess(term)
	if len(term) <= 1 or potentialConjunction(term) or startsWithCoref(term) or checkOntIgnoreList(term, ontIgnoreRegex, generalIgnoreRegex) or ignoreNltkStopwords(term) or isSingleLetterTerm(term) or ignoreWebsiteUrlLink(term) or not startsWithLetter(term) or ignorePhrases(term) or ignoreTerms(term) or startsWithOrEndsWithPrep(term):
		return True
	return False
