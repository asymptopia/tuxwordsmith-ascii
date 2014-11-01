# -*- coding: latin-1 -*-
"""
/***************************************************************************

	Author			:Charles B. Cosse 
	
	Email			:ccosse@gmail.com
					
	Website			:www.asymptopia.org
	
	Copyright		:(C) 2002-2007 Asymptopia Software.
	
 ***************************************************************************/
"""


import os,time,math,unicodedata
from random import random

from board import *
from spot import *
from tile import *
from player import Player

from xdxf_parser import *
from letters import *
from line_formatter import *

DEBUG=True
DEBUG=False

class TWS_Solver:
	
	def __init__(self,game):
		
		self.game=game
		self.tray=None
		self.str2pt=self.game.global_config['scoring']
		
		self.fullnames_targets=None
		self.current_resource_key=None
		self.current_resource_path=None
		self.available_words=None
		self.key_count=0
		
		self.special_chars=None
		self.ntuple=None
		self.candidates=None
		
		self.plets={
			'triplets':[],
			'doublets':[],
			'singlets':[],
			#'operator_doublets':self.get_operator_plets(2),
			#'operator_singlets':self.get_operator_plets(1),
		}
		
		self.expressions={
		   'triplet_expressions':[],
		   'doublet_expressions':[],
		   'singlet_expressions':[],
		   'wc_triplet_expressions':[],
		   'wc_doublet_expressions':[],
		   'wc_singlet_expressions':[],
		   'wc_wc_doublet_expressions':[],
		}
		
		#LOAD ONLY ONCE:
		#Parse dictionary:
		if DEBUG:print 'self.get_installed()='
		keys=self.get_installed()
		
		for key in keys:
			if DEBUG:print key.encode('latin1')
		
		self.current_resource_key=None
		self.current_resource_path=None
		
		self.default_resource='Oxford (En)'
		
		for key in self.fullnames_targets.keys():
			
			if DEBUG:print 'key=',type(key),type(self.fullnames_targets[key])
			if DEBUG:print self.fullnames_targets[key],'==',self.default_resource#self.game.global_config['default_resource']
			if DEBUG:print self.fullnames_targets[key]==self.default_resource#self.game.global_config['default_resource']
			
			if self.fullnames_targets[key]==self.default_resource:#self.game.global_config['default_resource']:
				self.current_resource_key=key
				self.current_resource_path=self.default_resource#self.game.global_config['default_resource']
				if DEBUG:print 'KEY :',self.current_resource_key
				if DEBUG:print 'PATH:',self.current_resource_path
				
				
		if not self.current_resource_path:
			self.current_resource_key=self.fullnames_targets.keys()[0]
			self.current_resource_path=self.fullnames_targets[self.current_resource_key]
		
		
		#rval=raw_input('q?')
		#if rval=='q':sys.exit()
		
		
		if DEBUG:print self.current_resource_key.encode('latin1')
		if DEBUG:print self.current_resource_path.encode('latin1')
		
		if DEBUG:print 'loading resource: ',self.current_resource_key
		self.load_resource()
		if DEBUG:print 'len(self.available_words)=',len(self.available_words)
		
		msg="%s (%d words)"%(self.current_resource_key.encode('latin1'),len(self.available_words))
		self.game.set_current_resource(msg)
		
	#This needs modified to handle mult/div:
	def get_operator_plets(self,N):
		
		plets=[]
		available_ops=self.game.global_config['available_operators'][self.game.LEVEL-1]
		
		if(N==1):
			for oidx in range(len(available_ops)):
				plets.append([available_ops[oidx]])
		
		elif(N==2):
			if available_ops.count('-') and available_ops.count('/'):
				plets.append(['-','/'])
				plets.append(['/','-'])
			if available_ops.count('*') and available_ops.count('/'):
				plets.append(['*','/'])
				plets.append(['/','*'])
			if available_ops.count('+') and available_ops.count('/'):
				plets.append(['+','/'])
				plets.append(['/','+'])
			if available_ops.count('+') and available_ops.count('*'):
				plets.append(['+','*'])
				plets.append(['*','+'])
			if available_ops.count('-') and available_ops.count('*'):
				plets.append(['-','*'])
				plets.append(['*','-'])
			if available_ops.count('+') and available_ops.count('-'):
				plets.append(['+','-'])
				plets.append(['-','+'])
			if available_ops.count('/'):
				plets.append(['/','/'])
			if available_ops.count('*'):
				plets.append(['*','*'])
			if available_ops.count('-'):
				plets.append(['-','-'])
			if available_ops.count('+'):
				plets.append(['+','+'])

		return(plets)
	
	def getStringValues(self):
		str_values=[]
		spots=self.tray.get_spots()#not sorted 1-10,so sort:
		nnumbers=self.game.NNUMBERS
		newspots=[]
		for spotidx in range(nnumbers):
			newspots.append(0)#=[0,0,0,0,0,0]
		
		ntrayspots=self.game.NTRAYSPOTS
		while len(spots)>ntrayspots-nnumbers:
			for spot in spots:
				if spot.getMN()[1]<nnumbers:
					newspots[spot.getMN()[1]]=spot
					spots.remove(spot)
				#else:print spot.getMN()
		
		for dummy in range(len(newspots)):
			str_values.append(newspots[dummy].guest.str_val)
		return(str_values)
	
	def getAllStringValues(self):
		str_values=[]
		spots=self.tray.get_spots()#not sorted 1-10,so sort:
		ntrayspots=self.game.NTRAYSPOTS
		newspots=[]
		for spotidx in range(ntrayspots):
			newspots.append(0)#=[0,0,0,0,0,0,0,0,0,0]
		while len(spots)>0:
			for spot in spots:
				newspots[spot.getMN()[1]]=spot
				spots.remove(spot)
		for dummy in range(len(newspots)):
			str_values.append(newspots[dummy].guest.str_val)
		return(str_values)

	def cycle_vals(self,vals):
		tmp=vals.pop()
		vals.insert(int(random()*len(vals)),tmp)
		return(vals)
	
	def get3x2x1x(self,N):
		#N=1,2,3 ~ singlets,doublets,tripplets
		#all unique index-triplets in set of 6 Tiles:
		#if 2 "5"'s in tiles, two "5"-singlets returned, etc..
		plets=[]
		num_times_cycled=0
		str_vals=self.getStringValues()
		#print str_vals
		NumNumbers=6
		while(num_times_cycled<1000):#print ratio when added vs idx on this before v2.0 release
			for idx in range(0,NumNumbers-N):
				i_plet=[]
				s_plet=[]
				for jdx in range(N):
					i_plet.append(float(str_vals[idx+jdx]))#changed to "float" v2.0
				i_plet.sort()
				for jdx in range(N):
					s_plet.append(`i_plet[jdx]`)
				
				if plets.count(s_plet)==0:plets.append(s_plet)
				elif(N==1 and plets.count(s_plet)<str_vals.count(s_plet[0])):
					plets.append(s_plet)
				
			str_vals=self.cycle_vals(str_vals)
			num_times_cycled=num_times_cycled+1
		return(plets)
	
	def evaluate(self,expr):	
		#print expr
		str=''
		for idx in range(len(expr)):
			str=str+expr[idx]
		
		try:
			val=eval(str)
			#print str,val
		except:return(None)
		return(val)

	def get3xPermutations(self,tripplet):#receives single triplet list of len=3
		#print 'tripplet:',tripplet
		p=[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
		px3=[]#list of permuted "t"riplets
		for pidx in range(len(p)):
			tx3=[]#a permuted "t"riplet
			for tidx in range(3):
				#print 'pidx:',pidx,'  tidx:',tidx,'  p[pidx][tidx]-1=',p[pidx][tidx]-1,'  tripplet[p[pidx][tidx]-1]=',tripplet[p[pidx][tidx]-1]
				tx3.append(tripplet[p[pidx][tidx]-1])
			if px3.count(tx3)==0:px3.append(tx3)
			#print 'px3:',px3
		return(px3)	
		
	def get2xPermutations(self,doublet):
		p=[[1,2],[2,1]]
		px2=[]#list of permuted doublets
		for pidx in range(len(p)):
			dx2=[]#permuted doublet
			for tidx in range(2):
				dx2.append(doublet[p[pidx][tidx]-1])
			if px2.count(dx2)==0:px2.append(dx2)
		return(px2)	
	
	def make_special_chars(self):#NEED:only add letters encountered in current_resource
		
		msg="Getting character set..."
		self.game.progress_message(msg)
		
		#FRENCH
		french_chars=[
		u'\xfb',# û
		u'\xee',# î
		u'\xea',# ê
		u'\xe7',# ç
		u'\xf1',# ñ
		u'\xe2',# â
		u'\xf4',# ô
		u'\xe0',# à
		u'\xf9',# ù
		u'\xe9',# é
		u'\xe8',# è
		]
			
		#GERMAN
		german_chars=[
		u'\xfc',# ü
		u'\xfa',# ú
		u'\xc4',# Ä
		u'\xdc',# Ü
		u'\xd6',# Ö
		u'\xe4',# ä
		u'\xf6',# ö
		u'\xe9',# é
		]
		
		#SPANISH
		spanish_chars=[
		u'\xed',# í
		u'\xf3',# ó
		u'\xf1',# ñ
		u'\xfa',# ú
		u'\xe1',# á
		u'\xe9',# é
		u'\xfc',# ü
		]
		
		#LATIN
		latin_chars=[
		u'\xe6',# æ
		]
		
		#ENGLISH
		english_chars=[]
		
		#COMMON
		common_chars=[u'A',u'B',u'C',u'D',u'E',u'F',u'G',u'H',u'I',u'J',u'K',u'L',u'M',u'N',u'O',u'P',u'Q',u'R',u'S',u'T',u'U',u'V',u'W',u'X',u'Y',u'Z']
		
		self.special_chars=[]
		
		target_set=None
		
		dfk=self.game.global_config['default_resource_key']
		
		if 0:pass
		elif dfk=="French-English dictionary":target_set=french_chars+common_chars
		elif dfk=="English-French dictionary":target_set=french_chars+common_chars
		elif dfk=="Spanish-English dictionary":target_set=spanish_chars+common_chars
		elif dfk=="English-Spanish dictionary":target_set=spanish_chars+common_chars
		elif dfk=="Italian-English dictionary":target_set=spanish_chars+common_chars
		elif dfk=="English-Italian dictionary":target_set=spanish_chars+common_chars
		elif dfk=="German-English dictionary":target_set=german_chars+common_chars
		elif dfk=="English-German dictionary":target_set=german_chars+common_chars
		elif dfk=="Latin-English dictionary":target_set=latin_chars+common_chars
		elif dfk=="English-Latin dictionary":target_set=latin_chars+common_chars
		elif dfk=="Swahili-English dictionary":target_set=[]+common_chars
		elif dfk=="Oxford (En)":target_set=[]+common_chars
		else:target_set=[]+common_chars
		
		
		for char in target_set:
			uchar=self.upper_uchar(char)
			
			letter=self.get_unidesc_field(uchar,'VALUE')
			
			mod=self.get_unidesc_field(uchar,'MOD')
			if not mod:mod='NOMOD'
			
			gc_scoring_key="%s_%s"%(letter,mod)
			
			self.special_chars.append({'uchar':uchar,'desc':unicodedata.name(uchar),'gc_scoring_key':gc_scoring_key})
		
		
		self.game.global_config['letters']=[]
		for idx in range(len(self.special_chars)):#1-1 mapping est. here.
			self.game.global_config['letters'].append(self.special_chars[idx]['uchar'])
			self.game.global_config['scoring'][self.special_chars[idx]['uchar']]=1
			self.game.global_config['distribution'][self.special_chars[idx]['uchar']]=1
			#if self.special_chars[idx]['uchar']==u'\xe9':
			#	self.game.global_config['distribution'][self.special_chars[idx]['uchar']]=10
		

	def get_unidesc_field(self,uchar,field):
		unidesc=unicodedata.name(uchar)
		unilist=string.split(unidesc,' ',20)
		fieldmap={
			'CHARSET':0,
			'CASE':1,
			'DESCRIPTOR':2,
			'VALUE':3,
			'PREPOSITION':4,
			'MOD':5,
		}
		idx=fieldmap[field]
		if len(unilist)>idx:return unilist[idx]
		return None
		
			
	def make_normalized_distro(self):
		
		msg="Computing distribution..."
		self.game.progress_message(msg)

		if not self.available_words:return None

		#msg="creating normalized distro for letters using %d words..."%(len(self.available_words))
		#self.feedback_manager.update(msg)

		distro={}#each key is a letter observed (dynamically, here) to occur in current dictionary
		for raw_word in self.available_words:
			for lidx in range(len(raw_word)):
				
				key=self.upper_uchar(raw_word[lidx])
				try:dummy=self.game.global_config['letters'].index(key)
				except Exception,e:#things like semi-colons and commas...
					#print 'line 381 tws_solver;',e
					continue
				
				if distro.has_key(key):
					distro[key]+=1
				else:
					distro[key]=1
		
		if DEBUG:print distro
		
		ctot=0
		for key in distro.keys():
			ctot+=distro[key]
		
		if DEBUG:print "\n\nctot=%d\n\n"%ctot
		
		msg="Computing scoring scheme..."
		self.game.progress_message(msg)
		
		nmax=1
		nmin=100000000
		for key in distro.keys():
			distro[key]=max(1,int(self.game.global_config['tiles_ntot']*float(distro[key])/float(ctot)))
			if distro[key]>nmax:nmax=distro[key]
			if distro[key]<nmin:nmin=distro[key]
		
		for key in distro.keys():
			self.game.global_config['distribution'][key]=max(1,distro[key])
			#make scoring inversly propto frequency of occurance; use z,q as realative ref points.
		
		ttot=0
		for key in 	self.game.global_config['distribution'].keys():
			ttot+=self.game.global_config['distribution'][key]
		
		if DEBUG:print self.game.global_config['distribution']
		if DEBUG:print "\n\nttot=%d\n\n"%ttot
		
		#Now identify score of each tile to use:
		nrange=nmax-nmin
		nmax_score=self.game.global_config['tile_max_val_possible']
		nmin_score=self.game.global_config['tile_min_val_possible']
		
		for key in distro.keys():
			letter=self.get_unidesc_field(key,'VALUE')
			mod=self.get_unidesc_field(key,'MOD')
			if mod==None:mod='NOMOD'
			gc_scoring_key="%s_%s"%(letter,mod)
			f_i=distro[key]#relative frequency
			F_tot=nmax
			self.game.global_config['scoring'][gc_scoring_key]=max(1,int(1.+nmax_score-(nrange-1)*float(f_i)/float(F_tot)))
			if DEBUG:print "%s: val=%d ntile=%d"%(gc_scoring_key,self.game.global_config['scoring'][gc_scoring_key],distro[key])
		
	def build_ntuple(self):
			
			
			if self.game.global_config['use_default_dist']==0:
				self.make_special_chars()
				self.make_normalized_distro()
			
			if DEBUG:print 'self.special_chars=',self.special_chars
			if DEBUG:print 'self.game.global_config[\'letters\']=',self.game.global_config['letters']
				
			self.ntuple={}
			
			#French dictionary has 15 special characters
			#distro=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			distro=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			
		
			ouf=open('distro.dat','w')
			
			indices_to_remove=[]
			
			for idx in range(len(self.available_words)):
				
				if math.fmod(idx,1000)==0:
					msg="\rBuilding ntuple...%d%s"%(int(100.*float(idx)/float(len(self.available_words))),"%")
					print msg,
					#self.game.progress_message(msg)

				raw_word=self.available_words[idx]
				
				raw_first_word=None
				parenthesis_idx=None
				
				try:parenthesis_idx=raw_word.index(')')
				except:
					#if DEBUG:print 'no parenthesis'
					pass
					
				if parenthesis_idx:
					raw_first_word=string.split(raw_word[parenthesis_idx+1:],' ')[0]
				else:
					raw_first_word=string.split(raw_word,' ')[0]
				
				cap_uniword=u''
				for lidx in range(len(raw_first_word)):
					if raw_first_word[lidx]==';':continue
					if raw_first_word[lidx]=='!':continue
					if raw_first_word[lidx]=='.':continue
					if raw_first_word[lidx]==',':continue
					cap_uniword+=self.upper_uchar(raw_first_word[lidx])
					
				encoded_word=unicode(cap_uniword).encode("iso-8859-1")
				uc_encoded_word=string.upper(encoded_word)
				
				
				fp_list=self.mkfingerprint(cap_uniword)
				
				if not fp_list:
					#if DEBUG:print 'no fp_list so skipping: ',uc_encoded_word
					indices_to_remove.append(idx)
					
					#if DEBUG:print string.split(uc_encoded_word,' ')
					
					#rval=raw_input('q?')
					#if rval=='q':sys.exit()
					continue
				
				fp_num=self.mkfp_num(fp_list)
				
				if self.ntuple.has_key(fp_num):
					
					self.ntuple[fp_num]['article_lookup_keys'].append(raw_word)
					self.ntuple[fp_num]['identical_letter_content'].append(cap_uniword)
					
					#rval=raw_input('q?')
					#if rval=='q':sys.exit()
					
				else:
					
					fp_sum=self.mkfp_sum(fp_list)
					scrabble_sum=self.get_scrabble_sum(fp_list)
							
					self.ntuple[fp_num]={
						'article_lookup_keys':[raw_word],
						'identical_letter_content':[cap_uniword],
						'fp_sum':fp_sum,
						'scrabble_sum':scrabble_sum,
						'fp_list':fp_list,
					}
					
					#if DEBUG:print self.ntuple[fp_num]
					
				#print "%s\t%s"%(self.available_words[idx],fingerprint)
				for lidx in range(len(distro)):
					distro[lidx]+=fp_list[lidx]
					if fp_list[lidx]>0:
						#for dummy in range(fp_list[lidx]):
						line="%d\n"%(lidx+3)
						ouf.write(line)
						#if lidx>25:print line
				
							
				#rval=raw_input('next?')
				#if rval=='q':sys.exit()
			
			#make ntuple:
			#ouf.write(`distro`)
			ouf.close()
			"""
			ntouf=open('ntuple.dat','w')
			line=">key\tnum_words\tfp_sum\tscrabble_sum\n"
			ntouf.write(line)
			
			sorted_keys=self.ntuple.keys()
			sorted_keys.sort()
			for kidx in range(len(sorted_keys)):
				
				line="%s\t%d\t%d\t%d\n"%(sorted_keys[kidx],len(self.ntuple[sorted_keys[kidx]]['identical_letter_content']),self.ntuple[sorted_keys[kidx]]['fp_sum'],self.ntuple[sorted_keys[kidx]]['scrabble_sum'])
				ntouf.write(line)
	
			ntouf.close()
			
			ouf=open('ntuple_oxford.dat','w')
			ouf.write(`self.ntuple`)
			ouf.close()
			"""
			
			msg="Removing odd-ball entries..."
			self.game.progress_message(msg)
		
			indices_to_remove.reverse()
			if DEBUG:print 'len(indices_to_remove)=',len(indices_to_remove)
			for ridx in range(len(indices_to_remove)):
				self.available_words.pop(indices_to_remove[ridx])
				
			
	def mkfingerprint(self,word):
		
		
		fingerprint=[]
		for idx in range(len(self.game.global_config['letters'])):
			fingerprint.append(0)
		
		#rval=raw_input('?')
		#if rval=='q':sys.exit()
		
		for idx in range(len(word)):
			try:fingerprint[self.game.global_config['letters'].index(word[idx])]+=1
			except Exception,e:
				return None
				
		return fingerprint
		

	def get_installed(self):
		
		msg="Examining installed resources..."
		self.game.progress_message(msg)
		
		if DEBUG:print 'get_installed',sys.argv
		
		self.fullnames_targets={}
		#dnames=os.listdir(os.path.join(self.parent.env.configdir,'xdxf'))
		dnames=os.listdir('xdxf')
		
		#progress bar:
		pb=None
		for d in dnames:
			
			target=os.path.join('xdxf',d,'dict.xdxf')
			if not os.path.exists(target):continue
			if DEBUG:print target
			inf=open(target)
			dh=GetFieldContent('full_name')
			parser.setContentHandler(dh)
			parser.parse(inf)
			inf.close()
			if dh.rval:
				
				self.fullnames_targets[dh.rval]=target
				if DEBUG:print dh.rval
				
				msg="Examining installed resources...%s"%(dh.rval)
				self.game.progress_message(msg)

		if pb:del pb
		return self.fullnames_targets.keys()

	def load_resource(self):	
		
		target=self.current_resource_path
		if not target:return

		msg="Loading configured resource: %s"%(self.current_resource_key)
		self.game.progress_message(msg)
		
		if DEBUG:print 'load_resource'
		inf=open(target)
		dh=GetKeys('ALL')#self.current_letter
		parser.setContentHandler(dh)
		parser.parse(inf)
		inf.close()
		self.available_words=dh.keys
		self.key_count=dh.key_count
		
		#self.alb_contents=self.available_words
		#self.albCB(None)
		
		if DEBUG:print 'load_resource calling build_ntuple...'
		if not self.ntuple:self.build_ntuple()#NEED:Save ntuple across sessions
		
		if DEBUG:print 'load_resource done'
	
	
	
	def identify_wc_options_on_board(self):
		#getting away from brute force techniques...
		pass
	
	def get_candidates(self,fp_list,min_wc,max_wc,max_delta):
		
		ntuple=self.ntuple
		candidates=[]
		
		#get wc_candidates with only 1 bit toggled:
		keys=ntuple.keys()
		if DEBUG:print "get_candidates: checking %d records"%len(keys)
		
		for key in keys:
		
			wc_list,delta=self.compute_delta(ntuple[key]['fp_list'],fp_list)
			if len(wc_list)<min_wc:continue
			if len(wc_list)>max_wc:continue
			if len(wc_list)>max_delta:continue
			if (delta-len(wc_list))<=max_delta:
				fp_sum=self.mkfp_sum(self.ntuple[key]['fp_list'])
				scrabble_sum=self.get_scrabble_sum(self.ntuple[key]['fp_list'])
				words=ntuple[key]['identical_letter_content']
				article_lookup_keys=ntuple[key]['article_lookup_keys']
				
				if DEBUG:print 'get_candidates: ',words,type(words[0])
				word_list=[]
				key_list=[]
				for idx in range(len(words)):
					word_list.append(words[idx])
					key_list.append(article_lookup_keys[idx])
					
				candidates.append((key,word_list,wc_list,delta-len(wc_list),fp_sum,scrabble_sum,key_list))
				
				
		#sort by scrabble_sum
		for idx0 in range(len(candidates)):
			for idx1 in range(idx0,len(candidates)):
				if candidates[idx1][5]>candidates[idx0][5]:
					tmp1=candidates.pop(idx1)
					tmp0=candidates.pop(idx0)
					candidates.insert(idx0,tmp1)
					candidates.insert(idx1,tmp0)
					
		return candidates
	
	def compute_delta(self,L0,L1):
		delta=0
		fp_diff=self.subtract_fp0_from_fp1(L0,L1)
		delta=0
		wc_list=[]
		for idx in range(len(self.game.global_config['letters'])):
			if fp_diff[idx]>=0:
				delta+=fp_diff[idx]
			else:
				delta+=abs(fp_diff[idx])
				for xidx in range(abs(fp_diff[idx])):
					wc_list.append(self.game.global_config['letters'][idx])
		return wc_list,delta
		
	def subtract_fp0_from_fp1(self,fp0,fp1):
		fp=[]
		for idx in range(len(self.game.global_config['letters'])):
			val=fp1[idx]-fp0[idx]
			fp.append(val)
			#if val<0:print 'val=',val
		
		return fp

	def subtract_strfp0_from_strfp1(self,fp0,fp1):
		fp=[]
		if len(fp0)!=len(fp1):
			if DEBUG:print "ERROR: lists not same length!!"
		for idx in range(len(fp1)):
			
			try:v1=eval(fp1[idx])
			except:v1='--'
			try:v0=eval(fp0[idx])
			except:v0='--'
			
			val=999
			if v0=='--' and v1=='--':val=0
			elif (v0=='--' or v1=='--'):val=-1
			else:val=v1-v0
			
			if val!=0:return None
			
			#print "%s-%s=%d"%(fp1[idx],fp0[idx],val)
			fp.append(val)
		
		return fp
			
			
	def mkfp_num(self,fp_list):
		fp_num=""
		for idx in range(len(fp_list)):
			if fp_list[idx]<0:return None
			fp_num="%s%c"%(fp_num,str(fp_list[idx]))#00102030001002
		return fp_num

	def get_scrabble_sum(self,fp_list):
		
		gc=self.game.global_config
		scrabble_sum=0
		
		#build pyld for score calculation:
		score_pyld={
			'double_letter':0,
			'double_word':0,
			'tripple_letter':0,
			'tripple_word':0,
		}
		
		for cidx in range(len(fp_list)):#ordering of fp_list == ordering of gc['letters']
			
			uchar=gc['letters'][cidx]
			letter=self.get_unidesc_field(uchar,'VALUE')
			mod=self.get_unidesc_field(uchar,'MOD')
			if not mod:mod='NOMOD'
			gc_scoring_key="%s_%s"%(letter,mod)
			
			score=gc['scoring'][gc_scoring_key]
			#print letter,score
			scrabble_sum+=fp_list[cidx]*score
		
		return scrabble_sum
	
	def mkfp_sum(self,fp_list):
		fp_sum=0
		for cidx in range(len(fp_list)):fp_sum+=fp_list[cidx]
		return fp_sum
		
	def generate_expressions(self):
		
		if DEBUG:print 'tms_solver: generate_expressions'
		#self.game.handle_mouse()
		#if self.game.STOP_RUNNING!=0:return None
		
		#print the contents of the tray:
		self.tray=self.game.players[self.game.player_idx].tray
		if DEBUG:print 'self.game.player_idx=',self.game.player_idx
		if DEBUG:print self.tray.get_word_map()
		
		#self.game.handle_mouse()
		#if self.game.STOP_RUNNING!=0:return None
	
	
	def generate_options(self):
		
		tray_map=self.tray.get_word_map()
		word=u''
		for idx in range(len(tray_map[0])):
			#print type(tray_map[0][idx])
			word+=tray_map[0][idx]
		
		fp_list=self.mkfingerprint(word)
		fp_num=self.mkfp_num(fp_list)
		
		if DEBUG:print 'tray word: ',word.encode('latin1')
		if DEBUG:print 'tray word fp_list=',fp_list
		if DEBUG:print 'tray word fp_num=',fp_num
		
		
		if DEBUG:print 'tws_solver: generate_options'
		gc=self.game.global_config
		
		if self.game.board.num_committed==0:		
			
			max_delta=5
			min_wc=0
			max_wc=0
			
			self.candidates=self.get_candidates(fp_list,min_wc,max_wc,max_delta)
			if len(self.candidates)==0:return None
			
			
			for idx in range(len(self.candidates)):
				if DEBUG:print self.candidates[idx]
				
				rlist=[]
			
				word=self.candidates[idx][1][0]#words
				if DEBUG:print 'trying candidate: ',unicode(word).encode('latin1')
				
				for lidx in range(len(word)):
					
					uchar=word[lidx]
					letter=self.get_unidesc_field(uchar,'VALUE')
					mod=self.get_unidesc_field(uchar,'MOD')
					if not mod:mod='NOMOD'
					gc_scoring_key="%s_%s"%(letter,mod)
					
					rlist.append([gc_scoring_key,int(gc['M']/2),int(gc['N']/2-len(word)/2+lidx)])
				
				"""
				#041507: b/c introduced boardmap, now letting game do scoring based on rlist
				if DEBUG:print 'score=',self.candidates[idx][5]
				if self.game.tuxturn:
					self.game.players[0].score+=self.candidates[idx][5]
				else:
					self.game.players[1].score+=self.candidates[idx][5]
				"""
				
				if DEBUG:print 'calling get_article: ',self.candidates[idx][1][0].encode('latin1')
				#last_article=self.get_article(self.candidates[idx][1][0].encode('latin1'))
				last_article=self.get_article_via_article_lookup_key(self.candidates[idx][6][0])
				
				if string.find(last_article['content'],'abbr.')>=0:continue
				#print 'last_article[content]=',last_article['content']
				
				
				if not last_article['key']:
					if DEBUG:print 'received key=',last_article['key'],' continuing...'
					continue#fragile; based on abbrv all caps
					
				msg="%s: %s"%(self.candidates[idx][6][0].encode('latin1'),last_article['content'].encode('latin1'))
				self.game.set_last_defn(msg)
				if DEBUG:print msg
				
				#rval=raw_input('proceed?')
				#if rval=='q':sys.exit()
				
				return rlist
			
		else:
			min_wc=1#NEED:These thresholds from config
			max_wc=1
			if self.game.board.num_committed==1:max_wc=1
			elif self.game.board.num_committed==2:max_wc=1
			elif self.game.board.num_committed==3:max_wc=2
			elif self.game.board.num_committed==4:max_wc=2
			elif self.game.board.num_committed==5:max_wc=3
			elif self.game.board.num_committed==6:max_wc=3
			else:max_wc=3
			max_delta=4
			
			self.candidates=self.get_candidates(fp_list,min_wc,max_wc,max_delta)
			
			#NEED:use WCs
			#sort words by scrabble_sum
			#do this in get_candidates() --DONE
			
			#loop over sorted words
			for idx in range(len(self.candidates)):
			  
			  #if math.fmod(idx,100)==0:self.game.queue_thinking_maneuver()
			  
			  for widx in range(len(self.candidates[idx][1])):#loop over words with identical letter content (all with same candidate fingerprint)
				
				if DEBUG:print "%d\r"%(idx),
				
				#determine WC fingerprint
				word2fit=self.candidates[idx][1][widx]
				wc_list=self.candidates[idx][2]
				fp_candidate=self.mkfingerprint(word2fit)
				fp_idx_candidate=self.mkidxfingerprint(word2fit,wc_list)
				fp_wcidx_candidate=self.mkwcidxfingerprint(word2fit,wc_list)
				#print 'fp_idx_candidate=',fp_idx_candidate
				#print 'fp_wcidx_candidate=',fp_wcidx_candidate
				
				#board search for fp_wcidx_candidate
				idx_map=self.game.board.get_idx_map(gc['letters'])
				
				#FITROW 
				for midx in range(len(idx_map)):
					for nidx in range(0,len(idx_map[0])-len(fp_wcidx_candidate)):
						
						board_list=[]
						for fp_idx in range(0,len(fp_wcidx_candidate)):
							board_list.append(idx_map[midx][nidx+fp_idx])
							
						#print 'subtracting:',board_list,fp_wcidx_candidate
						fp_diff=self.subtract_strfp0_from_strfp1(board_list,fp_wcidx_candidate)
						if not fp_diff:continue
						#print 'fp_diff=',fp_diff
						
						all_zeros=True
						for fp_diff_idx in range(len(fp_diff)):
							if fp_diff[fp_diff_idx]!=0:all_zeros=False
							
						if all_zeros:
							
							rlist=[]
							for lidx in range(len(word2fit)):
								#if board_list[lidx]=='--':
								if True:
									uchar=word2fit[lidx]
									letter=self.get_unidesc_field(uchar,'VALUE')
									mod=self.get_unidesc_field(uchar,'MOD')
									if not mod:mod='NOMOD'
									gc_scoring_key="%s_%s"%(letter,mod)
																		
									rlist.append([gc_scoring_key,midx,nidx+lidx])
							
							#NEED:check neighborhood
							rval=self.check_row_neighborhood(midx,nidx,word2fit,fp_wcidx_candidate,idx_map)
							if not rval:continue
							
							for cidx in range(len(self.candidates)):
								if DEBUG:print self.candidates[cidx]
							
							#last_article=self.get_article(word2fit)
							last_article=self.get_article_via_article_lookup_key(self.candidates[idx][6][widx])
							
							if not last_article['key']:continue#fragile; based on abbrv all caps
							
							if string.find(last_article['content'],'abbr.')>=0:continue
							#print 'last_article[content]=',last_article['content']
	
							msg='word2fit: unavailable'
							try:msg="%s: %s"%(self.candidates[idx][6][widx].encode('latin1'),last_article['content'].encode('latin1'))
							except Exception,e:
								if DEBUG:print 'unicode/ascii problem with article',e
								
							self.game.set_last_defn(msg)
							if DEBUG:print msg
							
							#rval=raw_input('proceed?')
							#if rval=='q':sys.exit()
							
							"""
							if DEBUG:print 'score=',self.candidates[idx][5]
							if self.game.tuxturn:
								self.game.players[0].score+=self.candidates[idx][5]
							else:
								self.game.players[1].score+=self.candidates[idx][5]
							"""
							
							return rlist
							
								
				#FITCOL
				for midx in range(0,len(idx_map)-len(fp_wcidx_candidate)):
					for nidx in range(len(idx_map[0])):
						
						board_list=[]
						for fp_idx in range(0,len(fp_wcidx_candidate)):
							board_list.append(idx_map[midx+fp_idx][nidx])
						
						#print 'subtracting:',board_list,fp_wcidx_candidate
						fp_diff=self.subtract_strfp0_from_strfp1(board_list,fp_wcidx_candidate)
						if not fp_diff:continue
						#print 'fp_diff=',fp_diff
						
						all_zeros=True
						for fp_diff_idx in range(len(fp_diff)):
							if fp_diff[fp_diff_idx]!=0:all_zeros=False
							
						if all_zeros:
							
							rlist=[]
							for lidx in range(len(word2fit)):
								#if board_list[lidx]=='--':
								if True:
										
									uchar=word2fit[lidx]
									letter=self.get_unidesc_field(uchar,'VALUE')
									mod=self.get_unidesc_field(uchar,'MOD')
									if not mod:mod='NOMOD'
									gc_scoring_key="%s_%s"%(letter,mod)
																		
									rlist.append([gc_scoring_key,midx+lidx,nidx])
							
							#NEED:check neighborhood
							rval=self.check_col_neighborhood(midx,nidx,word2fit,fp_wcidx_candidate,idx_map)
							if not rval:continue

							
							
							
							for cidx in range(len(self.candidates)):
								if DEBUG:print self.candidates[cidx]
							
							if DEBUG:print "%d/%d %s %d"%(idx,len(self.candidates),word2fit.encode('latin1'),self.candidates[idx][5])
							if DEBUG:print rlist
							
							#last_article=self.get_article(word2fit)
							last_article=self.get_article_via_article_lookup_key(self.candidates[idx][6][widx])
							
							if not last_article['key']:continue#fragile; based on abbrv all caps

							if string.find(last_article['content'],'abbr.')>=0:continue
							#print 'last_article[content]=',last_article['content']

							msg="%s: %s"%(self.candidates[idx][6][widx].encode('latin1'),last_article['content'].encode('latin1'))
							self.game.set_last_defn(msg)
							if DEBUG:print msg
							
							#rval=raw_input('proceed?')
							#if rval=='q':sys.exit()
							"""
							if DEBUG:print 'score=',self.candidates[idx][5]
							if self.game.tuxturn:
								self.game.players[0].score+=self.candidates[idx][5]
							else:
								self.game.players[1].score+=self.candidates[idx][5]
							"""
							return rlist
							
							
			
		
			return None

	def check_row_neighborhood(self,m,n,word,fp_wcidx_candidate,idx_map):
		rval=True
		
		#endpoints:
		if n>0:
			if idx_map[m][n-1]!='--':return False
		
		if (n+len(word))<len(idx_map[m]):
			if idx_map[m][n+len(word)]!='--':return False
		
		#check above
		if m>0:
			for nidx in range(n,n+len(word)):#-1
				if (idx_map[m-1][nidx]!='--' and fp_wcidx_candidate[nidx-n]=='--'):return False
		
		#check below
		if m<len(idx_map)-1:
			for nidx in range(n,n+len(word)):#-1
				if (idx_map[m+1][nidx]!='--' and fp_wcidx_candidate[nidx-n]=='--'):return False
		
		return rval
	
	def check_col_neighborhood(self,m,n,word,fp_wcidx_candidate,idx_map):
		rval=True
		
		#endpoints:
		if m>0:
			if idx_map[m-1][n]!='--':return False
		
		if (m+len(word))<len(idx_map):
			if idx_map[m+len(word)][n]!='--':return False
		
		#check left
		if n>0:
			for midx in range(m,m+len(word)):#-1
				if (idx_map[midx][n-1]!='--' and fp_wcidx_candidate[midx-m]=='--'):return False

		#check right
		if n<len(idx_map[0])-1:
			for midx in range(m,m+len(word)):#-1
				if (idx_map[midx][n+1]!='--' and fp_wcidx_candidate[midx-m]=='--'):return False

		return rval

	def mkidxfingerprint(self,word,wc_list):
		if DEBUG:print 'mkidxfingerprint: ',type(word),type(wc_list[0])
		if DEBUG:print `word`,`wc_list`
		letters=self.game.global_config['letters']
		idxfingerprint=[]
		for widx in range(len(word)):
			WC=False
			letter=word[widx]
			for wcidx in range(len(wc_list)):
				if letter==wc_list[wcidx]:WC=True
			
			if 0:pass#WC:	idxfingerprint.append("WC:%c"%letters.index(letter))
			else:idxfingerprint.append(letters.index(letter))					
		
		return idxfingerprint
							
	def mkwcidxfingerprint(self,word,wc_list):
		letters=self.game.global_config['letters']
		wcidxfingerprint=[]
		for widx in range(len(word)):
			WC=False
			letter=word[widx]
			for wcidx in range(len(wc_list)):
				if letter==wc_list[wcidx]:WC=True
			
			if WC:	wcidxfingerprint.append("%2d"%letters.index(letter))
			else:wcidxfingerprint.append('--')					
		
		return wcidxfingerprint

	def construct_submission(self,lhs_expressions,rhs_expressions):
		pass

	def lower_uchar(self,uchar):
		
		uchar_name=None
		
		try:uchar_name=unicodedata.name(uchar)
		except Exception,e:
			
			print e,type(uchar),uchar.encode('latin1')
			
			rval=raw_input('q?')
			if rval=='q':sys.exit()
			
			return uchar
		
		modified_uchar_name=string.replace(uchar_name,'CAPITAL','SMALL')
		modified_uchar=unicodedata.lookup(modified_uchar_name)
		return modified_uchar
	
	def upper_uchar(self,uchar):
		
		uchar_name=None
		
		try:uchar_name=unicodedata.name(uchar)
		except Exception,e:
			#print e,uchar,uchar.encode('latin1')
			return uchar
		
		modified_uchar_name=string.replace(uchar_name,'SMALL','CAPITAL')
		
		momdified_uchar=None
		try:
			modified_uchar=unicodedata.lookup(modified_uchar_name)
		
		except Exception,e:
			if DEBUG:print e
			return None
		
		return modified_uchar
	
	def get_article_via_article_lookup_key(self,article_lookup_key):
		dh=GetArticle(article_lookup_key)
		parser.setContentHandler(dh)
		inf=open(self.current_resource_path)
		parser.parse(inf)
		inf.close()
		return dh.article
	
	
	
	def get_article(self,target):
		
		#Some xdxf dicts have words all lower case, some capitalized first letter:
		#IMPORTANT: the target came from the dict, so it's there!! This func needs to retrieve SOMEHOW...
		
		cap_first=False
		
		if 0:pass
		elif self.current_resource_key=='German-English dictionary':cap_first=True
		elif self.current_resource_key=='Oxford (En)':cap_first=True
		
		if cap_first==True:
			
			if DEBUG:print 'cap_first=True'
			
			mtarget=u''
			try:mtarget+=self.lower_uchar(unicode(target[0]))
			except Exception,e:
				if DEBUG:print 'fist letter...',`target[0]`,type(target[0]),type(unicode(target[0])),e,' trying again...'
				try:
					mtarget+=self.lower_uchar(target[0])
					if DEBUG:print 'okay'
				except:
					rval=raw_input('nope! capitalizing first letter failed: hit enter to return None')
					if rval=='q':sys.exit()
			
			for idx in range(1,len(target)):
				try:mtarget+=self.lower_uchar(unicode(target[idx]))
				except:
					print 'get_article failes 1x: ',`target[idx]`,type(target[idx]),`mtarget`,type(target),`target`
					try:
						mtarget+=self.lower_uchar(target[idx])
					except:
						rval=raw_input('get_article failed 2x: hit enter to return None')
						if rval=='q':sys.exit()
			
			if DEBUG:print 'trying to get target article = ',mtarget.encode('latin1')
			dh=GetArticle(mtarget)
			parser.setContentHandler(dh)
			inf=open(self.current_resource_path)
			parser.parse(inf)
			inf.close()
			if dh.article['content']:return dh.article
			else:
				if DEBUG:print'failed for mtarget=',mtarget.encode('latin1')
				
		
		if DEBUG:print 'using cap_first=False'
		
		mtarget=u''
		for idx in range(0,len(target)):
			try:mtarget+=self.lower_uchar(unicode(target[idx]))
			except:
				print 'get_article failes 1x: ',`target[idx]`,type(target[idx]),`mtarget`,type(target),`target`
				try:
					mtarget+=self.lower_uchar(target[idx])
				except:
					rval=raw_input('get_article failed 2x: hit enter to return None')
					if rval=='q':sys.exit()
		
		if DEBUG:print 'trying to get target article = ',mtarget.encode('latin1')
		dh=GetArticle(mtarget)
		parser.setContentHandler(dh)
		inf=open(self.current_resource_path)
		parser.parse(inf)
		inf.close()
		return dh.article
