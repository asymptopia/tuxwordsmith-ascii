#!/usr/bin/python
"""
/***************************************************************************

        Author                  :Charles B. Cosse 
        
        Email                   :ccosse@gmail.com
                                        
        Website                 :www.asymptopia.org
        
        Copyright               :(C) 2002-2007 Asymptopia Software.
        
 ***************************************************************************/
"""

"""
	December 27, 2006: V0.0.0
	Ascii version of TuxWordSmith. This version is simplified.
	All files are contained in a single directory to make the programming easier.
	
	April 15, 2007: V0.1.0
	Major changes throughout. plays similar to scrabble now. 
	Scoring and letter distribution are the major differences.

	April 16, 2007: V0.1.1
	
	April 17, 2007: V0.1.2
	
	May 13, 2007:V0.1.3
"""

import os,sys,math,string,unicodedata
from random import random

from board import *
from player import *
from letters import *
from tile import *
from tws_solver import *
from tws_validator import *
from tws_localizer import *

DEBUG=True
DEBUG=False

class TWS_ASCII:
	def __init__(self):
		
		infname='config'
		inf=open(infname)
		self.global_config=eval(inf.read())
		inf.close()
		
		if self.global_config['show_help_at_startup']==1:self.usage()
		
		solver=TWS_Solver(self)
		self.localizer=None
		self.validator=None

		self.players=[]
		for idx in range(2):
			tray=Board(1,self.global_config['NTRAYSPOTS'],[['-','-','-','-','-','-','-']],1)
			p=Player(idx,tray,solver)
			self.players.append(p)
		
		self.player_idx=0
		self.bag_of_tiles=[]
		self.submission=None
		self.submissionspots=None
		self.target=None
		self.tuxturn=0
		
		self.words_used=[]
		self.last_defn=''
		self.CLR_CMD=os.system('clear')
		
		rval=0
		while rval>=0:
			rval=self.play(0)

	def pause(self):
		print '\n\n'
		print 'press enter to proceed\n'
		rval=raw_input('')
	
	def progress_message(self,msg):
		print msg
	
	def set_current_resource(self,msg):
		print msg
	
	def set_last_defn(self,msg):
		#print msg
		self.last_defn=msg
				
	def show_definition(self):
		#os.system('clear')
		if len(self.words_used)==0:return
		for idx in range(len(self.words_used)):
			print "%2d) %s"%(idx,self.words_used[idx]['key'])
		
		choice=None
		idx=None
		while 1:
			choice=raw_input('choice? ')
			try:
				idx=eval(choice)
				break
			except:return
		
		msg="Score received:%d\n%s\n%s\n"%(self.words_used[idx]['score'],self.words_used[idx]['key'],self.words_used[idx]['definition'])
		print msg	
		self.pause()

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

	def refill_bag_of_tiles(self):
		
		if DEBUG:print 'refil bag_of_tiles'
		
		gc=self.global_config
		distribution=gc['distribution']
		
		for idx in range(len(Letters)):
			letter=Letters[idx]
			ncopy=distribution[string.upper(letter)]
			for dummy in range(ncopy):
				uchar=unicode(Letters[idx])
				letter=self.get_unidesc_field(uchar,'VALUE')
				mod=self.get_unidesc_field(uchar,'MOD')
				if mod==None:mod='NOMOD'
				
				#gc_scoring_key="%s_%s"%(letter,mod)
				#score=gc['scoring'][gc_scoring_key]
				
				#fname="%s%s_%s_%02d.jpeg"%(gc['player_tile_prefix'],letter,mod,score)
				#fpath=os.path.join(gc['imgdir'],fname)
				
				#if DEBUG:print fpath
				#ptval=self.scoring[gc_scoring_key]
				l_mod=None
				#str_val=gc_scoring_key
				
				tile=Tile(idx,l_mod,letter,letter,1)
				self.bag_of_tiles.append(tile)
				
		
		#shuffle
		for nshuffle in range(10000):
			tile=self.bag_of_tiles.pop()
			idx2insert=int(random()*len(self.bag_of_tiles))
			self.bag_of_tiles.insert(idx2insert,tile)
		
		if DEBUG:print 'len(self.bag_of_tiles)=',len(self.bag_of_tiles)
		if DEBUG:print self.bag_of_tiles
		
	def exchange(self,sequence):
		if DEBUG:print 'exchange:',sequence
		spots=self.players[self.player_idx].tray.get_spots()
		
		
		for idx in range(len(sequence)):
			target=string.upper(sequence[idx])
			for spot in spots:
				if not spot.occupied():continue#shouldn't happen
				
				print spot.guest.uchar.encode('latin1'),target,spot.guest.uchar.encode('latin1')==target
				
				if spot.guest.uchar.encode('latin1')==target:
					tile=spot.pop_guest()
					self.bag_of_tiles.insert(0,tile)
					break#spot loop
					
		self.draw_tiles()
		
	def swap_tiles_lt(self,swap_val):
		
		spots=self.players[self.player_idx].tray.get_spots()
		
		for spot in spots:
			if not spot.occupied():continue#shouldn't happen
			if self.global_config['scoring'][spot.guest.uchar]<=swap_val:
				tile=spot.pop_guest()
				self.bag_of_tiles.insert(0,tile)
		
		self.draw_tiles()
			
	def draw_tiles(self):
		
		gc=self.global_config
		
		for plyr_idx in range(2):
		  spots=self.players[plyr_idx].tray.get_spots()
		  for spot in spots:
			
			if len(self.bag_of_tiles)==0:self.refill_bag_of_tiles()
		
			if spot.occupied():continue
			
			#HACK 120406:if Eng-Any dictionary resource, then don't draw special characters! (still need them to work with defn's though)
			avoid_special_chars=False
			if self.players[plyr_idx].solver.current_resource_key.encode('latin1')[0:3]=='eng':avoid_special_chars=True
			elif self.players[plyr_idx].solver.current_resource_key.encode('latin1')[0:3]=='osf':avoid_special_chars=True
			elif self.players[plyr_idx].solver.current_resource_key.encode('latin1')[0:3]=='Eng':avoid_special_chars=True
			
				
			common_letters=[u'A',u'B',u'C',u'D',u'E',u'F',u'G',u'H',u'I',u'J',u'K',u'L',u'M',u'N',u'O',u'P',u'Q',u'R',u'S',u'T',u'U',u'V',u'W',u'X',u'Y',u'Z']
			tile=None
			while True:
				
				tile=self.bag_of_tiles.pop()
				
				if DEBUG:print 'drawing tiles: ',tile.uchar.encode('latin1')
				
				if avoid_special_chars:
					try:
						lidx=common_letters.index(tile.uchar)
						break
					except:
						self.bag_of_tiles.insert(0,tile)
				
				else:break
					
			spot.take_guest(tile,1)
			
		
	
	def usage(self):
		lines=[]
		lines.append("\n")
		lines.append("          TuxWordSmith --- ASCII Version\n")

		lines.append("     AsymptopiaSoftware | Software@theLimit\n")

		lines.append("               www.asymptopia.org   \n")

		lines.append("                 Version 0.1.2    \n")

		lines.append("                 April 16, 2007   \n\n")
		
		
		lines.append("syntax: [action] <type> <row> <column> <word>")
		lines.append("action:  move, skip, help, defn, tb, lookup, dist, scoring, quit\n")
		
		lines.append("skip    = skip turn")
		lines.append("help    = show this help screen")
		lines.append("defn    = show list of available definitions")
		lines.append("tb      = toggle boardmap")
		lines.append("lookup  = lookup word in dictionary")
		lines.append("dist    = show letter frequency distribution")
		lines.append("scoring = show letter scoring scheme")
		lines.append("exchange= exchange tiles and sacrifice turn")
		lines.append("          example: exchange abc")
		lines.append("\n")		
		lines.append("boardmap scheme: ")
		lines.append("\t1 - double letter")
		lines.append("\t2 - double word")
		lines.append("\t3 - tripple letter")
		lines.append("\t4 - tripple word")
		lines.append("\n")		
		lines.append("type = r or c (row or col)")
		
		#lines.append("row        = number in range 0-%s specifying starting row of word entry"%str(self.global_config['M']-1))
		#lines.append("col        = number in range 0-%s specifying starting column of word entry"%str(self.global_config['N']-1))
		#lines.append("word       = complete word including letters already on board intended to be reused")
		lines.append("\n")
		for idx in range(len(lines)):
			print lines[idx]
		
	def lookup(self):
		word=raw_input('word: ')
		article=self.players[self.player_idx].solver.get_article(word)
		msg="%s: %s"%(unicode(word).encode('latin1'),unicode(article['content']).encode('latin1'))
		print msg,'\n'
		
	def scoring(self):
		gc=self.global_config
		if DEBUG:print gc['scoring']
		if DEBUG:print gc['scoring'].keys()
		for lidx in range(len(gc['letters'])):
			lval="%c_NOMOD"%(gc['letters'][lidx].encode('latin1'))
			lval=unicode(lval)
			print "%c %2d"%(string.upper(gc['letters'][lidx].encode('latin1')),gc['scoring'][lval])
		print '\n'
		"""
		for lidx in range(len(Letters)):
			lval="%c_NOMOD"%(string.upper(Letters[lidx].encode('latin1')))
			print "%c %2d"%(string.upper(Letters[lidx].encode('latin1')),self.global_config['scoring'][lval])
		print '\n'
		"""
		
	def dist(self):
		gc=self.global_config
		if DEBUG:print gc['distribution']
		for lidx in range(len(gc['letters'])):
			print "%c %2d %s"%(string.upper(gc['letters'][lidx].encode('latin1')),gc['distribution'][gc['letters'][lidx]],gc['distribution'][gc['letters'][lidx]]*"*")
		print '\n'
		"""
		for lidx in range(len(Letters)):
			print "%c %2d %s"%(string.upper(Letters[lidx].encode('latin1')),self.global_config['distribution'][Letters[lidx]],self.global_config['distribution'][Letters[lidx]]*"*")
		print '\n'	
		"""
		
	def handle_input(self):
		rval=raw_input('>')
		rlist=[]
		
		while rlist.count('  ')>0:
			rlist=string.replace(rlist,'  ',' ')
		srval=string.split(rval,' ')

		#if len(srval)<5:return rlist
		if srval[0]=='move' and len(srval)>=5:
			R_OR_C=srval[1]
			if R_OR_C=='r':R_OR_C='R'
			elif R_OR_C=='c':R_OR_C='C'
			R=srval[2]
			C=srval[3]
			word=list(srval[4])
			
			#rlist= [['B_NOMOD', 0, 0], ['I_NOMOD', 0, 1], ['G_NOMOD', 0, 2]]
			
			for idx in range(0,len(word)):
				if DEBUG:print word[idx]
				lookup_key="%s"%(string.upper(word[idx]))
				if R_OR_C=='R':
					rlist.append([lookup_key,int(R),int(C)+idx])
				elif R_OR_C=='C':
					rlist.append([lookup_key,int(R)+idx,int(C)])
					
		elif string.lower(rval)=='tb':
			self.board.toggle_boardmap()
			for player in self.players:
				player.tray.toggle_boardmap()
		
		elif string.lower(rval)=='quit':sys.exit()
		elif string.lower(rval)=='q':sys.exit()
		elif string.lower(rval)=='skip':
			self.tuxturn=1
			self.player_idx=0
		elif string.lower(rval)==('help'):
			self.usage()
			self.pause()
		elif string.lower(rval)=='defn':
			self.show_definition()
		elif string.lower(rval)=='scoring':
			self.scoring()
			self.pause()
		elif string.lower(rval)=='dist':
			self.dist()
			self.pause()
		elif string.lower(rval)=='lookup':
			self.lookup()
			self.pause()
		elif string.lower(rval)[0:8]=='exchange':
			srval=string.split(rval,' ',1)
			try:
				self.exchange(srval[1])
				self.tuxturn=1
				self.player_idx=0
			except:pass
		else:
			print 'command not understood'
		
		if DEBUG:print 'returning:',rlist
		return rlist
		
		
	def render(self):
		score="  Player[0]:%03d       Player[1]:%03d\n"%(self.players[0].score,self.players[1].score)
		print score
		self.players[0].tray.print_word_map(Letters)
		self.board.print_word_map(Letters)
		self.players[1].tray.print_word_map(Letters)
				
	def play(self,level):
		
		self.board=Board(self.global_config['M'],self.global_config['N'],self.global_config['default_boardmap'],self.global_config['use_default_boardmap'])

		validator=TWS_Validator(self.board,self)#self passed for score update
		self.validator=validator
		localizer=TWS_Localizer(self.board,self)#self passed for score update
		self.localizer=localizer

		self.tuxturn=0
		self.player_idx=self.global_config['first_player_idx']
		if self.player_idx==0:self.tuxturn=1
		
		self.draw_tiles()
		self.cannot_move_count=0
		PLAYING=True
		
		while PLAYING:
			
			#os.system('clear')
			
			self.render()
			if self.tuxturn:
				
				self.players[self.player_idx].solver.generate_expressions()
				solver_finished=0
				
				#while solver_finished!=1:#might not need to be loop now
				self.num_replacements=0
				self.solver_submission=self.players[self.player_idx].solver.generate_options()
				rlist=self.solver_submission
				if DEBUG:print 'rlist=',rlist
				#self.render()
				#rval=raw_input('am here:')
				#if rlist!=None:break
				
				if rlist != None:
					self.board.increment_num_committed()
					word=self.get_word_from_rlist(rlist)
					last_article=self.players[self.player_idx].solver.get_article(word)
					score=self.score(rlist)
					self.players[0].score+=score
					self.words_used.append(
						{
							'key':unicode(word).encode('latin1'),
							'definition':unicode(last_article['content']).encode('latin1'),
							'score':score,
						}	
					)

					num_used_from_tray=0
					for idx in range(len(rlist)):
						M=rlist[idx][1]
						N=rlist[idx][2]
						if not self.board.check4guest(M,N):
							tile=self.players[0].tray.get_guest_by_str(rlist[idx][0][0])
							self.board.take_guestMN(tile,M,N)
							num_used_from_tray+=1
						
					if num_used_from_tray==self.players[0].tray.N:
						self.players[0].score+=self.global_config['bonus_award']
					
					self.board.increment_num_committed()
					self.draw_tiles()
				
				self.tuxturn=0
				self.player_idx=1
				
			else:
			
				rlist=self.handle_input()
				if DEBUG:print 'received rlist=',rlist
				
				if rlist==[]:continue
				elif self.validate(rlist):pass
				else:continue
				
				num_used_from_tray=0
				for idx in range(len(rlist)):
					M=rlist[idx][1]
					N=rlist[idx][2]
					if not self.board.check4guest(M,N):
						tile=self.players[1].tray.get_guest_by_str(rlist[idx][0][0])
						self.board.take_guestMN(tile,M,N)
						num_used_from_tray+=1
						
				if num_used_from_tray==self.players[1].tray.N:
					self.players[1].score+=self.global_config['bonus_award']
					
				self.board.increment_num_committed()	
				self.draw_tiles()
				
				self.tuxturn=1
				self.player_idx=0
				
		return -1

	def score(self,rlist):
		score=0
		if len(rlist)>1:
			if rlist[0][1]==rlist[1][1]:exprtype='row'
			elif rlist[0][2]==rlist[1][2]:exprtype='col'
		
		tripple_word=0
		double_word=0
		for idx in range(len(rlist)):
			multiplier=1
			special_tile_code=self.board.get_default_char(rlist[idx][1],rlist[idx][2])
			if special_tile_code==0:
				multiplier=1
			if special_tile_code==1:
				multiplier=2
			if special_tile_code==2:
				double_word+=1
			if special_tile_code==3:
				multiplier=3
			if special_tile_code==4:
				tripple_word+=1
					
			gc_scoring_key=rlist[idx][0]
			char_val=self.global_config['scoring'][gc_scoring_key]
			#print 'char_val=',char_val
			score+=multiplier*char_val
			#now check boardmap schema:
		
		if tripple_word:score*=3
		if double_word:score*=2
		
		return score
		
	def get_word_from_rlist(self,rlist):
		word=u''
		for idx in range(len(rlist)):
			
			gc_scoring_key=rlist[idx][0]
			split_gc_scoring_key=string.split(gc_scoring_key,'_',1)
			achar=split_gc_scoring_key[0]
			mod='NOMOD'
			if len(split_gc_scoring_key)>1:
				mod=split_gc_scoring_key[1]
			
			uchar_desc=None
			
			if mod=='NOMOD':
				uchar_desc="LATIN CAPITAL LETTER %s"%(achar)
			else:
				uchar_desc="LATIN CAPITAL LETTER %s WITH %s"%(achar,mod)
			
			uchar=unicodedata.lookup(uchar_desc)
			word+=uchar
		return word	
	
	def validate(self,rlist):
		
		letters=self.global_config['letters']
		idx_map=self.board.get_idx_map(letters)#idx_map does return 2D array of uchars
		
		if DEBUG:print rlist
		
		if len(rlist)>1:
			if rlist[0][1]==rlist[1][1]:exprtype='row'
			elif rlist[0][2]==rlist[1][2]:exprtype='col'
			
		else:return False
		
		rval=False
		if exprtype=='row':
			if (rlist[0][2]+len(rlist)-1)>self.board.N:return False
			rval=self.check_row(rlist,idx_map)
		else:
			if (rlist[0][1]+len(rlist)-1)>self.board.M:return False
			rval=self.check_col(rlist,idx_map)
		
		if DEBUG:print 'check row/col returned rval=',rval
		if not rval:return False
		
		#print fixed-up rlist
		if DEBUG:print 'rlist=',rlist
		
		#confirm is key in dict
		word=self.get_word_from_rlist(rlist)
			
		last_article=self.players[self.player_idx].solver.get_article(word)
		
		if last_article['key']:	

			#don't allow abbreviations
			if string.find(last_article['content'][0:10],'abbr.')>=0:
				print 'abbreviations not allowed'
				return False
			
			
			
			#fp_list=self.players[self.player_idx].solver.mkfingerprint(word)
			#scrabble_sum=self.players[self.player_idx].solver.get_scrabble_sum(fp_list)
			#print 'sum=',scrabble_sum
			
			rlist4scoring=[]
			for	idx in range(len(rlist)):
				mod='NOMOD'
				gc_scoring_key="%s_%s"%(string.upper(rlist[idx][0]),mod)
				rlist4scoring.append([gc_scoring_key,rlist[idx][1],rlist[idx][2]])
			
			scrabble_sum=self.score(rlist4scoring)
			self.players[self.player_idx].score+=scrabble_sum
			
			
			self.words_used.append(
				{
					'key':unicode(word).encode('latin1'),
					'definition':unicode(last_article['content']).encode('latin1'),
					'score':scrabble_sum,
				}	
			)

			
			return True
		
		else:
			msg="%s: %s"%(word.encode('latin1'),'Not Found In Resource')
			self.set_last_defn(msg)
			return False


	def check_row(self,rlist,idx_map):
			
			letters=self.global_config['letters']
			
			if DEBUG:
				print rlist
				for ridx in range(len(idx_map)):
					for cidx in range(len(idx_map[0])):
						print idx_map[ridx][cidx],' ',
					print ''
			
			#left
			m=rlist[0][1]
			n=rlist[0][2]
			if n>0 and idx_map[m][n-1]!='--':return False
			
			#right
			m=rlist[0][1]
			n=rlist[len(rlist)-1][2]
			if n+1<=self.board.N-1 and idx_map[m][n+1]!='--':return False
			
			#above/below
			need={}
			for idx in range(len(rlist)):
				#Check that existing letters match submission:020507
				#And that needed letters available from tray::041407
				map_m=rlist[0][1]
				map_n=rlist[0][2]+idx
				if idx_map[map_m][map_n]!='--':
					if letters[int(idx_map[map_m][map_n])]!=rlist[idx][0]:return False
				else:
					if need.has_key(rlist[idx][0]):need[rlist[idx][0]]+=1
					else:need[rlist[idx][0]]=1
				
			#now verify need counts available in tray:
			for key in need.keys():
				if self.players[self.player_idx].tray.count(key)<need[key]:return False
				
			for idx in range(len(rlist)):
				#above
				map_m=rlist[0][1]-1
				map_n=rlist[0][2]+idx
				if map_m>0:
					if idx_map[map_m][map_n]!='--':
						if idx_map[map_m+1][map_n]!='--':continue#i.e existing
						return False
				
				#below
				map_m=rlist[0][1]+1
				map_n=rlist[0][2]+idx
				if map_m<self.global_config['M']:
					if idx_map[map_m][map_n]!='--':
						if idx_map[map_m-1][map_n]!='--':continue#i.e existing
						return False
			
			return True		
					
	def check_col(self,rlist,idx_map):
			
			letters=self.global_config['letters']
			
			if DEBUG:
				print rlist
				for ridx in range(len(idx_map)):
					for cidx in range(len(idx_map[0])):
						print idx_map[ridx][cidx],' ',
					print ''
			
			#above
			m=rlist[0][1]
			n=rlist[0][2]
			if m>0 and idx_map[m-1][n]!='--':return False
			
			#below
			m=rlist[len(rlist)-1][1]
			n=rlist[0][2]
			if m+1<=self.board.M-1 and idx_map[m+1][n]!='--':return False
			
			#left/right
			need={}
			for idx in range(len(rlist)):
				#Check that existing letters match submission:020507
				#And that needed letters available from tray::041407
				map_m=rlist[0][1]+idx
				map_n=rlist[0][2]
				if idx_map[map_m][map_n]!='--':
					if letters[int(idx_map[map_m][map_n])]!=rlist[idx][0]:return False
				else:
					if need.has_key(rlist[idx][0]):need[rlist[idx][0]]+=1
					else:need[rlist[idx][0]]=1
				
			#now verify need counts available in tray:
			for key in need.keys():
				if self.players[self.player_idx].tray.count(key)<need[key]:
					return False
				
			for idx in range(len(rlist)):
				#left
				map_m=rlist[0][1]+idx
				map_n=rlist[0][2]-1
				if map_n>0:
					if idx_map[map_m][map_n]!='--':
						if idx_map[map_m][map_n+1]!='--':continue#i.e existing
						return False
				
				#right
				map_m=rlist[0][1]+idx
				map_n=rlist[0][2]+1
				if map_n<self.global_config['N']:
					if idx_map[map_m][map_n]!='--':
						if idx_map[map_m][map_n-1]!='--':continue#i.e existing
						return False
			
			return True	
			


if __name__=='__main__':
	
	x=TWS_ASCII()
