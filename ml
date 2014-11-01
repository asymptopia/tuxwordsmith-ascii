#!/usr/bin/python
import string,os,sys


if __name__=='__main__':
        if len(sys.argv)>2:
                infname=sys.argv[1]
                inf=open(infname)
                lines=inf.readlines()
                inf.close()
                for idx in range(len(lines)):
                        if string.find(lines[idx],sys.argv[2])>0:
                                print "%04d\t%s"%(idx,string.split(lines[idx],'(',1)[0])
 
