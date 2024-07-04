from bs4 import BeautifulSoup
import requests
import json

url = 'https://www.imdb.com/list/ls003501243/'
sname = '../data/top_500.json'

def extract_from_txt(sname):
    with open('../data/page.txt', 'r') as f:
        text = f.read()
    titles = text.split('ipc-title ipc-title--base ipc-title--title ipc-title-link-no-icon ipc-title--on-textPrimary sc-c7e5f54-9 irGIRq dli-title')[1:]
    titles = [title.split('</div>')[0] for title in titles]
    titles = {title.split('href="')[1].split('/')[2]: ' '.join(title.split('"ipc-title__text">')[1].split('</h3>')[0].split(' ')[1:]) for title in titles}
    with open(sname, 'w') as f:
        json.dump(titles, f, indent=4)

def extract_imdb_list(url, sname):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    movies = soup.find_all('h3', {'class': 'lister-item-header'})
    movies = {str(movie.a).split('"')[1].split('/')[2]: str(movie.text).split('\n')[2] for movie in movies}
    with open(sname, 'w') as f:
        json.dump(movies, f, indent=4)

if __name__ == "__main__":
    extract_from_txt(sname)