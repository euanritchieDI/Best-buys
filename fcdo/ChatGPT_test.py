import requests 
import pandas as pd
from odf.opendocument import load
from odf.element import Element
from odf.text import P, H, Span, List, ListItem
import re
import os
from openai import OpenAI

#url = 'http://iati.fcdo.gov.uk/iati_documents/3717112.odt'

bc = pd.read_csv("C:/git/Best-buys/fcdo/data/Education_BCs.csv")

#---------------------------------------------------------
# Function to parse ODT documents

def readtext(url):
    response = requests.get(url)

    with open('temp.odt', 'wb') as temp_file:
        temp_file.write(response.content)

    doc = load('temp.odt')

    Elements = \
        doc.getElementsByType(P) +  \
        doc.getElementsByType(H) #+\

    paragraphs = []
    for elem in Elements:
        paragraphs.append(str(elem))

    thetext = "\n".join(paragraphs)
    return thetext
#---------------------------------------------------------

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

#---------------------------------------------------------
# Loop that passes text to ChatGPT API

client = OpenAI()

with open("H:/My Documents/apikey.txt",'r') as getkey:
    apikey = getkey.read()
    
os.environ["OPENAI_API_KEY"] = apikey

prompt = """
You will be provided with a business case for an education aid project. 
You are tasked with assessing whether it has any component which could be described as 
'teaching at the right level'. This is a specific type of education intervention which involves 
ensuring that the level of tuition provided to students is matched to their current level of educational
proficiency. Please be conservative, and if the answer is no, please 
just respond with the word no. If the answer is yes, please provide a very short 
description of why you think so.
"""
results = []
for i in bctext.values():
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": i
            }
        ]
    )
    results.append(completion.choices[0].message)

