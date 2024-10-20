import pandas as pd
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import time
from lxml import etree
import numpy as np


#--------------------------------------------------------------------------------------
## FUNCTIONS FOR PARSING XML DOCS MORE CONVENIENTLY

def read_xml(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        return etree.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        return "fail"
    
# GET WHETHER PROJECT HAS CLIMATE FINANCE (ICF) TAG    
def getICF(Node):
    codes=[node.attrib.get("code") for node in Node.xpath("tag")]
    if len(codes)==0:
        return False
    else:
        return "ICF" in codes


# GET OECD GENDER POLICY MARKER    
def getgender(Node):
    codes=[node.attrib.get("code") for node in Node.xpath("policy-marker")]
    focus=[node.attrib.get("significance") for node in Node.xpath("policy-marker")]
    return focus[codes==1] if len(codes)>0 and '1' in codes else "NA" # in IATI policy-marker code 1 is gender

# GET PROJECT DATES
def getdates(Node,num):
    dates=[node.attrib.get("iso-date") for node in Node.xpath("activity-date")]
    types=[node.attrib.get("type") for node in Node.xpath("activity-date")]
    return dates[types==num] if len(dates)>0 and num in types else "NA" # in IATI policy-marker code 1 is gender

# GET SUM OF BUDGETS (total commitment for project - needs to be summed by child level eventually)
def budgetSum(Node):
    test1 = [node.text for node in Node.xpath("budget/value")]
    return sum(map(float,test1))    
    
# GET SECTOR CODES    
def getsectors(Node):
    secs=[node.attrib.get("code") for node in Node.xpath("sector")]
    return ";".join(secs)

# GET SECTOR PERCENTAGES
def getsector_pct(Node):
    secs=[node.attrib.get("percentage") for node in Node.xpath("sector")]
    try:
        secs = ";".join(secs)
    except:
        secs = "100" # this may look odd but only relevant cases are where sector has one value
    return secs
    
    
    
    

##-----------------------------------------------------------------------
## PARSE XML INFO FROM REGISTRY - BASIC PROJECT DATA
## (Don't need ICF/gender for this but just part of code I copy and paste around)

collect = {}

for lnk in fcdolinks:
    proj = re.sub(r".*/", "", lnk)
    proj = re.sub(r"\.xml$", "", proj)
    
    link = read_xml(lnk)
    activities = link.xpath("//iati-activity")
    
    ids = [node.xpath("iati-identifier")[0].text for node in activities]
    ttl = [node.xpath("title/narrative")[0].text for node in activities]    
    dsc = [node.xpath("description/narrative")[0].text for node in activities]
    icf = [getICF(node) for node in activities]
    gen = [getgender(node) for node in activities]
    bud = [budgetSum(node) for node in activities]
    st1 = [getdates(node,'1') for node in activities]
    st2 = [getdates(node,'2') for node in activities]
    st3 = [getdates(node,'3') for node in activities]
    st4 = [getdates(node,'4') for node in activities]
    sec = [getsectors(node) for node in activities]
    pct = [getsector_pct(node) for node in activities]

    
    collect[proj] = pd.DataFrame({
        'id':ids,
        'title':ttl,
        'description':dsc,
        'icf':icf,
        'gender':gen,
        'budget':bud,
        'planstart':st1,
        'actualstart':st2,
        'planend':st3,
        'actualend':st4,
        'sectors':sec,
        'sector_pct':pct})
            
result = pd.concat(collect.values(), axis=0)
result['parent'] = result['id'].str.replace(r"-\d{3}$", "", regex=True)

result_grouped = result.groupby('parent').agg({'budget': 'sum'}).reset_index()
result_grouped = result_grouped.rename(columns={'budget':'budget_sum'}) 

result = result[result['id'].str.contains(r'\d{6}$')]
result = pd.merge(result, result_grouped, on="parent", how="left")
result = result.drop(columns=["budget"])