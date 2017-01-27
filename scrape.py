from requests import get
from bs4 import BeautifulSoup
from datetime import datetime
from pandas import DataFrame, read_excel
from time import sleep


def get_label(soup):
    artist = soup.find("span", attrs={"itemprop": "byArtist"}).a.contents[0].strip()
    releaser = soup.find("p", attrs={"id": "band-name-location"}).find("span", attrs={"class": "title"}).contents[0].strip()
    label_tag = soup.find("span", attrs={"class": "back-to-label-name"})
    if label_tag:
        return label_tag.contents[0].strip()
    else:
        return releaser if artist.lower() != releaser.lower() else None


def parse_release(url):
    release_request = get(url)
    soup = BeautifulSoup(release_request.text, "html.parser")
    if soup.find("h2", attrs={"class": "trackTitle"}):
        title = soup.find("h2", attrs={"class": "trackTitle"}).contents[0].strip()
        artist = soup.find("span", attrs={"itemprop": "byArtist"}).a.contents[0].strip()
        releasedate_str = soup.find("meta", attrs={"itemprop": "datePublished"})["content"]
        releasedate = str(datetime(int(releasedate_str[0:4]), int(releasedate_str[4:6]), int(releasedate_str[6:8])).date())
        formats_raw = soup.findAll("li", attrs={"class": "buyItem"})
        label = get_label(soup)
        if len(soup.find("span", attrs={"class": "location"}).contents) > 0:
            location = soup.find("span", attrs={"class": "location"}).contents[0].strip()
            formats = []
            for format_raw in formats_raw:
                if format_raw.h3.button:
                    secondary_text = format_raw.h3.find("div", attrs={"class": "merchtype secondaryText"})
                    format = secondary_text.contents[0].strip() if secondary_text else format_raw.h3.button.span.contents[0]
                    formats.append(format)
            return {
                "title": title,
                "artist": artist,
                "date": releasedate,
                "url": url,
                "formats": formats,
                "location": location,
                "label": label
            }


url = "https://bandcamp.com/tag/{0}?page={1}&sort_field=date"

with open("cities.txt", "r") as f:
    cities = [city.lower() for city in f.read().split("\n")]

start_urls = [url.format(city.lower(), i) for i in range(1, 11, 1) for city in cities]

data = read_excel("data.xlsx")

ignore_list = []
diff = []

for start_url in start_urls:
    stad = start_url.split("/")[-1].split("?")[0]
    if stad not in ignore_list:
        print(stad, start_url)
        r = get(start_url)
        soup = BeautifulSoup(r.text, "html.parser")
        releases = soup.find("div", attrs={"class": "results"})
        good_page = soup.find("ul", attrs={"id": "sortNav", "class": "horizNav"})
        while good_page is None:
            print("offline, even wachten")
            sleep(10.0)
            r = get(start_url)
            soup = BeautifulSoup(r.text, "html.parser")
            releases = soup.find("div", attrs={"class": "results"})
            good_page = soup.find("ul", attrs={"id": "sortNav", "class": "horizNav"})
        if releases:
            if len(releases.ul.findAll("li", attrs={"class": "item"})) > 0:
                for release in releases.ul.findAll("li", attrs={"class": "item"}):
                    release_url = release.a["href"]
                    if release_url not in data["url"].values:
                        release_info = parse_release(release_url)
                        if release_info:
                            artist_location_in_belgium = "Belg" in release_info["location"]
                            artist_location_matches_cities = release_info["location"].lower() in cities
                            if artist_location_in_belgium or artist_location_matches_cities:
                                for format in release_info["formats"]:
                                    line = release_info.copy()
                                    line.pop("formats")
                                    line["format"] = format
                                    data.append(DataFrame([line]))
                                    diff.append(line)
                                    print(release_info["artist"], release_info["title"], format, len(diff), len(data.index))
            else:
                ignore_list.append(stad)
                print(stad, "added to ignore list")
        else:
            ignore_list.append(stad)
            print(stad, "added to ignore list")

data.to_excel("data.xlsx")
DataFrame(diff).to_excel("diff_" + datetime.now().isoformat() + ".xlsx")