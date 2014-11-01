"""
/***************************************************************************

        Author                  :Charles B. Cosse 
        
        Email                   :ccosse@gmail.com
                                        
        Website                 :www.asymptopia.org
        
        Copyright               :(C) 2002-2007 Asymptopia Software.
        
 ***************************************************************************/
"""
class Spot:
	def __init__(self,M,N,default_char,use_default_char):
			
		self.guest=None
		self.locked=0
		self.M=M
		self.N=N
		self.default_char=default_char
		self.use_default_char=use_default_char
		
	def toggle_boardmap(self):
		if self.use_default_char==0:self.use_default_char=1	
		else:self.use_default_char=0
		
	
	def get_default_char(self):
		if self.use_default_char==1:
			return self.default_char
		else:
			return '-'
		
	def setMN(self,M,N):
		self.M=M
		self.N=N
	
	def getMN(self):
		return((self.M,self.N))
		
	def take_guest(self,guest,use_guest_image):
		self.guest=guest

	def lock(self):
		self.locked=1
	
	def islocked(self):
		return(self.locked)

	def occupied(self):
		if self.guest==None:return(0)
		return(1)
		
	def pop_guest(self):
		guest=self.guest
		self.guest=None
		return(guest)
		
	def update(self):
		pass
		
	
