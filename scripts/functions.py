import random
import json
from db_connect import MongoDBPipeline

class reasoner():
    def __init__(self, paths:dict):
        self.keep_topic_rate = 0.8
        self.keep_attr_rate = 0.66
        
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


        self.attrs = {'movie': ['plot episode', 'line', 'scene', 'costume', 'language', 'genres', 'rating', 'year', 'award', 'music', 'value expressed', 'characterization', 'technique', 'cinematography', 'editing', 'actor performance', 'adaptation', 'director', 'social impact'],
                      'person':['filmography', 'skill', 'award', 'appearance', 'personal life', 'birth year', 'death year', 'profession', 'works'], 
                      'book': ['storyline', 'writing style', 'symbolism', 'emotion impact', 'social background', 'series', 'author', 'language', 'rating', 'genres', 'characters', 'awards', 'setting', 'description']}
        
        self.round = 1

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
        return self.knowledge.find_one(topic, {'name':name})['tid']
            
    
    def _id_to_name(self, topic:str, ID:str) -> str:
        return self.knowledge.find_one(topic, {'tid':ID})['name']
            

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


    def get_answer(self, predicates:list) -> dict:
        '''
        Given the predicates, tell if there is a question to answer, and find the answer.
        '''
        # Find all questions to answer.
        ask_list = []
        for predicate in predicates:
            if len(predicate['arguments']) > 3 and predicate['arguments'][3] == 'ask':
                ask_list.append(predicate)
        
        if ask_list:
            for item in ask_list:
                item['topic'] = item['arguments'][0]
                item['name'] = item['arguments'][1]
                item['attr'] = item['arguments'][2]
                item['attitude'] = item['arguments'][3]
                item['id'] = self._name_to_id(item['topic'], item['name'])
                item['answer'] = self._look_up(item['topic'], item['id'], item['attr'])
                if type(item['answer']) == list:
                    item['answer'] = ' and '.join(item['answer'])
        
            return [(item['name'], item['attr'], item['answer']) for item in ask_list]
        else:
            return None
    

    def get_next_topic(self, predicates:list) -> tuple:
        '''
        Pick the next topic, and explain why pick it.
        '''
        # Random choose whether to continue the current topic.
        attitude_list = ['positive', 'negative']
        change_topic = True if random.random() > self.keep_topic_rate else False
        change_attr = False if not change_topic and random.random() < self.keep_attr_rate else True
        if change_topic or change_attr:
            attitude_list.append('ask')
        attitude = random.choice(attitude_list)
        reason = ('None', 'None')

        # Remove all predicates without argument.
        predicates = [predicate for predicate in predicates if 'arguments' in predicate]

        # If keep the same topic.
        if not change_topic:
            if not change_attr:
                # Pick one predicate
                next_pred = random.choice(predicates)
                # Go on its topic
                topic = next_pred['arguments'][0]
                name = next_pred['arguments'][1]
                attr = next_pred['arguments'][2]
                user_attitude = next_pred['arguments'][3]
                tid = self._name_to_id(topic, name)
            else:
                # Pick one predicate
                current_pred = random.choice(predicates)
                # Get tis topic, etc.
                topic = current_pred['arguments'][0]
                name = current_pred['arguments'][1]
                user_attitude = current_pred['arguments'][3]
                # Get all discussed attrs if in the same topic
                current_attrs = [pred['arguments'][2] for pred in predicates if pred['arguments'][0] == topic and pred['arguments'][1] == name]
                # Get the ID
                tid = self._name_to_id(topic, name)
                # Get the attrs that has been discussed
                if self.record_list and topic in self.record_list and tid in self.record_list[topic]:
                    discussed_list = list(self.record_list[topic][tid].keys())
                else:
                    discussed_list = []
                discussed_list.extend(current_attrs)
                discussed_list = list(set(discussed_list))
                # Remove the discussed attrs from the optional attr list
                optional_attr = list(set(self.attrs[topic]) - set(discussed_list))
                # Random pick the next attr
                attr = random.choice(optional_attr)
        # If jump to a new topic
        else:
            user_attitude = 'None'
            # Random pick one related topic and its reason from RCC list
            topic, tid, reason = random.choice(self.rcc_list)
            name = self._id_to_name(topic, tid)
            # Get the attrs that has been discussed
            if self.record_list and topic in self.record_list and tid in self.record_list[topic]:
                discussed_list = list(self.record_list[topic][tid].keys())
            else:
                discussed_list = []
            # Remove the discussed attrs from the optional attr list
            optional_attr = list(set(self.attrs[topic]) - set(discussed_list))
            # Random pick the next attr
            attr = random.choice(optional_attr)
        
        # Keep the same attitude
        if topic in self.record_list and tid in self.record_list[topic] and attr in self.record_list[topic][tid]:
            # Search for the records
            prev_talked = self.record_list[topic][tid][attr]
            # rec[1] is "log_from", which could be two values: user or bot.
            prev_talked = [rec for rec in prev_talked if 'bot' == rec[1]]
            if prev_talked:
                attitude = prev_talked[-1][3]
        # Calculate reply attitude
        if 'ask' in [attitude, user_attitude] or change_topic or change_attr:
            if_agree = 'None'
        elif attitude == user_attitude:
            if_agree = 'agree'
        else:
            if_agree = 'disagree'

        # Find possible value for the attr
        answer = self._look_up(topic, tid, attr)
        if type(answer) == list:
            answer = ' and '.join(answer)
        if not answer:
            answer = 'None'
        
        return (topic, tid, attr), (if_agree, attitude, name, attr, answer), reason
    

    def _find_book_relation(self, book_info:dict, topic:str, tid:str, source:str, search_key:str, reason:str, not_in_list:list=[]) -> list:
        '''
        not_in_list: The list of books that asked not to search in the future search
        '''
        rccs = []
        if book_info[search_key]:
            search_item = book_info[search_key]
            if isinstance(search_item, list):
                search_results = self._to_list(self.knowledge.find_data(topic, {search_key:{'$in':search_item}, 'tid':{'$ne':tid}}, {'_id':0, 'tid':1, search_key:1}))
                for result in search_results:
                    target_id = result['tid']
                    not_in_list.append(target_id)
                    intersect_items = list(set(search_item) & set(result[search_key]))
                    rccs.append((topic, target_id, (source, reason + 'and'.join(intersect_items))))
            elif isinstance(search_item, str):
                search_results = self._to_list(self.knowledge.find_data(topic, {search_key:search_item, 'tid':{'$ne':tid}}, {'_id':0, 'tid':1, search_key:1}))
                for result in search_results:
                    target_id = result['tid']
                    not_in_list.append(target_id)
                    rccs.append((topic, target_id, (source, reason + search_item)))
        return not_in_list, rccs
    
    
    def find_rcc(self, topic:str, tid:str) -> list:
        '''
        Find out the RCCs of a specific topic.
        '''
        rccs = []
        source = self._id_to_name(topic, tid)
        if topic == 'movie':
            # Person involved in the movie
            people = self._to_list(self.knowledge.find_data('attend_in', {'movie_tid':tid}, {'_id':0, 'person_tid':1}))
            for person in people:
                pname = self._id_to_name('person', person['person_tid'])
                relation = 'in the movie'
                rccs.append(('person', person['person_tid'], (source, relation)))
                # Movie has same person involved
                movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':person['person_tid'], 'movie_id':{'$ne':tid}}, {'_id':0, 'movie_tid':1}))
                for movie in movies:
                    relation = 'this movie also has ' + pname + ' involved'
                    rccs.append((topic, movie['movie_tid'], (source, relation)))
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
                        rccs.append(('book', book['tid'], (source, relation)))
            # Adapted from this book
            books = self._to_list(self.knowledge.find_one('adaption', {'tid':tid}, {'_id':0, 'from':1}))
            if books:
                for book in books[0]['from']:
                    relation = 'adapted from the book'
                    rccs.append(('book', book['tid'], (source, relation)))

            '''
            if tid in self.knowledge['win_award_movie']:
                for award in self.knowledge['win_award_movie'][tid].keys():
                    # Search the movie that also win this award
                    win_this_award = [movie for movie in self.knowledge['win_award_movie'].keys() if award in self.knowledge['win_award_movie'][movie].keys() and len(self.knowledge['win_award_movie'][movie].keys()) > 1]
                    for movie in win_this_award:
                        if movie != tid:
                            year1, year2 = self.knowledge['win_award_movie'][movie][award]['year'], self.knowledge['win_award_movie'][tid][award]['year']
                            if_winner1, if_winner2 = self.knowledge['win_award_movie'][movie][award]['winner'], self.knowledge['win_award_movie'][tid][award]['winner']
                            category1, category2 = self.knowledge['win_award_movie'][movie][award]['category'], self.knowledge['win_award_movie'][tid][award]['category']
                            if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also win ' + aname + ' award in ' + year1
                                rccs.append((topic, movie, (source, relation)))
                            elif category1 == category2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also win ' + aname + ' award in ' + category1
                                rccs.append((topic, movie, (source, relation)))
                            elif year1 == year2 and category1 == category2:
                                aname = self._id_to_name('award', award)
                                relation = 'this movie also compete for ' + aname + ' award in ' + category1 + ' in ' + year1
                                rccs.append((topic, movie, (source, relation)))
                    # Search the person that also win this award
                    win_this_award = [person for person in self.knowledge['win_award_person'].keys() if award in self.knowledge['win_award_person'][person].keys()]
                    for person in win_this_award:
                        year1, year2 = self.knowledge['win_award_person'][person][award]['year'], self.knowledge['win_award_movie'][tid][award]['year']
                        if_winner1, if_winner2 = self.knowledge['win_award_person'][person][award]['winner'], self.knowledge['win_award_movie'][tid][award]['winner']
                        if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                            aname = self._id_to_name('award', award)
                            relation = 'this one also win ' + aname + ' award in ' + year1
                            rccs.append(('person', person, (source, relation)))
        '''
        if topic == 'person':
            # Movie that the person involved in
            movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':tid}, {'_id':0, 'movie_tid':1}))
            for movie in movies:
                relation = 'this one is involved in this movie'
                rccs.append(('movie', movie['movie_tid'], (source, relation)))
                # Person that is involved in the same movie
                people = self._to_list(self.knowledge.find_data('attend_in', {'movie_tid':movie['movie_tid'], 'person_id':{'$ne':tid}}, {'_id':0, 'person_tid':1}))
                for person in people:
                    mname = self._id_to_name('movie', movie['movie_tid'])
                    relation = 'this person also attends in the movie ' + mname + ' involved'
                    rccs.append((topic, person['person_tid'], (source, relation)))
            # Books wrote by this person
            books = self._to_list(self.knowledge.find_data('book_writer', {'tid':tid}, {'_id':0, 'book':1}))
            for book in books['book']:
                relation = 'wrote by this person'
                rccs.append(('book', book['tid'], (source, relation)))
            '''
            if tid in self.knowledge['win_award_person']:
                for award in self.knowledge['win_award_person'][tid].keys():
                    # Search the movie that also win this award
                    win_this_award = [person for person in self.knowledge['win_award_person'].keys() if award in self.knowledge['win_award_person'][person].keys() and len(self.knowledge['win_award_person'][person].keys()) > 1]
                    for person in win_this_award:
                        if person != tid:
                            year1, year2 = self.knowledge['win_award_person'][person][award]['year'], self.knowledge['win_award_person'][tid][award]['year']
                            if_winner1, if_winner2 = self.knowledge['win_award_person'][person][award]['winner'], self.knowledge['win_award_person'][tid][award]['winner']
                            category1, category2 = self.knowledge['win_award_person'][person][award]['category'], self.knowledge['win_award_person'][tid][award]['category']
                            if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this person also win ' + aname + ' award in ' + year1
                                rccs.append((topic, person, (source, relation)))
                            elif category1 == category2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                                aname = self._id_to_name('award', award)
                                relation = 'this person also win ' + aname + ' award in ' + category1
                                rccs.append((topic, person, (source, relation)))
                            elif year1 == year2 and category1 == category2:
                                aname = self._id_to_name('award', award)
                                relation = 'this person also compete for ' + aname + ' award in ' + category1 + ' in ' + year1
                                rccs.append((topic, person, (source, relation)))
                    # Search the person that also win this award
                    win_this_award = [movie for movie in self.knowledge['win_award_movie'].keys() if award in self.knowledge['win_award_movie'][movie].keys()]
                    for movie in win_this_award:
                        year1, year2 = self.knowledge['win_award_movie'][movie][award]['year'], self.knowledge['win_award_person'][tid][award]['year']
                        if_winner1, if_winner2 = self.knowledge['win_award_movie'][movie][award]['winner'], self.knowledge['win_award_person'][tid][award]['winner']
                        if year1 == year2 and if_winner1 == if_winner2 and if_winner2 == 'True':
                            aname = self._id_to_name('award', award)
                            relation = 'this movie also win ' + aname + ' award in ' + year1
                            rccs.append((topic, movie, (source, relation)))
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
                        relation = 'adapted by this book'
                        rccs.append(('movie', movie['tid'], (source, relation)))
                # Writer -- if in the people list
                people = self._to_list(self.knowledge.find_data('book_writer', {'book.tid':tid}, {'_id':0, 'tid':1}))
                for person in people:
                    relation = 'wrote by this person'
                    rccs.append(('person', person['tid'], (source, relation)))
                    # Movie that adapted by the author's other work
                    movies = self._to_list(self.knowledge.find_data('attend_in', {'person_tid':person['tid']}, {'_id':0, 'movie_tid':1}))
                    movies = [movie['movie_tid'] for movie in movies]
                    adapted_movie = self._to_list(self.knowledge.find_one('adaption', {'from.tid':tid}, {'_id':0, 'tid':1}))
                    if adapted_movie:
                        adapted_movie = adapted_movie[0]['tid']
                    movies = list(set(movies) - set([adapted_movie]))
                    for movie in movies:
                        pname = self._id_to_name('person', person['tid'])
                        relation = 'the story of this movie is also written by ' + pname
                        rccs.append(('movie', movie, (source, relation)))
        return rccs
    

    def remove_discussed_rcc(self, rccs:list) -> list:
        new_rcc = []
        for rcc in rccs:
            topic, tid, (source, _) = rcc
            if topic in self.record_list and tid in self.record_list[topic].keys():
                pass
            else:
                new_rcc.append(rcc)
        
        return new_rcc
    

    def update_predicate(self, predicates:dict):
        '''
        Update the record, adding the extracted user item and new topic to the record list.
        '''
        for predicate in predicates:
            if 'arguments' in predicate:
                user_topic = predicate['arguments'][0]
                user_name = predicate['arguments'][1]
                user_attr = predicate['arguments'][2]
                user_attitude = predicate['arguments'][3]
                user_tid = self._name_to_id(user_topic, user_name)
                self._update_record(user_topic,user_tid, user_attr, user_attitude, None, 'user', self.round)
    

    def update_next(self, topic:tuple, reason:tuple, attitude:str):
        '''
        Update the record, adding the extracted user item and new topic to the record list.
        '''
        topic, tid, attr = topic
        self._update_record(topic, tid, attr, attitude, reason, 'bot', self.round)
        self.round += 1
    
    
    def next_action(self, predicates:list) -> dict:
        '''
        Find out the next step's state, its topic to discuss, and update the conversation states.
        The return would be: 
        1. mode: the mode of reply -- quit, irrelevant, answer or general.
        2. next: the topic to discuss next.
        3. attitude: the attitude towards this topic: positive or nagative, agree or disagree.
        4. reason(optional): if topic changes, how this topic comes out, i.e., the relation of the topic to a former discussed topic.
        5. answer(optional): if answer the question, the answer.
        '''

        # Update predicates to the record
        self.update_predicate(predicates)

        # Check if quit or irrelevant topic.
        preds = [predicate['predicate'] for predicate in predicates]
        if 'quit' in preds:
            return {'Mode': 'quit'}
        if 'irrelevant' in preds:
            mode = 'irrelevant'
        
        # Check if there is a question to answer.
        answer = self.get_answer(predicates)
        if answer:
            mode = 'answer'
        else:
            mode = 'general'

        # Find out the RCC of the user input predicates
        user_rcc = []
        for predicate in predicates:
            if 'arguments' in predicate:
                current_topic = predicate['arguments'][0]
                current_name = predicate['arguments'][1].replace('\\\'', '\'')
                predicate['arguments'][1] = predicate['arguments'][1].replace('\\\'', '\'')
                current_tid = self._name_to_id(current_topic, current_name)
                user_rcc.extend(self.find_rcc(current_topic, current_tid))
        user_rcc.extend(self.rcc_list)
        self.rcc_list = list(set(self.remove_discussed_rcc(user_rcc)))
        
        # Get the next topic and RCC.
        (next_topic, next_tid, next_attr), next_topic_content, reason = self.get_next_topic(predicates)

        new_rcc = self.find_rcc(next_topic, next_tid)

        # Update the logs.
        self.rcc_list = new_rcc
        next_attitude = next_topic_content[-1]
        self.update_next((next_topic, next_tid, next_attr), reason, next_attitude)
        
        ret = {'Mode': mode, 'Next': '[' + ', '.join(next_topic_content) + ']', 'Reason': '[' + ', '.join(reason) + ']', 'Answer': answer}
        return ret
    
    
    def reason(self, input:str):
        '''
        input style: aAA(aaa). bBB(bbb). cCC(ccc).
        output style: a dict of mode and output. None for error cases.
        '''
        
        predicates = [pred.strip(' ') for pred in input.split('.')]
        predicates = [pred for pred in predicates if pred]
        predicates = [predicate.split('(') for predicate in predicates]
        predicate_heads = [{'predicate': predicate[0]} for predicate in predicates]
        for idx, predicate in enumerate(predicates):
            if len(predicate) > 1:
                predicate_heads[idx]['arguments'] = predicate[1].strip(')')
                predicate_heads[idx]['arguments'] = [argument.strip(' \'') for argument in predicate_heads[idx]['arguments'].split(',')]
        predicates = predicate_heads
        
        # query for the next move.
        results = self.next_action(predicates)

        return results


if __name__ == "__main__":
    names = ['../data/info_list.pl', '../data/state.pl', '../data/knowledge.pl', '../scripts/functions.pl', '../scripts/query.pl']
    r = reasoner(names)
    result = r.reason('problem(busy).')
    print(result)