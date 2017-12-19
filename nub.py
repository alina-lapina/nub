import xml.etree.ElementTree as etree
import datetime
#from filecmp import dircmp
from filecmpmod import dircmp
import os
import shutil

version="4.2"
scriptname="nub"

def parse(filename):
    file=filename+'.xml'
    print('START Parsing ' +file)
    tree = etree.parse(file)
    print('END Parsing ' +file)
    return tree.getroot()

		
def output(filename,funcname):
    f = open(filename+'-'+funcname+'.txt', 'w')
    f.write ('File: ' + filename + '.xml processed by '+ scriptname + ' ' + version +'\n')
    f.write ('by Alina Lapina '+ datetime.datetime.now().isoformat() + '\n')
    return f
	
def v():
    print("version: "+version)
  
# for å sjekke gyldighets datoer til alle taksonomier i en fil
# input xml-fil
# output txt-fil med prefiks "dates" på
# usage nub.dates('crd-q4')
def dates(filename):
    f = output(filename,'dates')
   
    for taxonomy in parse(filename).findall('taxonomy'):
        libelle = taxonomy.get('libelle')
        dtdeb = taxonomy.find('xsd').get('dtdeb')
        dtfin = taxonomy.find('xsd').get('dtfin')
        f.write ('{:_<32} \tvalid from {} \tvalid to {}\n'.format(libelle, dtdeb, dtfin))
  
# for å sammenligne hvilke taksonomier dekker eller ikke deker filer
# (hardkoded for 3 filer)
# input 3 xml-filer
# output txt-fil med prefiks "diff" på
# usage nub.diff('crd-q2','crd-q3','crd-q4')
def diff(q2,q3,q4):
    f = output(q2+'-'+q3+'-'+q4,'diff')
   
    l2 = set(t.get('libelle') for t in parse(q2).findall('taxonomy'))
    l3 = set(t.get('libelle') for t in parse(q3).findall('taxonomy'))
    l4 = set(t.get('libelle') for t in parse(q4).findall('taxonomy'))
    f.write ('{:_<32} q2 q3 q4 \n'.format('taxonomy'))
    for l in sorted(l4 | l3 | l2):
        f.write ('{:_<32} {} {} {} \n'.format(l, ' x' if l in l2 else ' -', ' x' if l in l3 else ' -', ' x' if l in l4 else ' -'))
  
# for å vise hvilke taksonomier refererer til hvilke zip-filer i en fil
# input xml-fil
# output txt-fil med prefiks "zips" på
# usage nub.zips('both')
def zips(filename):
    f = output(filename,'zips')
   
    for taxonomy in parse(filename).findall('taxonomy'):
        libelle = taxonomy.get('libelle')
        zip = taxonomy.find('zip').text
        f.write ('{:_<32} \t{}\n'.format(libelle, zip))
	
def dirdiff(filename):
    f = output(filename, 'dirdiff')
    #XVS nye
    #dir1 = r'''V:\Log\13\XVS nye'''
    #dir2 = r'''V:\Test-Package2017-12-07\Nye13\XVS-TEST'''
    
    #XVS gamle
    dir1= r'''S:\XVSData\output\XVS gamle'''
    dir2= r'''V:\Test-Package2017-12-07\Gamle124\XVS-TEST'''
    
    # XRT nye
    #dir1= r'''V:\Log\14\XRT nye'''
    #dir2= r'''V:\Test-Package2017-12-07\Nye13\XRT-TEST'''
    
    # XRT gamle
    #dir1= r'''V:\Log\14\XRT gamle'''
    #dir2= r'''V:\Test-Package2017-12-07\Gamle124\XRT-TEST'''
    comparison = dircmp(dir1, dir2)
    comparison.report_full_closure(f)
