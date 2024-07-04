import json
import pandas as pd

'''
def get_data(source, filter_list, sname):
    data = pd.read_csv(source, error_bad_lines=False, sep='\t')
    data.head(100)
    filtered_data = data.query(f'nconst in {filter_list}')
    id_list = list(set(filter_list) - set(filtered_data['nconst']))
    filtered_data.to_csv(sname, header = True, index = False)
    not_in = data.query(f'nconst in {id_list}')
    not_in.to_csv('../data/not_in.csv', header=True, index=False)
'''

def get_data(source, filter_list, sname):
    data = pd.read_csv(source, error_bad_lines=False, sep=',')
    data.head(100)
    data['lower_title'] = data['title'].str.lower()
    filtered_data = data.query(f'lower_title in {filter_list}')
    id_list = list(set(filter_list) - set(filtered_data['lower_title']))
    book_list = {item[0]:item[-1] for item in data.iloc if item[-1].startswith(tuple(id_list)) and ':' in item[-1]}
    more_data = data.query(f'bookId in {list(book_list.keys())}')
    filtered_data = pd.concat([filtered_data, more_data])
    book_list = [item for item in id_list if any(item in s for s in list(book_list.values()))]
    id_list = list(set(id_list) - set(book_list))
    print(len(id_list))
    filtered_data = filtered_data[['bookId', 'title', 'series', 'author', 'rating', 'language', 'genres', 'characters', 'awards', 'setting', 'description']]
    filtered_data.to_csv(sname, header = True, index = False)
    with open('../data/not_in.json', 'w') as f:
        json.dump(id_list, f, indent=4)
    '''
    not_in = data.query(f'title in {id_list}')
    not_in.to_csv('../data/not_in.csv', header=True, index=False)
    '''
    print(len(filtered_data))


def top_250(fname):
    data = pd.read_csv(fname, error_bad_lines=False)
    links = list(data['IMDB link'])
    links = [l.split('/')[-1] for l in links]
    return links


def get_name_list(fnames):
    books = pd.read_csv(fnames)
    names = books['Title'].to_list()
    names = [x.lower() for x in names]
    return names
    '''name_list = {}
    for fname in fnames:
        with open(fname, 'r') as f:
            name_list.update(json.load(f))
    return name_list'''


def get_people_list(fnames):
    crews = pd.read_csv(fnames[0])
    directors = list(crews['directors'])
    writers = list(crews['writers'])
    writers = [writer.split() for writer in writers]
    writers = [w for writer in writers for w in writer]

    principals = pd.read_csv(fnames[1])
    principals = list(principals['nconst'])
    
    directors.extend(writers)
    directors.extend(principals)
    people_list = list(set(directors))

    return(people_list)

def merge_df(dfA, dfB):
    df = dfA.merge(dfB, how='left', on='tconst')
    return df

if __name__ == '__main__':
    name_list = get_name_list('../data/top_500_books.csv')
    '''
    dfA = pd.read_csv('../data/names.csv')
    dfA = dfA[['tconst', 'primaryTitle', 'isAdult', 'startYear', 'runtimeMinutes', 'genres']]
    dfB = pd.read_csv('../data/ratings.csv')
    merge_df(dfA, dfB).to_csv('../data/movies.csv', header=True, index=False)
    '''
    print(len(name_list))
    get_data('../data/books.csv', name_list, '../data/modified_books.csv')