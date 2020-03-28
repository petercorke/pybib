# Bibliography entry class
#   - holds all information about one bibliographic item
#   - provides methods for manipulating/setting/representing that information
#
# TODO:
#    __repr__ method needs to do a better job depending on the reference type, similar
#        logic is required in bib2html (but it's not their either...)
#

# Copyright (c) 2007, Peter Corke
#
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The name of the copyright holder may not be used to endorse or 
#	promote products derived from this software without specific prior 
#	written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

import sys;
import string;
import re;

#BadValue = "Bad value";
#BadField = "Bad field";
#BadRefType = "Bad reference type";

class BibEntry:
	fieldDict = {};
	verbose = 0;
	bibliography = {};

	def __init__(self, key, bib):
		self.key = key;
		self.fieldDict = {};
		self.bibliography = bib;
		if BibEntry.verbose:
			print >> sys.stderr, "New entry ", key;

	def __repr__(self):
		str = '"' + self.getTitle() + '"; ';
		try:
			str = str + self.getAuthorsNames();
		except:
			try:
				str = str + "eds. " + self.getEditorsNames();
			except:
				pass;
		month = self.getMonthName();
		year = self.getYear();
		book = self.getBooktitle();
		if book:
			str += ", " + book;
		if month:
			str += ", " + month;
			if year > 0:
				str += " " + `year`;
		else:
			if year > 0:
				str += ", " + `year`;
		str += '.';
		return str;

	def brief(self, fp=sys.stdout):
		print >> fp, self;

	def display(self, fp=sys.stdout):
		print >> fp, "%12s: %s" % ("CiteKey", self.key)
		for k in self.fieldDict:
			if k[0] == '_':
				continue;
			if k == 'Author':
				print >> fp, "%12s: %s" % (k, self.getAuthors())
			else:
				print >> fp, "%12s: %s" % (k, self.fieldDict[k])

	def __getitem__(self, i):
		if type(i) is str:
			return self.fieldDict[i];
		elif type(i) is int:
			return self.fieldDict.keys()[i];
		else:
			raise;


	def check(self):
		keys = self.fieldDict.keys();
		missing = [];
		reftype = self.getRefType();
		if not (reftype in alltypes):
			raise AttributeError, "bad reference type [%s]" % self.getKey();
		for k in required_fields[self.getRefType()]:
			if not (string.capitalize(k) in keys):
				missing.append(k);
		return missing;
			
	#############################################################3
	# get methods
	#############################################################3

	def getKey(self):
		return self.key;

	def getField(self, field):
		#print >> sys.stderr, field
		#print >> sys.stderr, self.fieldDict[field]
		field = field.capitalize();
		if field in self.fieldDict:
			return self.fieldDict[field]
		else:
			return None;

	def getRefType(self):
		return self.reftype;

	def isRefType(self, rt):
		return self.getRefType().lower() == rt.lower();

	def getTitle(self):
		if 'Title' in self.fieldDict:
			title = self.fieldDict['Title'];
			title = re.sub(r"""[{}]""", "", title);
			title = title.strip('.,\'"');
			return title;
		else:
			return "";

	def getURL(self):
		if 'Url' in self.fieldDict:
			url = self.fieldDict['Url'];
			return url;
		else:
			return "";

	def getAuthorList(self):
		if 'Author' in self.fieldDict:
			return self.fieldDict['Author'];
		else:
			return [];

	def getAuthors(self):
		if 'Author' in self.fieldDict:
			l = self.fieldDict['Author'];
			if len(l) == 1:
				return l[0];
			elif len(l) == 2:
				return l[0] + " and " + l[1];
			elif len(l) > 2:
				return string.join(l[:-1], ", ") + " and " + l[-1];
		else:
			return "";


	def surname(self, author):
		# remove LaTeX accents
		def chg(mo): return mo.group(mo.lastindex);
		re_accent = re.compile(r'''\\[.'`^"~=uvHcdb]\{(.)\}|\t\{(..)\}''');
		author = re_accent.sub(chg, author)

		# "surname, first names"
		m = re.search(r"""^([^,]*),(.*)""", author);
		if m:
			#print >> sys.stderr, m.group(1), m.group(2)
			#return m.group(1) + "," + m.group(2).lstrip()[0];
			return [m.group(1), m.group(2).lstrip()[0]];
			#return m.group(1);

		# "first names surname"

		# take the last component after dot or space
		#m = re.search(r"""([a-zA-Z][a-zA-Z-]*)$""", author);
		m = re.search(r"""(.*?)([^\. \t]*)$""", author);
		if m:
			#print >> sys.stderr, author, ":", m.group(2), "|",  m.group(1)
			return [m.group(2), m.group(1)[0]];
			#return m.group(2) + "," + m.group(1)[0];

		return "";

	def getAuthorsSurnameList(self):			
		if 'Author' in self.fieldDict:
			l = self.fieldDict['Author'];
			return map(self.surname, l);

	def getAuthorsSurname(self):
		l = self.getAuthorsSurnameList();
		try:
			l = map(lambda x: x[0], l);
			if len(l) == 1:
				return l[0];
			elif len(l) == 2:
				return l[0] + " and " + l[1];
			elif len(l) > 2:
				return string.join(l[:-1], ", ") + " and " + l[-1];
			else:
				return "";
		except:
			return "<NO AUTHOR>";

	# return initial dot sunrname
	def getAuthorsNames(self):
		l = self.getAuthorsSurnameList();
		l = map(lambda x: x[1] + ". " + x[0], l);
		if len(l) == 1:
			return l[0];
		elif len(l) == 2:
			return l[0] + " and " + l[1];
		elif len(l) > 2:
			return string.join(l[:-1], ", ") + " and " + l[-1];
		else:
			return "";

	# return initial dot sunrname

	def getEditorsSurnameList(self):			
		if 'Editor' in self.fieldDict:
			l = self.fieldDict['Editor'];
			return map(self.surname, l);
			
	def getEditorsNames(self):
		l = self.getEditorsSurnameList();
		if not l:
			return None;
		l = map(lambda x: x[1] + ". " + x[0], l);
		if len(l) == 1:
			return l[0];
		elif len(l) == 2:
			return l[0] + " and " + l[1];
		elif len(l) > 2:
			return string.join(l[:-1], ", ") + " and " + l[-1];
		else:
			return "";

	def getBooktitle(self):
		if 'Booktitle' in self.fieldDict:
			return  self.fieldDict['Booktitle'];
		else:
			return "";

	def getVolume(self):
		if 'Volume' in self.fieldDict:
			return self.fieldDict['Volume'];
		else:
			return -1;

	def getNumber(self):
		if 'Number' in self.fieldDict:
			return self.fieldDict['Number'];
		else:
			return -1;

	def getPage(self):
		if 'Pages' in self.fieldDict:
			return self.fieldDict['Pages'];
		else:
			return "";

	def afterDate(self, date):
		'''True if the entry occurs after the specified date'''
		
		if not date:
			return True;
		elif len(date) == 1:
			# simple case, year only
			return self.getYear() >= date[0];
		elif len(date) == 2:
			# complex case, [month year]
			if self.getYear() > date[1]:
				return True;
			elif (date[1] == self.getYear()) and (self.getMonth() >= date[0]):
				return True;
			else:
				return False;
	def beforeDate(self, date):
		'''True if the entry occurs before the specified date'''
		
		if not date:
			return True;
		elif len(date) == 1:
			# simple case, year only
			return self.getYear() < date[0];
		elif len(date) == 2:
			# complex case, [month year]
			if self.getYear() < date[1]:
				return True;
			elif (date[1] == self.getYear()) and (self.getMonth() < date[0]):
				return True;
			else:
				return False;

	def getYear(self):
		if '_year' in self.fieldDict:
			return self.fieldDict['_year'];
		else:
			return -1;

	# return month ordinal in range 1 to 12
	def getMonth(self):
		if '_month' in self.fieldDict:
			return self.fieldDict['_month'];
		else:
			return -1;

	monthdict = {
		'january' : 1,
		'february' : 2,
		'march' : 3,
		'april' : 4,
		'may' : 5,
		'june' : 6,
		'july' : 7,
		'august' : 8,
		'september' : 9,
		'october' : 10,
		'november' : 11,
		'december' : 12  };

	def getMonthName(self):
		monthNames = (
			'january',
			'february',
			'march',
			'april',
			'may',
			'june',
			'july',
			'august',
			'september',
			'october',
			'november',
			'december' );
		m = self.getMonth();
		if m > 0:
			return string.capitalize(monthNames[m-1]);
		else:
			return "";



	#############################################################3
	# set methods
	#############################################################3

	def setType(self, value):
		value = string.lower(value);
		if not (value in alltypes):
			raise AttributeError, "bad reference type [%s]" % self.getKey();
		self.reftype = value;
		self.fieldDict['Type'] = value;

	def setField(self, key, value):
		key = key.capitalize();
		if not (key in allfields):
			raise AttributeError, "bad field <%s> [%s]" % (key, self.getKey());
		if key == 'Year':
			self.fieldDict[key] = value;

			# remove all text like "to appear", just leave the digits
			year = filter(lambda c : c.isdigit(), value);
			try:
				self.fieldDict['_year'] = int(year);
			except:
				if value.find('appear') > -1:
					sys.stderr.write("[%s] no year specified, continuing\n" % self.getKey());
					self.fieldDict['_year'] = 0;
				else:
					self.fieldDict['_year'] = -1;
					raise AttributeError, "[%s] bad year <%s>" % (self.getKey(), value);
		elif key == 'Month':
			# the Month entry has the original string from the file if it is of
			# nonstandard form, else is None.
			# the hidden entry _month has the ordinal number
			self.fieldDict[key] = value;
			#print >> sys.stderr, "Month = <%s>" % value;
			month = mogrify(value);
			for monthname in self.monthdict:
				# handle month abbreviations, eg. nov in november
				if monthname.find(month) >= 0:
					self.fieldDict['_month'] = self.monthdict[monthname];
					#print >> sys.stderr, "_month 1 %d" % self.monthdict[monthname];
					self.fieldDict[key] = None;
						
					return;
				# handle extraneous like november in 'november 12-13'
				if month.find(monthname) >= 0:
					self.fieldDict['_month'] = self.monthdict[monthname];
					#print >> sys.stderr, "_month 2 %d" % self.monthdict[monthname];
					return;
			raise AttributeError, "bad month [%s]" % self.getKey();
		else:
			self.fieldDict[key] = value;
		#print >> sys.stderr, "<%s> := <%s>\n" % (key, value)



	#############################################################3
	# matching methods
	#############################################################3

	def search(self, field, str, caseSens=0):
		field = string.capitalize(field);

		if field.lower() == 'all':
			for be in self:
				for k in self.fieldDict:
					if k[0] == '_':
						continue;
					s = self.fieldDict[k];
					if isinstance(s, list):
						s = ' '.join(s);
					if s:
						if caseSens == 0:
							m = re.search(str, s, re.IGNORECASE);
						else:
							m = re.search(str, s);
						if m:
							return True;
				
		else:
			# silently ignore search field if not present
			if not(field in self.fieldDict):
				return False;
			s = self.fieldDict[field];
			if isinstance(s, list):
				s = ' '.join(s);
			if s:
				if caseSens == 0:
					m = re.search(str, s, re.IGNORECASE);
				else:
					m = re.search(str, s);
				if m:
					return True;

		return 0;


	def matchAuthorList(self, be):

		def split(a):
			return re.findall(r"""([a-zA-Z][a-zA-Z-]*[.]?)""", a);

		def matchfrag(s, f):
			sdot = s[-1:] == '.';
			fdot = f[-1:] == '.';

			if (sdot == 0) and (fdot == 0):
				return s == f;
			elif (sdot == 0) and (fdot == 1):
				matchstr = f + '*';
				m = re.match(matchstr, s);
				if m:
					return m.group(0) == s;
				else:
					return 0;
			elif (sdot == 1) and (fdot == 0):
				matchstr = s + '*';
				m = re.match(matchstr, f);
				if m:
					return m.group(0) == f;
				else:
					return 0;
			elif (sdot == 1) and (fdot == 1):
				return s == f;

		def matchAuthor(a1, a2):
			l1 = split(a1);
			l2 = split(a2);
			count = 0;

			for p1 in l1:
				for p2 in l2:
					if matchfrag(p1,p2):
						count += 1;
			return count;

		# check if each article has the same number of authors
		l1 = self.getAuthorList();
		l2 = be.getAuthorList();
		if len(l1) != len(l2):
			return 0;

		# now check the authors match, in order
		for i in range( len(l1) ):
			if matchAuthor(l1[i], l2[i]) < 2:
				return 0;
		return 1;

	def matchTitle(self, be, dthresh):
		# Levenstein distance between two strings
		def distance(a,b):
		    c = {}
		    n = len(a); m = len(b)

		    for i in range(0,n+1):
			c[i,0] = i
		    for j in range(0,m+1):
			c[0,j] = j
			
		    for i in range(1,n+1):
			for j in range(1,m+1):
			    x = c[i-1,j]+1
			    y = c[i,j-1]+1
			    if a[i-1] == b[j-1]:
				z = c[i-1,j-1]
			    else:
				z = c[i-1,j-1]+1
			    c[i,j] = min(x,y,z)
		    return c[n,m]

		d = distance( mogrify(self.getTitle()), mogrify(be.getTitle()) );

		return d <= dthresh;

	def matchType(self, be):
		return self.getRefType() == be.getRefType();

	def matchYear(self, be):
		return fmatch(self.getYear(), be.getYear());

	def matchMonth(self, be):
		return fmatch(self.getMonth(), be.getMonth());

	def matchVolumeNumber(self, be):
		if not fmatch(self.getVolume(), be.getVolume()):
			return 0;
		if not fmatch(self.getNumber(), be.getNumber()):
			return 0;
		return 1;

	def matchPage(self, be):

		p1 = self.getPage();
		p2 = be.getPage();
		if p1 and p2:
			# both not null
			p1 =  re.findall("([0-9.]+)", p1);
			p2 =  re.findall("([0-9.]+)", p2);
			if (len(p1) > 0) and (len(p2) > 0):
				# optionally compare starting page numbers
				if p1[0] != p2[0]:
					return 0;
			if (len(p1) > 1) and (len(p2) > 1):
				# optionally compare ending page numbers
				if p1[1] != p2[1]:
					return 0;
			return 1;
		else:
			return 1;


	# see if two bibentries match
	def match(self, be, dthresh=2):
		# we do the cheapest comparisons first...
		if not self.matchType(be):
			return 0;
		if not self.matchYear(be):
			return 0;
		if not self.matchMonth(be):
			return 0;
		if self.isRefType("Article"):
			if not self.matchVolumeNumber(be):
				return 0;
		if not self.matchPage(be):
			return 0;
		if not self.matchAuthorList(be):
			return 0;
		if not self.matchTitle(be, dthresh):
			return 0;
		return 1;

# we adopt the convention that a numeric value of -1 means not provided,
# so here we match two quantites where either or both is not provided.  Only
# return false if both numbers are provided, and they are not equal, otherwise
# give the benefit of the doubt and return true.
def fmatch(n1, n2):
	if (n1 > 0) and (n2 > 0):
		return n1 == n2;
	else:
		return 1;

# remove all punctuation marks and white space that people
# might get wrong
def mogrify(s):
	s = string.lower(s);
	s = re.sub(r"""[#{}:;,&$ -]""", "", s);
	return s;


allfields = ('_Reftype', 'Address', 'Author', 'Booktitle', 'Chapter', 'Edition',
	     'Editor', 'Howpublished', 'Institution', 'Journal', 'Month',
	     'Number', 'Organization', 'Pages', 'Publisher', 'School',
	     'Series', 'Title', 'Type', 'Volume',
	     'Year', 'Note', 'Code', 'Url', 'Crossref', 'Annote', 'Abstract', 'Date-added', 'Date-modified', 'Read');

# list of all reference types
alltypes = ('article', 'book', 'booklet', 'inbook', 'incollection',
	    'inproceedings', 'manual', 'mastersthesis', 'misc', 'phdthesis',
	    'proceedings', 'techreport', 'unpublished');

# list of additional fields, ignored by the standard BibTeX styles
ign = ('crossref', 'code', 'url', 'annote', 'abstract');

# lists of required and optional fields for each reference type

required_fields = {
  'article' :		['Author', 'Title', 'Journal', 'Year'],
  'book' :		['Author', 'Title', 'Publisher', 'Year'],
  'booklet' :		['Title'],
  'inbook' :		['Author', 'Title', 'Chapter', 'Pages', 
  				'Publisher', 'Year'],
  'incollection' :	['Author', 'Title', 'Booktitle', 'Publisher', 'Year'],
  'inproceedings' :	['Author', 'Title', 'Booktitle', 'Year'],
  'manual' :		['Title'],
  'misc' : 		[],
  'mastersthesis' :	['Author', 'Title', 'School', 'Year'],
  'phdthesis' :		['Author', 'Title', 'School', 'Year'],
  'proceedings' :	['Title', 'Year'],
  'techreport' :	['Author', 'Title', 'Institution', 'Year'],
  'unpublished' :	['Author', 'Title', 'Note']
};

opt_fields = {
  'article' :		['Volume', 'Number', 'Pages', 'Month', 'Note'],
  'book' :		['Editor', 'Volume', 'Number', 'Series', 'Address',
  				'Edition', 'Month', 'Note'],
  'booklet' :		['Author', 'Howpublished', 'Address', 'Month', 'Year',
  				'Note'],
  'inbook' :		['Editor', 'Volume', 'Series', 'Address', 'Edition',
  				'Month', 'Note'],
  'incollection' :	['Editor', 'Volume', 'Number', 'Series', 'Type', 
  				'Chapter'  'Pages', 'Address', 'Edition',
				'Month', 'Note'],
  'inproceedings' :	['Editor', 'Pages', 'Organization', 'Publisher', 
  				'Address', 'Month', 'Note'],
  'manual' :		['Author', 'Organization', 'Address', 'Edition',
  				'Month', 'Year', 'Note'],
  'misc' :		['Title', 'Author', 'Howpublished', 'Month', 'Year',
  				'Note'],
  'mastersthesis' :	['Address', 'Month', 'Note'],
  'phdthesis' :		['Address', 'Month', 'Note'],
  'proceedings' :	['Editor', 'Publisher', 'Organization', 'Address', 
  				'Month', 'Note'],
  'techreport' :	['Type', 'Number', 'Address', 'Month', 'Note'],
  'unpublished' :	['Month', 'Year']
};
