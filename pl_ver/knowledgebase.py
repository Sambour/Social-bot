import random
import json
from db_connect import MongoDBPipeline
from extract_titles import extract_imdb_list

class knowledgebase():
    def __init__(self, paths:dict):
        
        self.rcc_list = []
        self.record_list = {}

        #knowledge_path = paths[0]
        #self.extra_path = paths[1]
        self.knowledge = MongoDBPipeline(paths)
        self.db_names = list(paths.keys())

        #with open(knowledge_path, 'r') as f:
        #    self.knowledge = json.load(f)
        #self.knowledge['movies'] = pd.read_csv(movie_path)
        #self.knowledge['people'] = pd.read_csv(people_path)
        #self.knowledge['books'] = pd.read_csv(book_path)

        # Create Intersection Database for Authors in books and movies.
        merge = {
            '$lookup':{
                'from': 'book',
                'localField': 'name',
                'foreignField': 'author',
                'pipeline': [{'$project':{'_id':0, 'tid':1}}],
                'as': 'book_writer'
            }
        }
        self.knowledge.socialbotDB['person'].aggregate(
            [
                merge, 
                {'$project':{'tid':1, 'book_writer':1}}, 
                {'$match':{'book_writer':{'$ne':[]}}}, 
                {'$group':{'_id':'$tid', 'tid':{'$first':'$tid'}, 'book':{'$first':'$book_writer'}}}, 
                {'$out':'book_writer'}
            ]
        )
        self.db_names.append('book_writer')
        
        # Create Intersection Database for movies adapted from books.
        merge = {
            '$lookup':{
                'from': 'book',
                'localField': 'name',
                'foreignField': 'name',
                'let': {'book_id':'$tid'},
                'pipeline': [{'$project':{'_id':0, 'tid':1, 'book_id':1}}],
                'as': 'adaption'
            }
        }

        self.knowledge.socialbotDB['movie'].aggregate(
            [
                merge, 
                {'$match':{'adaption':{'$ne':[]}}}, 
                {'$group':{'_id':'$tid', 'tid':{'$first':'$tid'}, 'from':{'$first':'$adaption'}}}, 
                {'$out':'adaption'}
            ]
        )
        self.db_names.append('adaption')


    def close_database(self):
        self.knowledge.close_database(self.db_names)
    

    def _to_list(self, dataitem):
        if isinstance(dataitem, dict):
            return [dataitem]
        elif dataitem is None:
            return []
        else:
            return list(dataitem)
    

    def _name_to_id(self, topic:str, name:str) -> str:
        result = self.knowledge.find_one(topic, {'name':name})
        if result:
            return result['tid']
        else:
            return None
            
    
    def _id_to_name(self, topic:str, ID:str) -> str:
        result = self.knowledge.find_one(topic, {'tid':ID})
        if result:
            return result['name']
        else:
            return None
            

    def _look_up(self, topic:str, ID:str, attr:str) -> str:
        result = self.knowledge.find_one(topic, {'tid':ID})
        if attr in result:
            return result[attr]
        else:
            return None
        
    
    def _update_record(self, topic:str, ID:str, attr:str, attitude:str, reason:str, log_from:str, round:int):
        if topic not in self.record_list:
            self.record_list[topic] = {}
        if ID not in self.record_list[topic]:
            self.record_list[topic][ID] = {}
        if attr not in self.record_list[topic][ID]:
            self.record_list[topic][ID][attr] = []
        self.record_list[topic][ID][attr].append((round, log_from, reason, attitude))


    def _find_book_relation(self, book_info:dict, topic:str, tid:str, source:str, search_key:str, reason:str, not_in_list:list=[]) -> list:
        '''
        not_in_list: The list of books that asked not to search in the future search
        '''
        rccs = []
        if book_info[search_key]:
            search_item = book_info[search_key]
            if isinstance(search_item, list):
                search_results = self._to_list(self.knowledge.find_data(topic, {search_key:{'$in':search_item}, 'tid':{'$ne':tid}}, {'_id':0, 'name':1, search_key:1}))
                for result in search_results:
                    target_name = result['name']
                    not_in_list.append(target_name)
                    intersect_items = list(set(search_item) & set(result[search_key]))
                    rccs.append((topic, target_name, source, reason + 'and'.join(intersect_items)))
            elif isinstance(search_item, str):
                search_results = self._to_list(self.knowledge.find_data(topic, {search_key:search_item, 'tid':{'$ne':tid}}, {'_id':0, 'tid':1, search_key:1}))
                for result in search_results:
                    target_name = result['name']
                    not_in_list.append(target_name)
                    rccs.append((topic, target_name, source, reason + search_item))
        return rccs, not_in_list
    
    
    def find_rcc(self, topic:str, source:str) -> list:
        '''
        Find out the RCCs of a specific topic.
        '''
        rccs = []
        tid = self._name_to_id(topic, source)
        if topic == 'movie':
            # Person involved in the movie
            people = self._to_list(self.knowledge.find_data('attend_in', {'movie_tid':tid}, {'_id':0, 'person_tid':1}))
            for person in people:
                pname = self._id_to_name('person', person['person_tid'])
                relation = 'in the movie'
                rccs.append(('person', pname, source, relation))
                # Movie has same person involved
                movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':person['person_tid'], 'movie_tid':{'$ne':tid}}, {'_id':0, 'movie_tid':1}))
                for movie in movies:
                    relation = 'this movie also has ' + pname + ' involved'
                    mname = self._id_to_name('movie', movie['movie_tid'])
                    rccs.append((topic, mname, source, relation))
                # Book written by its writer
                books = []
                adaptions = self._to_list(self.knowledge.find_data('adaption', {'tid':person['person_tid']}, {'_id':0, 'from':1}))
                [books.extend(adaption['from']) for adaption in adaptions]
                books = list(set(books))
                for book in books:
                    mname = self._id_to_name(topic, tid)
                    bname = self._id_to_name('book', book['tid'])
                    if mname not in bname and bname not in mname:
                        relation = 'this movie\'s writer, ' + pname + ', also wrote this book'
                        rccs.append(('book', bname, source, relation))
            # Adapted from this book
            books = self._to_list(self.knowledge.find_one('adaption', {'tid':tid}, {'_id':0, 'from':1}))
            if books:
                for book in books[0]['from']:
                    relation = 'adapted from the book'
                    rccs.append(('book', bname, source, relation))

            '''
            if tid in self.knowledge['win_award_movie']:
                for award in self.knowledge['win_award_movie'][tid].keys():
                    # Search the movie that also win this award
                    win_this_award = [movie for movie in self.knowledge['win_award_movie'].keys() if award in self.knowledge['win_award_movie'][movie].keys() and len(self.knowledge['win_award_movie'][movie].keys()) > 1]
                    for movie in win_this_award:
                        if movie != tid:
                            mname = self._id_to_name('movie', movie)
                            year1, year2 = self.knowledge['win_award_movie'][movie][award]['year'], self.knowledge['win_award_movie'][tid][award]['year']
                            if_winner1, if_winner2 = self.knowledge['win_award_movie'][movie][award]['winner'], self.knowledge['win_award_movie'][tid][award]['winner']
                            category1, category2 = self.knowledge['win_award_movie'][movie][award]['category'], self.knowledge['win_award_movie'][tid][award]['category']
                            if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also win ' + aname + ' award in ' + year1
                                rccs.append((topic, mname, source, relation))
                            elif category1 == category2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also win ' + aname + ' award in ' + category1
                                rccs.append((topic, mname, source, relation))
                            elif year1 == year2 and category1 == category2:
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also compete for ' + aname + ' award in ' + category1 + ' in ' + year1
                                rccs.append((topic, mname, source, relation))
                    # Search the person that also win this award
                    win_this_award = [person for person in self.knowledge['win_award_person'].keys() if award in self.knowledge['win_award_person'][person].keys()]
                    for person in win_this_award:
                        pname = self._id_to_name('person', person)
                        year1, year2 = self.knowledge['win_award_person'][person][award]['year'], self.knowledge['win_award_movie'][tid][award]['year']
                        if_winner1, if_winner2 = self.knowledge['win_award_person'][person][award]['winner'], self.knowledge['win_award_movie'][tid][award]['winner']
                        if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                            aname = self._id_to_name('award', award)
                            relation = 'this one also win ' + aname + ' award in ' + year1
                            rccs.append(('person', pname, source, relation))
        '''
        if topic == 'person':
            # Movie that the person involved in
            movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':tid}, {'_id':0, 'movie_tid':1}))
            for movie in movies:
                mname = self._id_to_name('movie', movie['movie_tid'])
                relation = 'this one is involved in this movie'
                rccs.append(('movie', mname, source, relation))
                # Person that is involved in the same movie
                people = self._to_list(self.knowledge.find_data('attend_in', {'movie_tid':movie['movie_tid'], 'person_tid':{'$ne':tid}}, {'_id':0, 'person_tid':1}))
                for person in people:
                    pname = self._id_to_name('person', person['person_tid'])
                    relation = 'this person also attends in the movie ' + mname + ' involved'
                    rccs.append((topic, pname, source, relation))
            # Books wrote by this person
            books = self._to_list(self.knowledge.find_one('book_writer', {'tid':tid}, {'_id':0, 'book':1}))
            if books:
                for book in books[0]['book']:
                    bname = self._id_to_name('book', book['tid'])
                    relation = 'wrote by this person'
                    rccs.append(('book', bname, source, relation))
            '''
            if tid in self.knowledge['win_award_person']:
                for award in self.knowledge['win_award_person'][tid].keys():
                    # Search the movie that also win this award
                    win_this_award = [person for person in self.knowledge['win_award_person'].keys() if award in self.knowledge['win_award_person'][person].keys() and len(self.knowledge['win_award_person'][person].keys()) > 1]
                    for person in win_this_award:
                        if person != tid:
                            pname = self._id_to_name('person', person)
                            year1, year2 = self.knowledge['win_award_person'][person][award]['year'], self.knowledge['win_award_person'][tid][award]['year']
                            if_winner1, if_winner2 = self.knowledge['win_award_person'][person][award]['winner'], self.knowledge['win_award_person'][tid][award]['winner']
                            category1, category2 = self.knowledge['win_award_person'][person][award]['category'], self.knowledge['win_award_person'][tid][award]['category']
                            if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this person also win ' + aname + ' award in ' + year1
                                rccs.append((topic, pname, source, relation))
                            elif category1 == category2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this person also win ' + aname + ' award in ' + category1
                                rccs.append((topic, pname, source, relation))
                            elif year1 == year2 and category1 == category2:
                                aname = self._id_to_name('award', award)
                                relation = 'this person also compete for ' + aname + ' award in ' + category1 + ' in ' + year1
                                rccs.append((topic, pname, source, relation))
                    # Search the person that also win this award
                    win_this_award = [movie for movie in self.knowledge['win_award_movie'].keys() if award in self.knowledge['win_award_movie'][movie].keys()]
                    for movie in win_this_award:
                        mname = self._id_to_name('movie', movie)
                        year1, year2 = self.knowledge['win_award_movie'][movie][award]['year'], self.knowledge['win_award_person'][tid][award]['year']
                        if_winner1, if_winner2 = self.knowledge['win_award_movie'][movie][award]['winner'], self.knowledge['win_award_person'][tid][award]['winner']
                        if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                            aname = self._id_to_name('award', award)
                            relation = 'this movie also win ' + aname + ' award in ' + year1
                            rccs.append((topic, mname, source, relation))
            '''
        if topic == 'book':
            book_info = self.knowledge.find_one(topic, {'tid':tid})
            if book_info:
                # Book that in the same series
                new_rccs, not_in_list = self._find_book_relation(book_info, topic, tid, source, 'series', 'in the same book series, ')
                rccs.extend(new_rccs)
                # Book that written by the same writer (but not in the same series)
                new_rccs, not_in_list = self._find_book_relation(book_info, topic, tid, source, 'author', 'both written by ', not_in_list)
                rccs.extend(new_rccs)
                # Book that is settled in the same place (but not in the same series or by same author)
                new_rccs, not_in_list = self._find_book_relation(book_info, topic, tid, source, 'setting', 'the two stories both took place in ', not_in_list)
                rccs.extend(new_rccs)
                # Book that written in the same genre
                new_rccs, _ = self._find_book_relation(book_info, topic, tid, source, 'genres', 'the two books are both in the same genres, ')
                rccs.extend(new_rccs)
                # Book that win the same award
                new_rccs, _ = self._find_book_relation(book_info, topic, tid, source, 'awards', 'the two books both win the same awards, ')
                rccs.extend(new_rccs)
                # Movie that adapted by this book
                movies = self._to_list(self.knowledge.find_one('adaption', {'from.tid':tid}, {'_id':0, 'tid':1}))
                if movies:
                    for movie in movies[0]:
                        mname = self._id_to_name('movie', movie['tid'])
                        relation = 'adapted by this book'
                        rccs.append(('movie', mname, source, relation))
                # Writer -- if in the people list
                people = self._to_list(self.knowledge.find_data('book_writer', {'book.tid':tid}, {'_id':0, 'tid':1}))
                for person in people:
                    pname = self._id_to_name('person', person['tid'])
                    relation = 'wrote by this person'
                    rccs.append(('person', pname, source, relation))
                    # Movie that adapted by the author's other work
                    movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':person['tid']}, {'_id':0, 'movie_tid':1}))
                    movies = [movie['movie_tid'] for movie in movies]
                    adapted_movie = self._to_list(self.knowledge.find_one('adaption', {'from.tid':tid}, {'_id':0, 'tid':1}))
                    if adapted_movie:
                        adapted_movie = adapted_movie[0]['tid']
                    movies = list(set(movies) - set([adapted_movie]))
                    for movie in movies:
                        mname = self._id_to_name('movie', movie)
                        pname = self._id_to_name('person', person['tid'])
                        relation = 'the story of this movie is also written by ' + pname
                        rccs.append(('movie', mname, source, relation))
        return rccs
    

    def preference_match(self, pref:dict, topic_data:dict={'movie':'in_theater', 'book':'bestseller'}) -> dict:
        '''
        pref: a dict with three levels: topic, attr, value.
        topic_data: {'movie':'in_theater', 'book':'bestseller'}
        '''
        
        # Check prefrence satisfiction one by one.
        matched_dict = {}
        for topic in pref:
            for attr in pref[topic]:
                for value in pref[topic][attr]:
                    if attr == 'popularity rank':
                        if value == 'high':
                            value = {'$lt':10}
                        elif value == 'above average':
                            value = {'$lt':35}
                        elif value == 'any':
                            value = {'$ne':0}
                    elif attr == 'rating':
                        if value == 'high':
                            value = {'$gt':8}
                        elif value == 'above average':
                            value = {'$gt':5.5}
                        elif value == 'any':
                            value = {'$ne':0}
                    matched_topics = self._to_list(self.knowledge.find_data(topic_data[topic], {attr:value}, {'_id':0, 'name':1}))
                    if matched_topics:
                        for matched_topic in matched_topics:
                            name = matched_topic['name']
                            if topic not in matched_dict:
                                matched_dict[topic] = {}
                            if name not in matched_dict[topic]:
                                matched_dict[topic][name] = {}
                            if 'num_matched' not in matched_dict[topic][name]:
                                matched_dict[topic][name]['num_matched'] = 1
                            else:
                                matched_dict[topic][name]['num_matched'] += 1
                            if 'reason' not in matched_dict[topic][name]:
                                matched_dict[topic][name]['reason'] = []
                                matched_dict[topic][name]['reason'].append({'attr':attr, 'value':value})
                            else:
                                matched_dict[topic][name]['reason'].append({'attr':attr, 'value':value})
        return matched_dict
                        
                

if __name__ == "__main__":
    names = ['../data/info_list.pl', '../data/state.pl', '../data/knowledge.pl', '../scripts/functions.pl', '../scripts/query.pl']
    r = knowledgebase(names)
    result = r.reason('problem(busy).')
    print(result)