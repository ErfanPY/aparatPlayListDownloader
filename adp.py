import argparse
import requests as req
from bs4 import BeautifulSoup as bs

def usage():
    return """
        USe "" around link to avoid bad things :>
        adp.py "{Link}" [quality]
        python apd.py "https://www.aparat.com/v/d13rh3"
        python apd.py "https://www.aparat.com/v/d13rh3" -q 480

        The default quality is 480.
    """

def main():
    mainPage = req.get(link).content
    main_soup = bs(mainPage, 'html.parser')
    main_name = main_soup.find("span", attrs={"class":"d-in v-m"}).text.encode()

    playlist = main_soup.find_all('div', attrs={'class':'playlist-body'})[0]
    playListLinks = playlist.find_all('a', attrs={'class':'title'})

    videoPages = [f"https://www.aparat.com{video.get('href')}" for video in playListLinks]

    links = {}
    for page in videoPages :
        html = req.get(page).content
        soup = bs(html, 'html.parser')
        name = soup.find("h1", attrs={"id":"videoTitle", "class":"title"}).text.encode()
        qualitys = soup.find_all('div', attrs={'class':'dropdown-content'})[0].find_all('a')
        for qual in qualitys :
            if quality in qual.get('aria-label'):
                links[name] = qual.get('href')

    with open('downloadList.txt', 'a') as file:
        file.write(f"{main_name}--{quality}\n")
        [file.write(f"{name}:{link}\n") for name, link in links.items()]



if __name__ == "__main__":
    link = "https://www.aparat.com/v/fAZSV?playlist=288572"
    quality = "720"
    main()
    """
    parser = argparse.ArgumentParser(description="Aparat Playlist Downloader(APD)", usage=usage())
    parser.add_argument("link", help="main page Link")
    parser.add_argument("-q", "--quality", help="eg: [124, 360, 480, 720, ...]", default='480')
    '''parser.add_argument("--debug", action="store_true")'''

    args = parser.parse_args()
    link = args.link
    quality = args.quality

    if args.quality :
        main()
    else:
        usage()
    """
