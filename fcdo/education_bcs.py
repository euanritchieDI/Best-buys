import pandas as pd
import requests 
from odf.opendocument import load
from odf.element import Element
from odf.text import P, H, Span, List, ListItem
import re

bc     = pd.read_csv("C:/git/Best-buys/fcdo/data/BC_links.csv")
result = pd.read_csv("C:/git/Best-buys/fcdo/data/basic_data.csv")

# Merge on the basic project data
bc = pd.merge(bc, result.drop(columns=["title"]), on="parent", how="left")

# Some sectors have missing info. Assuming these are not education (which are selected as <12000)
bc['sectors'] = bc['sectors'].replace("", "99999")
bc['sectors'].fillna("99999", inplace=True)
bc['sector_pct'] = bc['sector_pct'].replace("", "100")
bc['sector_pct'].fillna("100", inplace=True)

# CHECK TO SEE IF LENGTHS OF EACH ELEMENT ARE SAME 
#seclen = [len(i) for i in sects]
#pctlen = [len(i) for i in pcts]
#seclen==pctlen

# Some sector_pct are "". Given lengths are the same as sectors, this must mean that there is only one
# sector listed (even if NA). So, going to 

sects = bc['sectors'].str.split(";")
pcts  = bc['sector_pct'].str.split(";")


educ = []
for i, j in zip(sects,pcts):
    if len(i)>1:
        sec = [float(x) for x in i]
        pct = [float(y) for y in j]
        Pcts=sum((np.asarray(sec)<12000) * pct/100)
    else:
        sec = float(i[0])
        pct = float(j[0])
        Pcts = (sec<12000)*pct
    educ.append(Pcts)

bc['educ_pct'] = educ
bc = bc.drop(columns=['LF','PCR','AR','BC','IS'])    
bc = bc[bc['link'].str.endswith('odt')].reset_index() 

bc = bc[bc['educ_pct']>0].reset_index()

#bc.to_csv("C:/git/Best-buys/fcdo/data/Education_BCs.csv",index=False)

def readtext(url):
    response = requests.get(url)

    with open('temp.odt', 'wb') as temp_file:
        temp_file.write(response.content)

    doc = load('temp.odt')

    Elements = \
        doc.getElementsByType(P) +  \
        doc.getElementsByType(H) #+\
#        doc.getElementsByType(Span) + \
#        doc.getElementsByType(List)

    paragraphs = []
    for elem in Elements:
        paragraphs.append(str(elem))

    thetext = "\n".join(paragraphs)
    return thetext


#doc.getElementsByType(H) doc.getElementsByType(P)
bctext = {}
for x,y in enumerate(bc['link']):
    try:
        thetext = readtext(y)
        #bctext[bc['id'][x]] = thetext
    except:
        thetext = 'link_broken'
    bctext[x] = thetext
    print(x)

lengths = [len(i) for i in bctext.values()]
bc['doclength'] = lengths     


preprim_str = r"pre[- ]?primary"
tarl_str = r"teaching ?at ?the ?right ?level|\btarl\b"
stped_str = r"structured ?pedagogy"
bestbuy_str = r"(best|smart) ?buys|what does recent evidence tell us are"

preprim = []
tarl = []
stped = []
bestbuy = []

for i in bctext:
    preprim.append(len(re.findall(preprim_str, bctext[i].lower())))
    tarl.append(len(re.findall(tarl_str, bctext[i].lower())))
    stped.append(len(re.findall(stped_str, bctext[i].lower())))
    bestbuy.append(len(re.findall(bestbuy_str, bctext[i].lower())))    

bc['tarl'] = tarl 
bc['stped'] = stped 
bc['preprim'] = preprim 
bc['bestbuy'] = bestbuy 


bc.to_csv("C:/git/Best-buys/fcdo/data/Education_BCs.csv",index=False)










