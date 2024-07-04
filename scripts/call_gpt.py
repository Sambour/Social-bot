import openai
import os
import json

openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_version = "2024-02-15-preview" 
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")

def sentence_gen(prompt):
    #sleep(60)
    context = '''
    Turn the predicates to the sentence.
    It happens in a chat where you will act as a movie fan talking with one of your friends.
    Note that you should write in a short (with no more than 50 tokens), simple, but oral way, just like our daily chat. 
    Don't be too polite, and say the point of view directly.

    *example*

    talk(movie, Titanic, line, "I'm the king of the world", positive). ### I really like the movie Titanic, especially for the impressive line by Jack, "I'm the king of the world.".

    *start*

    '''

    prompt += ' ###'
    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=[{'role': 'user', 'content': context + prompt}],
                    max_tokens=150, temperature=0.65)
    return prediction['choices'][0]['message']['content']


def keyword_classify(context:str, prompt:str) -> str:

    instructions = '''
You are now a classifier. For each sentence input, output one or **MORE** predicates that the extract the topics of the sentence, the object name, the property it is talking about, the details for this property, and the attitude towards it.
The sentences are about things around movies and books.
The sentence will comes to the "irrelevant" class if it does not fit any of the others.
The user intention for expressing leaving (using "quit") shall also be extracted.
**ONLY** output the topics, properties, and attitudes that listed below.
The topics are:
movie, person, book.
The properties for "movie" predicate are (and only contain):
plot episode, line, scene, costume, language, genres, rating, year, award, music, value expressed, characterization, technique, cinematography, editing, actor performance, adaptation, director, social impact.
The properties for "person" predicates are:
filmography, skill, award, appearance, personal life, birth year, death year, profession, works.
The properties for "book" predicates are:
storyline, writing style, symbolism, emotion impact, social background, series, author, language, rating, genres, characters, awards, setting, description.
The attitude has three values:
positive, negative, ask.

Besides the above topics and properties, you should also capture the detail information about the property. For example, if the user is talking about the episode of one movie, capture it by the predicate that reflects its core meaning. Apply this for other properties as well, like line, characterization, etc.

**Important** Note that the context is only used when you do not know what the pronouns in the main sentence refer to. DO NOT extract pradicates from context, even there is no useful or enough information from the main sentence!!!

'''

    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=[{'role': 'system', 'content': instructions},
                        {'role': 'user', 'content': context + prompt + '->'}],
                    max_tokens=100, temperature=0)
    return prediction['choices'][0]['message']['content']


def sentence_diversity(prompt:str) -> str:
    #sleep(60)
    context = '''
    Rewrite the sentence in a different expression, and check the grammar and spelling, etc.
    If the sentence comes too long and redundant, please make the sentence concise, or summarize several sentences into one where but maintain the meaning unchanged.
    Also, avoid showing any predicate in the rewritten sentence. If the original sentence contains any predicate, turn it into plain text form.
    Make the tone become playful and light.

    *example*

    What can I do for you, sir? -> Hello, what can I help you today?

    What kind of food do you prefer? -> What type of cuisine are you looking for?

    Sorry, I didn't get what you mean. -> Sorry, I didn't understand. Could you please say that again?

    You are welcome. It's my pleasure to help. -> It's my pleasue to be of service.

    *start*

    '''

    prompt += ' ->'
    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=[{'role': 'system', 'content': 'Please complete the following task. Not that the sentence meaning should not be changed.'},
                            {'role': 'user', 'content': context + prompt}],
                    max_tokens=200, temperature=1)
    return prediction['choices'][0]['message']['content']


def name_correction(predicates:str, paths:dict):
    '''predicates: talk(TopicA, NameA, AttrA, ValueA, AttitudeA). talk(TopicB, NameB, AttrB, ValueB, AttitudeB).
    paths: a dictionary of paths (e.g., {"movies": "./movies.json", "people": "./people.json"})'''

    pred_dict = {item:{} for item in paths.keys()}
    predicates = predicates.strip().split('.')[:-1]
    temp_predicates = [predicate.split('(')[1].split(',')[:2] for predicate in predicates]
    for idx, (topic, name) in enumerate(temp_predicates):
        pred_dict[topic.strip(' \'')].update({name.strip(' \''):predicates[idx]})

    instruct = '''
You are now an expert in movies, books, and related people. Now I need you to use your association skills to correct the names.
Find **ONLY** in the below name list that is most similar (and best matched) to the input name.
You should only output the name only, without any other words.
If there is no matched name, output None.

An example: 

input name: Batman: The Begin -> Batman Begins
input name: ArrFST -> None

name list:

'''
    return_value = ''
    for topic, preds in pred_dict.items():
        with open(paths[topic], 'r') as f:
            name_list = json.load(f)
        cur_instruct = instruct + json.dumps(name_list)
        for name, pred in preds.items():
            prediction = openai.ChatCompletion.create(
                engine="AutoConcierge-Long",
                messages=[{'role': 'system', 'content': cur_instruct},
                          {'role': 'user', 'content': 'input name: ' + name + ' -> '}],
                          max_tokens=10, temperature=0)
            
            extracted_name = prediction['choices'][0]['message']['content']
            if extracted_name != 'None':
                return_value += pred.replace(name, extracted_name) + '. '
    
    return return_value


def update_relation_rules(predicates:str, paths:dict, extra_rule_path:str):
    '''predicates: talk(TopicA, NameA, AttrA, ValueA, AttitudeA). talk(TopicB, NameB, AttrB, ValueB, AttitudeB).
    paths: a dictionary of paths (e.g., {"movies": "./movies.json", "people": "./people.json"})'''
    
    pred_dict = {item:[] for item in paths.keys()}
    predicates = predicates.strip().split('.')[:-1]
    predicates = [predicate.split('(')[1].split(',')[:3] for predicate in predicates]
    for topic, name, attr in predicates:
        pred_dict[topic.strip('\'')].append((name.strip(' \''), attr.strip(' \'')))

    instruct = '''
You are now an expert in movies, books, and related people. Now I need you to use your association skills to give the names (one to at most three) **ONLY** in the below name list that is most similar (and best matched) to the input name in terms of the input attribute. You should only output a list of names separated by comma, without any other words.

An example: 

input name: Batman Begins, input attribute: genre -> The Dark Knight
input name: Nicolas Cage, input attribute: skill -> John Malkovich

name list:

'''
    for topic, preds in pred_dict.items():
        with open(paths[topic], 'r') as f:
            name_list = json.load(f)
        cur_instruct = instruct + json.dumps(name_list)
        for (name, attr) in preds:
            prediction = openai.ChatCompletion.create(
                engine="AutoConcierge-Long",
                messages=[{'role': 'system', 'content': cur_instruct},
                          {'role': 'user', 'content': 'input name: ' + name + ', input attribute: ' + attr + ' -> '}],
                          max_tokens=200, temperature=0)
            
            extracted_names = prediction['choices'][0]['message']['content'].split(',')
            for extracted_name in extracted_names:
                rule = 'related(\'' + topic + '\', TID1, \'' + topic + '\', TID2, \'' + attr + '\') :- get_name(\'' + topic + '\', TID1, \'' + name \
                    + '\'), get_name(\'' + topic + '\', TID2, \'' + extracted_name.strip() + '\').'
                with open(extra_rule_path, 'a') as f:
                    f.write(rule + '\n')


def get_answer(topic, attr, attitude, if_agree, log_dict):
    if attitude == 'None':
        attitude = 'positive'
    if topic not in log_dict:
        log_dict[topic] = {}
    if attr not in log_dict[topic]:
        log_dict[topic][attr] = []
    
    instruct = '''
You are now an expert in movies, books, and related people.
Now I need you to use your expert knowledge to answer the question given by user.
You should answer in an informal tune as if you are chatting with a friend, and finally ask back a question.
Note that you should write in a short (with no more than 50 tokens), simple, but oral way, just like our daily chat. 
Don't be too polite, and say the point of view directly.
Only answer for ONE aspect once.
The positive/negative in the prompt indicates that you should say the good point/bad point of the movie or the person, and the agree/disagree indicates you are agreeing the user saying or not.
Use the function "get_reply_of_chatting_in_movie_and_book" to reply.
If you find that this movie/book/person has no positive/negative point to talk, pick another attitude and generate the reply. In this case, you should mark it down to the 'attitude' part of function call. Otherwise, keep the given attitude in the function call.
Don't directly say "I want to discuss blabla with you" at the beginning. Simply mentioned the topic naturally. 

Examples: 

What is one of the most impressive value expressed for Batman Begins? (positive, disagree) -> But I do not think so. I feel like Batman Begins nails it with the whole inner battle vibe. It's not just about taking down bad guys; it's Bruce Wayne wrestling with his own demons, and that's what makes it hit home. Do you have the same feeling as me?

What is one of the most impressive scene for Avatar: The Way of Water? (negative, agree) -> Yes, I agree with you. Especially in the underwater battle sequence, the scene generated by computer CG lacks clarity and intensity. I can hardly focus on the move and action of the characters. How about you? Do you like it?

'''
    prompt = 'What is one of the most impressive ' + attr + ' for ' + topic + '? (' + attitude + ',' + if_agree + ') -> '
    if log_dict[topic][attr]:
        instruct += '''
Note:

Below are discussed in the past. Avoid using similar points as them.

'''
        for idx, item in enumerate(log_dict[topic][attr]):
            instruct += '\n' + str(idx) + '. ' + item

    function = [
    {
        'name': 'get_reply',
        'description': 'Get the reply of the chatting in book/movie domain.',
        'parameters': {
            'type': 'object',
            'properties': {
                'attitude': {
                    'type': 'string',
                    'description': 'The attitude towards this topic, summarized from the answer. Two options: positive or negative.'
                    },
                'answer': {
                    'type': 'string',
                    'description': 'Generated reply to the user.'
                }
            }
        }
    }]
    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=[{'role': 'system', 'content': instruct},
                            {'role': 'user', 'content': prompt}],
                    functions = function,
                    function_call = 'auto',
                    max_tokens=200, temperature=1)
    output = json.loads(prediction['choices'][0]['message']['function_call']['arguments'])
    log_dict[topic][attr].append(output['answer'])
    return output


def chat(prompt:str):
    instruct = 'You are now a big movie fan chatting with a new friend about the movie area. You like reading books as well. You are enthusiastical and active, but don\'t provide make-up information.'
    #sleep(60)
    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=[{'role': 'system', 'content': instruct},
                            {'role': 'user', 'content': prompt}],
                    max_tokens=300, temperature=1)
    output = prediction['choices'][0]['message']['content']
    return output


if __name__ == "__main__":
    prompt = "Hey I like Titanic. Do you know when did Jack and Rose meet?"
    with open('../data/examples.txt', 'r') as f:
        context = ''.join(f.readlines())
    #paths = {'movie': '../knowledge/movies_names.pl', 'person': '../knowledge/principals_names.pl'}
    #output = name_correction(prompt, paths)
    #log = {'Nolan': {'filmography': ['Oh, hands down, it\'s got to be "Inception." This movie just has it all - a mind-bending plot, stellar cast, and visuals that really push the envelope. The way he crafts such complex stories is literally dreamy. It\'s Nolan at his absolute best, mate!']}}
    #output = get_answer('Nolan', 'filmography', log)
    #print(sentence_diversity(output))
    output = keyword_classify(context, prompt)
    print(output)