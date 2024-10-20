import pandas as pd
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import time
from lxml import etree
import numpy as np


### ------------------------------------------------------------------------------------
# GET LINKS TO XML PAGES FROM IATI REGISTRY

fcdolinks = []

for i in range(1, 8):  # Loop from 1 to 7
    url = f"https://iatiregistry.org/publisher/fcdo?page={i}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a',string=re.compile("Download"))
    toadd = [link['href'] for link in links]
    fcdolinks.extend(toadd)

fcdolinks = [link for link in fcdolinks if 'xml' in link]
fcdolinks = [link for link in fcdolinks if 'organisation' not in link]

##-----------------------------------------------------------------------
## GET LINKS TO PROJECT DOCUMENTS
## (It might be more efficient to combine with above rather than query xmls twice but this is simple)


collectdocs = {}

for lnk in fcdolinks:  
    proj = re.sub(r".*/", "", lnk)
    proj = re.sub(r"\.xml$", "", proj)
    
    link = read_xml(lnk)
    
    if link == "fail":
        continue

    docnodes = link.xpath("//document-link/title/narrative")
    if len(docnodes) == 0:
        continue
    else:
        docnarr = [node.text for node in docnodes]
        doclink = [node.xpath('../..')[0].attrib.get('url') for node in docnodes]
        docid   = [node.xpath('../../../*')[0].text for node in docnodes] 
        docttl  = [node.xpath('../../../title/narrative')[0].text for node in docnodes]# Adjust 'child' to the correct tag if necessary
        docs    = pd.DataFrame({
            "narrative": docnarr,
            "link": doclink,
            "parent": docid,
            "proj": proj,
            "title":docttl
        })
    collectdocs[proj] = docs

collectdocs = pd.concat(collectdocs, ignore_index=True)    


collectdocs = collectdocs.drop_duplicates()  # Drop duplicate rows

# Convert the 'narrative' column to lowercase
collectdocs.loc[:,'narrative'] = collectdocs['narrative'].str.lower()

# Create new columns based on whether certain patterns are found in the 'narrative' column
collectdocs.loc[:,'LF'] = collectdocs['narrative'].str.contains(r"logical ?framework").astype(int)
collectdocs.loc[:,'PCR'] = collectdocs['narrative'].str.contains(r"project ?completion ?review").astype(int)
collectdocs.loc[:,'AR'] = collectdocs['narrative'].str.contains(r"annual ?review").astype(int)
collectdocs.loc[:,'BC'] = collectdocs['narrative'].str.contains(r"business ?case").astype(int)
collectdocs.loc[:,'IS'] = collectdocs['narrative'].str.contains(r"intervention ?summary").astype(int)

# Select just the business case documents
bc = collectdocs[collectdocs['BC']==1].copy()
bc.loc[:,'year'] = bc['narrative'].str.extract(r'((?<=, )\d{4})')
bc.loc[:,'ADD'] = bc['narrative'].str.contains(r'addendum', case=False).astype(int)

# Just ex-DFID bits
bc = bc[~bc["parent"].str.contains('GOV-3')]
bc.to_csv("C:/git/Best-buys/fcdo/data/BC_links.csv",index=False)



