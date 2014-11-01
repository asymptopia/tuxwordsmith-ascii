"""
/***************************************************************************

        Author                  :Charles B. Cosse 
        
        Email                   :ccosse@gmail.com
                                        
        Website                 :www.asymptopia.org
        
        Copyright               :(C) 2002-2007 Asymptopia Software.
        
 ***************************************************************************/
"""
from spot import Spot
DEBUG=True
DEBUG=False

class Board:
	def __init__(self,M,N,boardmap,use_boardmap):
		if DEBUG:print 'Board'
		self.M=M
		self.N=N
		self.boardmap=boardmap
		self.use_boardmap=use_boardmap
		self.num_committed=0
		
		self.spots=[]
		self.representation2D=[]
		for midx in range(self.M):
			self.representation2D.append([])
			for nidx in range(self.N):
				spot=Spot(midx,nidx,boardmap[midx][nidx],self.use_boardmap)
				self.spots.append(spot)
				self.representation2D[midx].append(spot)

	def count(self,char):
		count=0
		for spot in self.spots:
			if spot.guest:
				if spot.guest.uchar.encode('latin1')==char:count+=1
		if DEBUG:print "returning count(%s)=%d"%(char,count)
		return count
				
	def get_word_map(self):
		wm=[]
		for midx in range(self.M):
			wm.append([])
			for nidx in range(self.N):
				spot=self.representation2D[midx][nidx]
				if spot.guest:
					str_val=spot.guest.str_val
					uchar=spot.guest.uchar
					wm[midx].append(uchar)
					#counts[str_val]['count']+=1
					#counts[str_val]['mn'].append((midx,nidx))
				else:
					wm[midx].append(spot.get_default_char())
					
		
		return wm
	
	def get_default_char(self,m,n):
		default_char=self.representation2D[m][n].default_char
		try:
			rval=eval(default_char)
			return rval
		except Exception,e:
			return 0
		
		
	def toggle_boardmap(self):
		
		if self.use_boardmap==1:self.use_boardmap=0
		else:self.use_boardmap=1
		
		for idx in range(len(self.spots)):
			self.spots[idx].toggle_boardmap()
			
			
				
	def get_idx_map(self,letters):
		wm=[]
		for midx in range(self.M):
			wm.append([])
			for nidx in range(self.N):
				spot=self.representation2D[midx][nidx]
				if spot.guest:
					str_val=spot.guest.str_val
					uchar=spot.guest.uchar
					wm[midx].append("%2d"%letters.index(uchar))
					#counts[str_val]['count']+=1
					#counts[str_val]['mn'].append((midx,nidx))
				else:wm[midx].append('--')
		
		
		return wm
	
	def print_idx_map(self,letters):
		idx_map=self.get_idx_map(letters)
		for ridx in range(len(idx_map)):
			for cidx in range(len(idx_map[0])):
				print idx_map[ridx][cidx],
			print ''
		
	def print_word_map(self,letters):#letters not used; passed for likeness to print_idx_map()
		
		word_map=self.get_word_map()
		
		if self.M>1:
			line="    "
			for cidx in range(len(word_map[0])):
				val=cidx
				if val>9:val-=10
				line="%s%d "%(line,val)
			print line,'\n'
		
		for ridx in range(len(word_map)):
			if self.M>1:line="%02d "%(ridx)
			else:line="\n%s"%(10*' ')

			for cidx in range(len(word_map[0])):
				line="%s %s"%(line,word_map[ridx][cidx].encode('latin1'))

			if self.M==1:line="%s\n"%line
			else:line="%s  %02d"%(line,ridx)
			print line
			
		if self.M>1:
			line="    "
			for cidx in range(len(word_map[0])):
				val=cidx
				if val>9:val-=10
				line="%s%d "%(line,val)
			print '\n',line

	def get_map(self):#return meta info as well...
		
		counts={}
		counts['+']={'count':0,'mn':[]}
		counts['-']={'count':0,'mn':[]}
		counts['*']={'count':0,'mn':[]}
		counts['/']={'count':0,'mn':[]}
		counts['=']={'count':0,'mn':[]}
		for idx in range(21):counts[`float(idx)`]={'count':0,'mn':[]}
		
		m=[]
		for midx in range(self.M):
			m.append([])
			for nidx in range(self.N):
				spot=self.representation2D[midx][nidx]
				if spot.guest:
					str_val=spot.guest.str_val
					m[midx].append(str_val)
					counts[str_val]['count']+=1
					counts[str_val]['mn'].append((midx,nidx))
				else:m[midx].append(spot.get_default_char())
		
		
		return(m,counts)
	
			
	def check4guest(self,m,n):
		if m<0 or m>self.M-1 or n<0 or n>self.N-1:return(0)
		spot=self.get_spotMN(m,n)
		if spot.guest==None:return(0)
		else:return(1)
		
	def get_listofheads(self):
		heads=[]
		for spot in self.spots:
			if spot.guest:
				if spot.AMHEAD:heads.append(spot)
		return(heads)			
	
	def clear_spots(self):
		for spot in self.spots:
			spot.remove(self)
	
	def get_spotMN(self,m,n):
		for spot in self.spots:
			MN=spot.getMN()
			if MN[0]==m and MN[1]==n:
				return(spot)
	
	def take_guestMN(self,tile,m,n):
		for spot in self.spots:
			MN=spot.getMN()
			if MN[0]==m and MN[1]==n:
				spot.take_guest(tile,1)
				return(spot)
	
	def get_num_committed(self):
		return(self.num_committed)
	
	def increment_num_committed(self):
		self.num_committed=self.num_committed+1
	
	def get_guest_by_str(self,str_val):
		for spot in self.spots:
			if spot.guest and spot.guest.str_val==str_val:
				return spot.pop_guest()
		return(None)
			
	def get_spots(self):
		return(self.spots)
		
