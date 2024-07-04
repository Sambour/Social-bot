import pandas as pd
import json, ast
from parsing import add_quote

def get_names(fname):
    '''
    This step generates the restaurants' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = ''
    names = []
    movies = {}

    for index, row in data.iterrows():
        if row[0] not in movies:
            movies[row[0]] = {'actor': 0, 'director': 0, 'writer': 0}
        if row[3] == 'actor':
            if movies[row[0]][row[3]] < 3:
                movies[row[0]][row[3]] += 1
                names.append(row[2])
        elif row[3] == 'director':
            if movies[row[0]][row[3]] < 1 and row[4] == '\\N':
                movies[row[0]][row[3]] += 1
                names.append(row[2])
        elif row[3] == 'writer':
            if movies[row[0]][row[3]] < 1 and row[4] == 'written by':
                movies[row[0]][row[3]] += 1
                names.append(row[2])
        row = ['\'' + str(row[attr]).replace('\'', '\\\'') + '\'' for attr in attrs]
        context += 'attend_in' + '(' + ', '.join(row) + '). '
        context += '\n'
    names = list(set(names))
    people = pd.read_csv('../data/people.csv')
    people = people[people['nconst'].isin(names)]
    names = list(people['primaryName'])

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '_names.pl', 'w') as f:
        json.dump(names, f, indent=4)
    
    return attrs


def get_movie_predicates(fname):
    '''
    This step generates the books' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = []

    for index, row in data.iterrows():
        item = {}
        for attr in attrs:
            if attr == 'tconst':
                tid = row[attr]
                item['tid'] = tid
            elif attr in ['genres']:
                value = str(row[attr])
                value = value.split(',')
                if value == ['\\N']:
                    value = None
                item[attr] = value
            else:
                attr_dict = {'primaryTitle':'name', 'startYear':'year', 'averageRating':'rating'}
                if attr in attr_dict:
                    value = str(row[attr])
                    if value == '\\N':
                        value = None
                    item[attr_dict[attr]] = value
        context.append(item)

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '.json', 'w') as f:
        json.dump(context, f, indent=4)


def get_person_predicates(fname):
    '''
    This step generates the books' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = []

    for index, row in data.iterrows():
        item = {}
        multi_dict = {'primaryProfession':'profession', 'knownForTitles':'works'}
        for attr in attrs:
            if attr == 'nconst':
                tid = row[attr]
                item['tid'] = tid
            elif attr in multi_dict:
                value = str(row[attr])
                value = value.split(',')
                if value == ['\\N']:
                    value = None
                item[multi_dict[attr]] = value
            else:
                attr_dict = {'primaryName':'name', 'birthYear':'birth year', 'deathYear':'death year'}
                if attr in attr_dict:
                    value = str(row[attr])
                    if value == '\\N':
                        value = None
                    item[attr_dict[attr]] = value
        context.append(item)

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '.json', 'w') as f:
        json.dump(context, f, indent=4)


def get_principal_predicates(fname):
    '''
    This step generates the books' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = []

    for index, row in data.iterrows():
        item = {}
        multi_dict = {'characters':'characters'}
        tid = row['nconst']
        movieid = row['tconst']
        if 'person_tid' not in item:
            item['person_tid'] = tid
        if 'movie_tid' not in item:
            item['movie_tid'] = movieid
        for attr in attrs:
            if attr == 'tconst':
                pass
            elif attr == 'nconst':
                pass
            elif attr in multi_dict:
                value = str(row[attr])
                value = value.split('","')
                value = [v.strip('"[]') for v in value]
                if value == ['\\N']:
                    value = None
                item[multi_dict[attr]] = value
            else:
                attr_dict = {'category':'category', 'job':'job'}
                if attr in attr_dict:
                    value = str(row[attr])
                    if value == '\\N':
                        value = None
                    item[attr_dict[attr]] = value
        context.append(item)

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '.json', 'w') as f:
        json.dump(context, f, indent=4)


def get_book_predicates(fname):
    '''
    This step generates the books' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = []

    for index, row in data.iterrows():
        item = {}
        for attr in attrs:
            if attr == 'bookId':
                tid = row[attr]
                item['tid'] = tid
            elif attr in ['genres','characters','awards','setting']:
                value = str(row[attr])
                num_quote = value.count('"')
                if num_quote > 1:
                    count = 0
                    left = 0
                    while count < num_quote:
                        left = value.find('"', left)
                        right = value.find('"', left + 1)
                        count += 2
                        if left == 1 or (left > 1 and value[left - 2] == ','):
                            value = value[:left] + '\'' + value[left + 1: right].replace('\'', '\\\'') + '\'' + value[right + 1:]
                        left = right + 1
                if value == 'nan':
                    value = None
                value = ast.literal_eval(value)
                item[attr] = value
            elif attr == 'author':
                value = str(row[attr])
                values = value.split(',')
                values = [value.split('(')[0].strip() for value in values]
                item[attr] = values
            else:
                value = str(row[attr])
                if attr == 'title':
                    attr = 'name'
                if attr == 'series':
                    value = value[:value.find('#') - 1] if '#' in value else value
                value = value.replace('\n', ' ')
                if value.startswith('\''):
                    value = '"' + value[1:]
                if value == 'nan':
                    value = None
                item[attr] = value
        context.append(item)

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '.json', 'w') as f:
        json.dump(context, f, indent=4)


def find_book_authors():
    with open('../knowledge/books.json', 'r') as f:
        book = json.load(f)
    authors = []
    [authors.extend(book[tid]['author']) for tid in book.keys()]
    authors = list(set(authors))
    with open('../knowledge/people.json', 'r') as f:
        people = json.load(f)
    names = [people[tid]['name'] for tid in people.keys() if 'writer' in people[tid]['profession']]
    interset = [name for name in authors if name in names]
    not_in = list(set(authors) - set(interset))

    print(len(authors))
    print(len(interset))
    print(interset)


def find_book_adaptions():
    with open('../knowledge/books.json', 'r') as f:
        book = json.load(f)
    adaptions = []
    [adaptions.append(book[tid]['name']) for tid in book.keys()]
    adaptions = list(set(adaptions))
    with open('../knowledge/movies.json', 'r') as f:
        movies = json.load(f)
    names = [movies[tid]['name'] for tid in movies.keys()]
    interset = [name for name in adaptions if name in names]
    not_in = list(set(adaptions) - set(interset))    
    with open('../knowledge/books_names.pl', 'w') as f:
        json.dump(adaptions, f, indent=4)
    print(len(adaptions))
    print(len(interset))
    print(interset)


def concat():
    with open('../knowledge/movies.json', 'r') as f:
        movie = json.load(f)
    with open('../knowledge/people.json', 'r') as f:
        person = json.load(f)
    with open('../knowledge/principals.json', 'r') as f:
        principal = json.load(f)
    with open('../knowledge/books.json', 'r') as f:
        book = json.load(f)
    
    total = {}
    total['movie'] = movie
    total['person'] = person
    total['attend_in'] = principal
    total['book'] = book
    with open('../knowledge/knowledge.json', 'w') as f:
        json.dump(total, f, indent=4)


if __name__ == "__main__":
    find_book_adaptions()