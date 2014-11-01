"""
/***************************************************************************

	Author			:Charles B. Cosse 
	
	Email			:ccosse@gmail.com
					
	Website			:www.asymptopia.org
	
	Copyright		:(C) 2002-2007 Asymptopia Software.
	
 ***************************************************************************/
"""
import string,unicodedata
DEBUG=False

def format_line(content,REFORMAT_IN_ALB):
	
	content=unicode(content).encode('latin1')
	
	content=string.strip(content)
	#concat_content=content
	#""" 
	content=string.split(content,' ',100000)
	concat_content=u''
	count=0
	for idx in range(0,len(content)):
		count+=len(content[idx])
		concat_content="%s %s"%(concat_content,content[idx])
		if count>=100 and REFORMAT_IN_ALB:
			concat_content="%s \n"%(concat_content)
			count=0
	
	concat_content=string.replace(concat_content,"'",'')
	return concat_content
