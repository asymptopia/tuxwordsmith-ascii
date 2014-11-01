# -*- coding: latin-1 -*-
"""
/***************************************************************************

	Author			:Charles B. Cosse 
	
	Email			:ccosse@gmail.com
					
	Website			:www.asymptopia.org
	
	Copyright		:(C) 2002-2007 Asymptopia Software.
	
 ***************************************************************************/
"""
import xml,sys,os,string,unicodedata
from xml.sax import make_parser
from xml.sax import saxutils
from xml.sax.handler import feature_namespaces

DEBUG=False

letters=['"','&',';',':','?','<','>',' ','-','.','/','"','(',')',"'",'{','}','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
	u'\xe0',# à
	u'\xe1',# á
	u'\xe2',# â
	u'\xe3',# ã
	u'\xe4',# ä
	u'\xe6',# æ
	u'\xe7',# ç
	u'\xe8',# è
	u'\xe9',# é
	u'\xee',# î
	u'\xef',# ï
	u'\xed',# í
	u'\xeb',# ë
	u'\xea',# ê
	u'\xf1',# ñ
	u'\xf3',# ó
	u'\xf4',# ô
	u'\xf6',# ö
	u'\xf9',# ù
	u'\xfa',# ú
	u'\xfb',# û
	u'\xfc',# ü
]
def lower_uchar(uchar):
	
	uchar_name=None
	
	try:uchar_name=unicodedata.name(uchar)
	except Exception,e:
		#print e,type(uchar),uchar.encode('latin1')
		#rval=raw_input('q?')
		#if rval=='q':sys.exit()
		return uchar
	
	modified_uchar_name=string.replace(uchar_name,'CAPITAL','SMALL')
	modified_uchar=unicodedata.lookup(modified_uchar_name)
	return modified_uchar

def upper_uchar(uchar):
	
	uchar_name=None
	
	try:uchar_name=unicodedata.name(uchar)
	except Exception,e:
		#print e,uchar,uchar.encode('latin1')
		return uchar
	
	modified_uchar_name=string.replace(uchar_name,'SMALL','CAPITAL')
	modified_uchar=unicodedata.lookup(modified_uchar_name)
	return modified_uchar

def lower_uword(uword):
	print 'lower_uword'
	
	
class XDXFParser(xml.sax.ContentHandler):
	def __init__(self):
		self.inKey=False
		self.in_arContent=False
		self.current_key=''
		self.content=''
		
	def error(self, exception):
		if DEBUG:print exception
	
	def normalize_whitespace(self,text):
		"Remove redundant whitespace from a string"
		return ' '.join(text.split())

class GetInfo(XDXFParser):
	
	def __init__(self):
		XDXFParser.__init__(self)
		self.ar_count=0
		self.k_count=0
		self.keys=[]
		
	def startElement(self,name,attrs):
		if name=='ar':
			self.ar_count+=1
			self.in_arContent=True
		elif name=='k':
			self.k_count+=1
			self.inKey=True
			self.current_key=''

	def characters(self,ch):
		if self.inKey:
			self.current_key=self.current_key+ch
			
	def endElement(self,name):
		if name=='ar':
			self.in_arContent=False
		if name=='k':
			self.inKey=False	
			self.current_key=self.normalize_whitespace(self.current_key)
			self.keys.append(self.current_key)

	def display_info(self):
		if DEBUG:print self.keys
		if DEBUG:print "ar_count:\t%s"%(self.ar_count)
		if DEBUG:print "k_count:\t%s"%(self.ar_count)

class GetFieldContent(XDXFParser):
	
	def __init__(self,target):
		XDXFParser.__init__(self)
		self.rval=None
		self.target=target
		self.inTarget=False
		self.DONE=False
		
	def characters(self,ch):
		if self.inTarget:
			self.rval=self.rval+ch

	def startElement(self,name,attrs):
		if self.DONE:return
		if name==self.target:
			self.inTarget=True
			self.rval=''
		
	def endElement(self,name):
		if name==self.target:
			self.inTarget=False
			self.DONE=True
			

class GetArticle(XDXFParser):
	
	def __init__(self,target):
		XDXFParser.__init__(self)
		self.target=target
		self.inTarget=False
		self.inTR=False
		self.DONE=False
		
		self.article={
			'key':None,
			'content':None,
		}
	
	def getArticle(self):
		return self.article
		
	def characters(self,ch):
		if self.inTR:return
		if self.inKey:
			self.current_key=self.current_key+ch
		if self.inTarget:
			self.content=self.content+ch

	def startElement(self,name,attrs):
		if self.DONE:return
		if name=='ar':
			self.in_arContent=True
		elif name=='k':
			self.inKey=True
			self.current_key=''
		elif name=='tr':
			self.inTR=True
		
	def endElement(self,name):
		if name=='ar':
			self.in_arContent=False
			if self.inTarget:
				self.current_key=''
				self.inTarget=False
				self.article['content']=self.content
				self.DONE=True
				
		elif name=='k':
			self.inKey=False
			self.current_key=self.normalize_whitespace(self.current_key)
			if self.current_key==self.target:
				self.inTarget=True
				self.article['key']=self.current_key
				self.content=''
		elif name=='tr':
			self.inTR=False
			
class GetKeys(XDXFParser):
	
	def __init__(self,target_range):
		XDXFParser.__init__(self)
		if len(target_range)==5:
			target_range=string.split(target_range,'-',1)
			self.indices=[
				letters.index(string.lower(target_range[0][0])),
				letters.index(string.lower(target_range[0][1])),
				letters.index(string.lower(target_range[1][0])),
				letters.index(string.lower(target_range[1][1])),
			]
		elif len(target_range)==3 and target_range=='ALL':
			self.indices=[
				0,0,1000,1000
			]
		elif len(target_range)==1:
			self.indices=[letters.index(string.lower(target_range))]
			if DEBUG:print 'self.indices=',self.indices
		else:
			if DEBUG:print 'target_range=',target_range
			
		self.key_count=0
		self.keys=[]
		
	def startElement(self,name,attrs):
		if name=='ar':
			self.in_arContent=True
		elif name=='k':
			self.inKey=True
			self.current_key=''

	def characters(self,ch):
		
		if not self.inKey:return
		RETURN=False
		
		try:
			idx0=letters.index(lower_uchar(ch[0]))
		except Exception,e:
			if DEBUG:print e,lower_uchar(ch[0]).encode('latin1'),`self.current_key`
			#rval=raw_input('line 231 xdxf_parser; quit?')
			#if rval=='q':sys.exit()
			
			self.inKey=False
			RETURN=True
			return
			
		if len(self.indices)==1:
			if idx0==self.indices[0]:
				self.current_key=ch
				#print idx0,self.indices[0],ch
				return
			else:
				self.inKey=False
				RETURN=True
				return
			
		idx1=None
		if len(ch)>1:
			try:
				if ch[1]!=' ':idx1=letters.index(lower_uchar(ch[1]))
			except Exception,e:
				if DEBUG:print e
				if DEBUG:print unicode(ch[1]).encode('latin1'),type(ch[1])
				#rval=raw_input('line 255 xdxf_parser; quit?')
				#if rval=='q':sys.exit()
			
				self.inKey=False
				return
				
		#check AT_OR_AFTER first range
		if idx0>=self.indices[0]:
			if not idx1:pass
			elif idx1>=self.indices[1]:pass
			else:RETURN=True
		else:RETURN=True
					
		#check AT_OR_BEFORE second range
		if idx0<=self.indices[2]:
			if not idx1:pass
			elif idx1<=self.indices[3]:pass
			else:RETURN=True
		else:RETURN=True
		
		if RETURN:
			self.inKey=False
			return
		
		self.current_key=ch
		
	
	def endElement(self,name):
		if name=='ar':
			self.in_arContent=False
		if name=='k':
			if self.inKey==True and self.current_key!='':
				self.current_key=self.normalize_whitespace(self.current_key)
				
				#NEED:strip-out {} and other? in key so get more words....
				
				self.keys.append(self.current_key)
				self.key_count+=1
				try:
					if DEBUG:print self.key_count,len(self.keys),self.current_key.encode('latin1'),self.indices
				except Exception,e:
					if DEBUG:print e,`self.current_key`,unicode(self.current_key).encode('latin1')
					#rval=raw_input('line 294 -- no problem -- just special chars in key: q?')
					#if rval=='q':sys.exit()
			
			self.inKey=False	
			

parser = make_parser()

if __name__=='__main__':
	
	
	#Tell the parser we are not interested in XML namespaces
	parser.setFeature(feature_namespaces, 0)
	
	#dh=GetInfo()
	dh=GetArticle('Zincking')
	#dh=GetArticle('Somalia')
	parser.setContentHandler(dh)
	inf=open('xdxf/webster_1913/dict.xdxf')
	#inf=open('xdxf/world02/dict.xdxf')
	parser.parse(inf)
	inf.close()
	
	#dh.display_info()
	result=dh.getArticle()
	try:
		if DEBUG:print result['key']
		if DEBUG:print string.strip(result['content'])
		language='english'
		cmd="echo %s|festival --tts --language %s"%('Here is the result for: ',language)
		os.system(cmd)
		cmd="echo %s|festival --tts --language %s"%(result['key'],language)
		os.system(cmd)
		cmd="echo %s|festival --tts --language %s"%(result['content'],language)
		os.system(cmd)
		
	except Exception,e:
		if DEBUG:print e
