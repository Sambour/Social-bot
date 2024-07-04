import pandas as pd
import json
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


def get_predicates(fname):
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
    with open('../knowledge/' + fname + '.pl', 'w') as f:
        json.dump(names, f, indent=4)
    
    return attrs


def get_book_predicates(fname):
    '''
    This step generates the books' information from a .csv file.
    It also returns all the predicate names as well as their values.
    '''
    data = pd.read_csv('../data/' + fname + '.csv')
    attrs = list(data.columns)
    context = ''
    names = []

    for index, row in data.iterrows():
        context += 'book('
        for attr in attrs:
            if attr in ['genres','characters','awards','setting']:
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
                    value = '\\N'
                context += value + ', '
            else:
                value = str(row[attr])
                if attr == 'series':
                    value = value[:value.find('#') - 1] if '#' in value else value
                if attr == 'author':
                    value = value.split(',')[0]
                    if '(' in value:
                        value = value.split('(')[0].strip()
                value = value.replace('\n', ' ')
                if value == 'nan':
                    value = '\\N'
                if value.startswith('\''):
                    value = '"' + value[1:]
                context += add_quote(value) + ', '
        context = context.strip(', ') + ').\n'

    # Write down the knowledge base to prolog format. The only place to generate knowledge base.
    with open('../knowledge/' + fname + '.pl', 'w') as f:
        f.write(context)
    
    return attrs


def concat():
    with open('../knowledge/movies.pl', 'r') as f:
        movie = f.read()
    with open('../knowledge/people.pl', 'r') as f:
        person = f.read()
    with open('../knowledge/principals.pl', 'r') as f:
        principal = f.read()
    
    total = movie + '\n' + person + '\n' + principal
    with open('../knowledge/knowledge.pl', 'w') as f:
        f.write(total)


if __name__ == "__main__":
    get_book_predicates('modified_books')