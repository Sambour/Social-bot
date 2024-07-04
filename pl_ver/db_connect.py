import pymongo
import json

class MongoDBPipeline():

    def __init__(self, paths:dict) -> None:
 
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.socialbotDB = myclient["socialbot"]
        [self.create_database(v, k) for k, v in paths.items()]

    def create_database(self, path:list, collname:list) -> pymongo.collection.Collection:
        '''
        path: path to the json file to be loaded
        collname: the name of the collection to be created.
        '''
        coll = self.socialbotDB[collname]

        with open(path) as file:
            data_values = json.load(file)
        coll.insert_many(data_values)

        # Find all lists and ids that should be indexed.
        index_fields = []
        for k, v in data_values[0].items():
            if isinstance(v, list):
                index_fields.append(k)
            elif isinstance(v, str) and 'tid' in v:
                index_fields.append(k)
            elif isinstance(v, str) and 'name' in v:
                index_fields.append(k)

        # prepare index
        for idx in index_fields:
            coll.create_index({idx:1})

    def close_database(self, collnames:list):
        for collname in collnames:
            self.socialbotDB[collname].drop()
    
    def find_data(self, collname, value, opts={"_id":0}):
        return self.socialbotDB[collname].find(value, opts)
    
    def find_one(self, collname, value, opts={"_id":0}):
        return self.socialbotDB[collname].find_one(value, opts)

if __name__ == '__main__':
    paths = {'book': '../knowledge/books.json', 'movie': '../knowledge/movies.json', 'person': '../knowledge/people.json', 'attend_in': '../knowledge/principals.json', 'in_theater': '../knowledge/in_theater.json'}
    mongo = MongoDBPipeline(paths)
    try:
        '''
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

        mongo.socialbotDB['movie'].aggregate(
            [
                merge, 
                {'$match':{'adaption':{'$ne':[]}}}, 
                {'$group':{'_id':'$tid', 'tid':{'$first':'$tid'}, 'from':{'$first':'$adaption'}}}, 
                {'$out':'adaption'}
            ]
        )
        paths.update({'adaption':''})
        '''
        
        output = mongo.find_data('in_theater', {'popularity rank':{'$ne':0}}, {'_id':0, 'name':1})
        output = list(output)
        print(output)
    finally:
        close_list = list(paths.keys())
        close_list.append('in theater')
        mongo.close_database(close_list)