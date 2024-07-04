from bs4 import BeautifulSoup
import requests
from imdb import Cinemagoer
import json
from parsing import add_quote

url = 'https://www.imdb.com/showtimes/location/US/75080'
url_book = 'https://www.usatoday.com/booklist/booklist'
url_book_alt = 'https://www.librarything.com/zeitgeist/popularity'
sname = '../knowledge/in_theater.json'
sname_book = '../knowledge/bestseller.json'

def extract_imdb_list():
    ia = Cinemagoer()
    in_theater_list = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    movies = soup.find_all('div', class_='lister-item-image ribbonize')
    for movie in movies:
        extracted_items = movie.find_all('strong', recurssive=False)
        pop, rating, date, runtime = [item.text.strip(' </strong>\n') for item in extracted_items]
        title = movie.find('div', class_='title').text
        tid = movie['data-tconst']
        info_dict = {'tid':tid, 'name':title, 'popularity rank':int(pop), 'rating':float(rating), 'release date':date, 'runtime':runtime}
        
        movie_imdb = ia.get_movie(tid[2:])
        casts = movie_imdb['cast'] if 'cast' in movie_imdb else None
        if casts:
            casts = [cast['name'] for cast in casts if 'name' in cast]
            if len(casts) > 10:
                casts = casts[:10]
            info_dict['actors'] = casts
        genres = movie_imdb['genres'] if 'genres' in movie_imdb else None
        if genres:
            info_dict['genres'] = genres
        directors = movie_imdb['director'] if 'director' in movie_imdb else None
        if directors:
            directors = [director['name'] for director in directors if 'name' in director]
            info_dict['directors'] = directors
        writers = movie_imdb['writer'] if 'writer' in movie_imdb else None
        if writers:
            writers = [writer['name'] for writer in writers if 'name' in writer]
            info_dict['writers'] = writers
        countries = movie_imdb['countries'] if 'countries' in movie_imdb else None
        if countries:
            info_dict['located countries'] = countries
        languages = movie_imdb['languages'] if 'languages' in movie_imdb else None
        if languages:
            info_dict['languages'] = languages
        
        in_theater_list.append(info_dict)
    with open(sname, 'w') as f:
        json.dump(in_theater_list, f, indent=4)
    return in_theater_list

def transfer_movie_kn_to_pl(kname):
    with open(sname, 'r') as f:
        kn = json.load(f)
    pl = ''
    for item in kn:
        name = item.pop('name')
        item.pop('tid')
        for attr, value in item.items():
            if isinstance(value, list):
                for v in value:
                    pl += 'movie(' + add_quote(name) + ', ' + add_quote(attr) + ', ' + add_quote(v) + '). '
            else:
                pl += 'movie(' + add_quote(name) + ', ' + add_quote(attr) + ', ' + add_quote(value) + '). '
        pl += '\n'
    with open(kname, 'w') as f:
        f.write(pl)

def extract_book_list():
    bestseller_list = []
    response = requests.get(url_book)
    soup = BeautifulSoup(response.text, 'html.parser')
    book_data = json.loads(soup.find('script', id='__NEXT_DATA__').text)['props']['pageProps']['fallback']['@\"books\",\"2024-04-24\",1,\"\",\"All Books\",\"Rank\",']['books']
    #print(book_data)
    for book in book_data:
        name = book['title']
        auth = [a['name'] for a in book['contributors']]
        author = []
        for a in auth:
            a = a.split(', ')
            a.reverse()
            a = ' '.join(a)
            author.append(a)
        rank = int([r['rank'] for r in book['rankings'] if r['name'] == "USA Today"][0])
        genres = [g['description'].lower() for g in book['subjects']]
        genres_fine = []
        for genre in genres:
            gs = genre.split(' - ')
            for g in gs:
                genres_fine.append(g)
        genres = list(set(genres_fine))
        description = book['description']
        places = []
        rating = None

        open_library_doc = requests.get('https://openlibrary.org/search.json?q=' + name + '+' + author[0])
        open_library_doc = json.loads(open_library_doc.text)
        if open_library_doc['num_found'] > 0:
            open_library_doc = open_library_doc['docs'][0]
            if 'ratings_average' in open_library_doc:
                rating = float(open_library_doc['ratings_average']) * 2
        #print(open_library_doc.keys())
        bestseller_list.append({'name':name, 'author':author, 'popularity rank':rank, 'genres':genres, 'description':description, 'rating':rating})
    with open(sname_book, 'w') as f:
        json.dump(bestseller_list, f, indent=4)
    return bestseller_list

if __name__ == "__main__":
    extract_book_list()