from pandas import read_excel, DataFrame
from requests import get
from bs4 import BeautifulSoup
from time import sleep


def is_still_online(soup, url):
    out = False
    i = 0
    while i < 5:
        out = soup.find("h2", attrs={"class": "trackTitle"}) is not None
        if out:
            return out
        if not out:
            sleep(10.0)
            r = get(url)
            soup = BeautifulSoup(r.text, "html.parser")
        i += 1
    return out


def supported_by(soup):
    return soup.find("div", attrs={"class": "deets"}) is not None


df = read_excel("bandcamp_2017_Q1.xlsx", sheetname="Bandcamp Q1 2017")

enriched = []

for url in set(df["url"]):
    print(url)
    lijn = df[df["url"] == url].iloc[0].to_dict()
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    online = is_still_online(soup, url)
    support = supported_by(soup) if online else None
    enriched.append(
        {
            "url": url,
            "still_online": online,
            "supported": support
        }
    )

DataFrame(enriched).to_excel("bandcamp_2017_Q1_enriched.xlsx", index=False)
