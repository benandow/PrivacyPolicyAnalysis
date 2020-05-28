from __future__ import unicode_literals
import spacy
from spacy.matcher import Matcher


def mergeExcludePhrases(doc, vocab):
	def getLemma(ephrase):
		return u' '.join([ tok.lemma_ for tok in ephrase if tok.lemma_ != u':' ])

	results = []
	##########################################
	def callback(matcher, doc, i, matches):
		for match_id, start, end in matches:
			span = doc[start:end]
			results.append(span)
	##########################################
	matcher = Matcher(vocab)
	matcher.add(1, callback,
		[	{spacy.attrs.LOWER: "other"},
			{spacy.attrs.LOWER: "than"},
		])
	matcher.add(2,callback,
		[	{spacy.attrs.LOWER: "aside"},
			{spacy.attrs.LOWER: "from"},
		])
	matcher.add(3,callback,
		[	{spacy.attrs.LOWER: "apart"},
			{spacy.attrs.LOWER: "from"},
		])
	matcher.add(4,callback,
		[	{spacy.attrs.LOWER: "with"},
			{spacy.attrs.LOWER: "the"},
			{spacy.attrs.LOWER: "exception"},
			{spacy.attrs.LOWER: "of"}
		])
	matcher.add(5,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "for"},
		])
	matcher.add(6,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "when"},
		])
	matcher.add(7,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "in"},
		])
	matcher.add(8,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "to"},
		])
	matcher.add(9,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "as"},
		])
	matcher.add(10,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "under"},
		])
	matcher.add(11,callback,
		[	{spacy.attrs.LOWER: "except"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "where"},
		])
	matcher.add(12,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "when"},
		])
	matcher.add(13,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "in"},
		])
	matcher.add(14,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "to"},
		])
	matcher.add(15,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "as"},
		])
	matcher.add(16,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "under"},
		])
	matcher.add(17,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "where"},
		])
	matcher.add(18,callback,
		[	{spacy.attrs.LOWER: "unless"},
			{spacy.attrs.ORTH: ":", 'OP' : '?'},
			{spacy.attrs.LOWER: "for"},
		])
	matcher.add(19,callback,
		[	{spacy.attrs.LOWER: "outside"},
			{spacy.attrs.LOWER: "of"},
		])



	matcher(doc)
	for ephrase in results:
		ephrase.merge(lemma=getLemma(ephrase))
