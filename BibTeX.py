# Defines two classes:
#
#  BibTexEntry, subclass of BibEntry, and provides all BibTeX specific methods such as
#    writing an entry to file
#
#  BibTex, a subclass of Bibliography, and provides all BibTeX specific methods, in
#    particular a parser.

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

import Bibliography;
import BibEntry;
import string;
import re;
import sys;
import urllib;

class BibTeXEntry(BibEntry.BibEntry):

	# write a BibTex format entry
	def write(self, file=sys.stdout, stringdict=None):
		file.write( "@%s{%s,\n"  % (self.getRefType(), self.getKey()) );
		count = 0
		for rk in self.fieldDict:
			count += 1;
			# skip internally used fields
			if rk[0] == '_':
				continue;
			if rk == 'Type':
				continue;

			# generate the entry
			value = self.fieldDict[rk];
			file.write("    %s = " % rk );

			if rk in ['Author', 'Editor']:
				file.write("{%s}" % " and ".join(value) );
			elif rk == 'Month':
				if value:
					file.write("{%s}" % value );
				else:
					value = self.getMonthName();
					file.write("%s" % value[0:3].lower() );
			else:
				# is it an abbrev?
				if value in self.bibliography.abbrevDict:
					file.write("%s" % value );
				else:
					file.write("{%s}" % value );

			# add comma to all but last fields
			if count < len(self.fieldDict):
				file.write(",\n");
			else:
				file.write("\n");
		file.write("}\n\n");


	def setField(self, field, value):
		def strStrip(s):
			s = string.strip(s, ' ');
			if (s[0] == '"') and (s[-1] == '"'):
				return s[1:-1];
			if (s[0] == '{') and (s[-1] == '}'):
				return s[1:-1];
			return s;


		# deal specially with author list, convert from bibtex X and Y to
		# a list for bibentry class
		if field.lower() in ["author", "editor"]:
			value = string.split(value, " and ");
			value = map(strStrip, value);
		try:
			# invoke the superclass
			BibEntry.BibEntry.setField(self, field, value);
		except AttributeError, err:
			sys.stderr.write( "%15s: bad value <%s=%s>" % (self.getKey(), field, value));

class BibTeX(Bibliography.Bibliography):

	stringDict = {};

	def parseFile(self, fileName=None, verbose=0, ignore=False):
		if fileName == None:
			fp = sys.stdin;
		else:
			fp = self.open(fileName);

		# get the file into one huge string
		nbib = 0;
		s = fp.read();
		try:
			nbib = self.parseString(s, ignore=ignore, verbose=verbose);
		except AttributeError, err:
			print >> sys.stderr, "Error %s" % err;

		self.close(fp);
		return nbib;

	def display(self):
		for be in self:
		        be.display()

	def write(self, file=sys.stdout, resolve=0):
		if resolve:
			dict = self.stringDict;
		else:
			dict = None;

		for be in self:
		        be.write(file, dict)

	def writeStrings(self, file=sys.stdout):
		for abbrev, value in self.abbrevDict.items():
		        file.write("@string{ %s = {%s} }\n" % (abbrev, value) );

	# resolve BibTeX's cross reference capability
	def resolveCrossRef(self):
		for be in self:
			try:
				xfref = self.getField('crossref');
			except:
				return;

			for f in xref:
				if not (f in be):
					be.setField(f, xref.getField(f));

	def parseString(self, s, verbose=0, ignore=False):

		# lexical analyzer for bibtex format files
		class BibLexer:

			inString = "";	# the string to parse
			lineNum = 1;
			pos = 0;

			def __init__(self, s):
				self.inString = s;

			# an iterator for the class, return next character
			def next(self):
				if self.pos >= len(self.inString):
					raise StopIteration;
				c = self.inString[self.pos];
				if c == '\n':
					self.lineNum += 1;
				self.pos += 1;
				return c;

			def __iter__(self):
				return self;

			# peek at the next character
			def peek(self):
				return self.inString[self.pos];

			# push a character back onto the input
			def pushback(self, c):
				self.pos -= 1;
				if c == '\n':
					self.lineNum -= 1;

			# eat whitepsace characters and comments
			def skipwhite(self):
				
				for c in self:
					if c == '%':
						for c in self:
							if c == '\n':
								break;
					elif (not c.isspace()):
						self.pushback(c);
						break;

			# print >> sys.stderr, the input buffer
			def show(self):
				print >> sys.stderr, "[%c]%s" % (self.inString[0], self.inString[1:10]);

			# get the next word from the input stream, this can be
			#	[alpha][alnum$_-]
			#	"...."
			#	{....}
			def nextword(self):

				str = "";
				c = self.peek();

				if c == '"':
					# quote delimited string
					str = self.next();
					cp = None;	# prev char
					for c in self:
						str += c;
						if (c == '"') and (cp != '\\'):
							break;
						cp = c;
				elif c == '{':
					# brace delimited string
					count = 0;
					for c in self:
						if c == '{':
							count += 1;
						if c == '}':
							count -= 1;
							
						str += c;
						if count == 0:
							break;
				else:
					# undelimited string
					#if (not c.isalpha()):
					#	print >> sys.stderr, "BAD STRING"
					for c in self:
						if c.isalnum():
							str += c;
						elif c in ".+-_$:'":
							str += c;
						else:
							self.pushback(c);
							break;
				return str;


		class Token:
			t_ENTRY = 1;
			t_DELIM_L = 2;
			t_DELIM_R = 3;
			t_STRING = 5;
			t_EQUAL = 6;
			t_COMMA = 7;

			val = None;
			type = None;

			def __repr__(self):
				if self.type == self.t_ENTRY:
					str = "@ %s" % self.val;
				elif self.type == self.t_DELIM_R:
					str = "  }";
				elif self.type == self.t_STRING:
					str = "<%s>" % self.val;
				elif self.type == self.t_EQUAL:
					str = "  EQUAL";
				elif self.type == self.t_COMMA:
					str = "  COMMA";
				else:
					str = "BAD TOKEN (%d) <%s>" % (self.type, self.val);
				return str;

			def isstring(self):
				return self.type == self.t_STRING;

			def isabbrev(self):
				return (self.type == self.t_STRING) and self.val.isalnum();

			def iscomma(self):
				return self.type == self.t_COMMA;

			def isequal(self):
				return self.type == self.t_EQUAL;

			def isentry(self):
				return self.type == self.t_ENTRY;

			def isdelimR(self):
				return self.type == self.t_DELIM_R;

			def isdelimL(self):
				return self.type == self.t_DELIM_L;

		#
		# tokenizer for bibtex format files
		#
		class BibTokenizer:

			lex = None;

			def __init__(self, s):
				self.lex = BibLexer(s);
				
			# setup an iterator for the next token
			def __iter__(self):
				return self;

			# return next token
			def next(self):
				#self.lex.show();
				self.lex.skipwhite();
				c = self.lex.next();

				t = Token();
				if c == '@':
					t.type = t.t_ENTRY;
					self.lex.skipwhite();
					t.val = self.lex.nextword();
					self.lex.skipwhite();
					c = self.lex.next();
					if not ((c == '{') or (c == '(')):
						print >> sys.stderr, "BAD START OF ENTRY"

				elif c == ',':
					t.type = t.t_COMMA;
				elif c == '=':
					t.type = t.t_EQUAL;
				elif (c == '}') or (c == ')'):
					t.type = t.t_DELIM_R;
				else:
					self.lex.pushback(c);
					t.type = t.t_STRING;
					t.val = self.lex.nextword();

				return t;


		class BibParser:

			tok = None;
			bibtex = None;

			def __init__(self, s, bt):
				self.tok = BibTokenizer(s);
				self.bibtex = bt;

			# setup an iterator for the next entry
			def __iter__(self):
				return self;

			# return next entry
			def next(self):

				def strstrip(s):
					if s[0] in '"{':
						return s[1:-1];
					else:
						return s;

				t = self.tok.next();
				if not t.isentry():
					raise SyntaxError, self.tok.lex.lineNum;
				if t.val.lower() == 'string':
					tn = self.tok.next();
					if not tn.isstring():
						raise SyntaxError, self.tok.lex.lineNum;
					t = self.tok.next();
					if not t.isequal():
						raise SyntaxError, self.tok.lex.lineNum;
					tv = self.tok.next();
					if not tv.isstring():
						raise SyntaxError, self.tok.lex.lineNum;
					# insert string into the string table
					self.bibtex.insertAbbrev(tn.val, strstrip(tv.val));
					#print >> sys.stderr, "string", tn.val, tv.val
					t = self.tok.next();
					if not t.isdelimR():
						raise SyntaxError, self.tok.lex.lineNum;
				elif t.val.lower() == 'comment':
					depth = 0;
					while True:
						tn = self.tok.next();
						if t.isdelimL():
							depth += 1;
						if t.isdelimR():
							depth -= 1;
							if depth == 0:
								break;
				else:
					# NOT A STRING or COMMENT ENTRY
					# assume a normal reference type

					# get the cite key
					ck = self.tok.next();
					if not ck.isstring():
						raise SyntaxError, self.tok.lex.lineNum;

					#print >> sys.stderr, t.val, ck.val
					be = BibTeXEntry(ck.val, self.bibtex);
					be.setType(t.val);

					# get the comma
					ck = self.tok.next();
					if not ck.iscomma():
						raise SyntaxError, self.tok.lex.lineNum;

					# get the field value pairs
					for tf in self.tok:
						# allow for poor syntax with comma before
						# end brace
						if tf.isdelimR():
							break;

						if not tf.isstring():
							raise SyntaxError, self.tok.lex.lineNum;
						t = self.tok.next();
						if not t.isequal():
							raise SyntaxError, self.tok.lex.lineNum;
						ts = self.tok.next();
						if not ts.isstring():
							raise SyntaxError, self.tok.lex.lineNum;
						#print >> sys.stderr, "  ", tf.val, " := ", ts.val;
						be.setField(tf.val, strstrip(ts.val));

						# if it was an abbrev in the file, put it in the
						# abbrevDict so it gets written as an abbrev
						if ts.isabbrev():
							self.bibtex.insertAbbrev(ts.val, None);
							#print >> sys.stderr, "putting unresolved abbrev %s into dict" % ts.val;

						t = self.tok.next();
						if t.iscomma():
							continue;
						elif t.isdelimR():
							break;
						else:
							raise SyntaxError, self.tok.lex.lineNum;


					self.bibtex.insertEntry(be, ignore);
				return;

		bibparser = BibParser(s, self);
		bibcount = 0;
		try:
			for be in bibparser:
				bibcount += 1;
				pass;
		except SyntaxError, err:
			print "Syntax error at line " + str(err);

		return bibcount;
