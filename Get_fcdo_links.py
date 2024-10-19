import requests
from bs4 import BeautifulSoup
import re

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