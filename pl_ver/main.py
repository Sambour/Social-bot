from call_gpt import sentence_diversity, name_correction, update_relation_rules, get_answer, get_reply, chat, keyword_classify
from reasoner import reasoner
from parsing import split_attr_value, add_quote, add_quote_list
from knowledgebase import knowledgebase
from colorama import Fore, Style
from json import loads
import random

import time


def parse_theme(predicates:str, attrs:dict, special_pred:list) -> list:
    
    ret_struct = []
    if '.' not in predicates:
        return ret_struct
    themes = predicates.split('###')
    for theme in themes:
        theme = theme.strip()
        theme_list = {}
        predicates = theme.split('.')
        for predicate in predicates:
            predicate = predicate.strip()
            if predicate in special_pred:
                return [{predicate:[]}]
            if '(' not in predicate:
                continue
            (attr, value) = split_attr_value(predicate)
            if attr == 'talk':
                if value[0] not in attrs:
                    continue
                if len(value) > 2 and value[2] not in attrs[value[0]]:
                    continue
                theme_list.update({attr:value})
            elif attr == 'attitude':
                if len(value) == 1 and value[0] in ['positive', 'negative', 'ask']:
                    theme_list.update({attr:value})
            elif attr == 'content':
                find_flag = False
                for attr in attrs.values():
                    if value[0] in attr:
                        find_flag = True
                        break
                if find_flag and len(value) > 1:
                    if len(value) > 2:
                        value = [value[0], ' '.join(value[1:])]
                    theme_list.update({'content':value})
            elif attr == 'question':
                if len(value) == 1:
                    theme_list.update({attr:value})
            elif attr == 'prefer':
                if (value[0] == 'movie' and value[1] in ['genres', 'actors', 'writers', 'located countries', 'languages', 'directors', 'rating', 'popularity rank']) or (value[0] == 'book' and value[1] in ['genres', 'author', 'popularity rank', 'rating', 'places']):
                    if 'prefer' not in theme_list:
                        theme_list['prefer'] = [value]
                    elif value not in theme_list['prefer']:
                        theme_list['prefer'].append(value)
        ret_struct.append(theme_list)
    return ret_struct


def join_predicates(preds:dict) -> str:
    ret_preds = ''
    for attr, value in preds.items():
        if value:
            ret_preds += attr + '(' + ', '.join([add_quote(v) for v in value]) + '). '
        else:
            ret_preds += attr + '.'
    return ret_preds.strip()

'''
def random_group():
    change_topic = True if random.random() > 0.7 else False
    change_attr = False if not change_topic and random.random() < 0.66 else True
    output = ''
    if not change_topic:
        output += 'continue_topic. '
    if not change_attr:
        output += 'continue_attr.\n'
    return output
'''

if __name__ == '__main__':

    # Initialization
    reasoner_paths = ['../src/info_list.pl', '../src/record.pl', '../src/rcc.pl', '../knowledge/self_knowledge.pl', '../pl_ver/functions.pl', '../pl_ver/extra_rule.pl', '../pl_ver/query.pl', '../src/recm.pl']
    knowledge_paths = {'movie':'../knowledge/movies.json', 'book':'../knowledge/books.json', 'person':'../knowledge/people.json', 'attend_in':'../knowledge/principals.json', 'in theater':'../knowledge/in_theater.json', 'in_theater':'../knowledge/in_theater.json', 'bestseller':'../knowledge/bestseller.json'}
    
    with open('../data/new_examples.txt', 'r') as f:
        coach_context = ''.join(f.readlines())

    pred_attrs = {'movie': ['plot episode', 'line', 'scene', 'costume', 'language', 'genres', 'rating', 'year', 'award', 'music', 'value expressed', 'characterization', 'technique', 'cinematography', 'editing', 'actor performance', 'adaptation', 'director', 'social impact'],
                  'person':['filmography', 'skill', 'award', 'appearance', 'personal life', 'birth year', 'death year', 'profession', 'works'], 
                  'book': ['storyline', 'writing style', 'symbolism', 'emotion impact', 'social background', 'series', 'author', 'language', 'rating', 'genres', 'characters', 'awards', 'setting', 'description']}
    special_preds = ['irrelevant', 'thank', 'quit']

    r = reasoner(reasoner_paths)
    kb = knowledgebase(knowledge_paths)

    log_dict = {}
    pref_dict = {}
    recommend_hist = {}
    theme_list = []
    session_continues = True
    mode = 'recommend'
    confirm = ''
    last_query = 'None'
    extracted_predicates = {}
    reply_predicates = ''
    reply = chat("Hello!")
    start_time = 0
    total = 0

    # Start the dialog loop
    try:
        while(session_continues):
            # input-output interface
            reply = sentence_diversity(reply).strip()
            
            # calculate the time
            end_time = time.time()
            duration = end_time - start_time if r.round != 0 else 0
            total = total + duration
            avg = total / r.round if r.round != 0 else 0

            print('\n' + Fore.RED + 'Time duration for round ' + str(r.round) + ':' + Style.RESET_ALL + str(duration))
            print('\n' + Fore.RED + 'Average time duration:' + Style.RESET_ALL + str(avg))
            
            print('\n' + Fore.YELLOW + 'Bot:' + Style.RESET_ALL)
            print(confirm + reply + Fore.CYAN + '\n\nYou: ' + Style.RESET_ALL)
            r.round += 1
            original_query = input()

            # record start time
            start_time = time.time()
            
            # check if need context and what context
            if mode == 'ask':
                query = '[Question] ' + reply + ' [End Question] ' + '[Main Sentence] ' +  original_query + ' [End Main Sentence]'
            elif mode != 'ask':
                query = '[Context] user said last time: ' + last_query + ' the last sentence generated: ' + reply + ' [End Context] ' + '[Main Sentence] ' +  original_query + ' [End Main Sentence]'

            extracted_themes = keyword_classify(coach_context, query).strip()
            
            # predicates syntax check
            print(Fore.GREEN + '\n[extracted semantics] ' + Style.RESET_ALL + extracted_themes)
            extracted_themes = parse_theme(extracted_themes, pred_attrs, special_preds)

            # log the user reply content
            for theme in extracted_themes:
                if 'content' in theme and 'talk' in theme and len(theme['talk']) > 2:
                    topic = theme['talk'][0]
                    name = theme['talk'][1]
                    attr = theme['talk'][2]
                    if topic not in log_dict:
                        log_dict[topic] = {}
                    if name not in log_dict[topic]:
                        log_dict[topic][name]= {}
                    if attr not in log_dict[topic][name]:
                        log_dict[topic][name][attr] = []
                    log_dict[topic][name][attr].append(', '.join(theme['content'][1:]))
                elif 'prefer' in theme:
                    for prefer in theme['prefer']:
                        topic = prefer[0]
                        attr = prefer[1]
                        value = prefer[2]
                        if topic not in pref_dict:
                            pref_dict[topic] = {}
                        if attr not in pref_dict[topic]:
                            pref_dict[topic][attr]= []
                        if value not in pref_dict[topic][attr]:
                            pref_dict[topic][attr].append(value)
                    theme.pop('prefer')

            extracted_themes = [x for x in extracted_themes if x]
            if len(extracted_themes) > 0 and list(extracted_themes[0].keys())[0] not in special_preds:
                # randomly select one theme from user's response
                random_theme_id = random.randrange(len(extracted_themes))
                extracted_predicates = extracted_themes.pop(random_theme_id)
                # the reply follows this theme
                response_theme = extracted_predicates
                theme_list.extend(extracted_themes)
            # otherwise, randomly pick one theme from the history
            else:
                # extracted_predicates: remains possibility for "irrelevant", etc.
                if len(extracted_themes) > 0:
                    extracted_predicates = extracted_themes.pop()
                else:
                    extracted_predicates = {}
                # response_theme: the theme that should be call by reasoner
                if theme_list:
                    random_theme_id = random.randrange(len(theme_list))
                    response_theme = theme_list.pop(random_theme_id)
                # if finds nothing, the default is the movie Titanic
                else:
                    response_theme = {'talk':['movie', 'Titanic'], 'attitude':['positive']}
                extracted_predicates.update(response_theme)
            print(Fore.GREEN + '\n[chosen theme] ' + Style.RESET_ALL + join_predicates(extracted_predicates))
            print(Fore.GREEN + '\n[response theme] ' + Style.RESET_ALL + join_predicates(response_theme))

            # check matched recommendation numbers
            matched_recommends = kb.preference_match(pref_dict)
            r.write_matched_preference(matched_recommends, recommend_hist)

            if 'talk' in extracted_predicates and extracted_predicates['talk'][0] in pred_attrs.keys():
                # get the name list
                topic = extracted_predicates['talk'][0]
                name = extracted_predicates['talk'][1]
                if len(extracted_predicates['talk']) > 2:
                    attr = extracted_predicates['talk'][2]
                else:
                    attr = random.choice(pred_attrs[topic])
                    extracted_predicates['talk'].append(attr)
                name_list = list(kb.knowledge.find_data(topic, {'name':{'$regex':'^'}}))
                name_list = [l['name'] for l in name_list]

                # predictes-LLM interaction
                if name not in name_list:
                    new_name = name_correction(name, name_list)
                    if new_name:
                        extracted_predicates['talk'][1] = new_name
                num_rules = update_relation_rules(topic, name, attr, name_list, r.extra_path)
            
                # prepare rccs
                rccs = kb.find_rcc(topic, name)
                len_rcc = len(rccs) + num_rules
                rccs = ['rcc(' + str(i + num_rules + 1) + ', ' + ', '.join([add_quote(x) for x in rcc]) + ').' for i, rcc in enumerate(rccs)]
                rccs = '\n'.join(rccs)
                rccs += 'len_rcc(' + str(len_rcc) + ').\n'
                r.write_rcc(rccs)
                
            # log the discussed theme
            if 'quit' not in extracted_predicates and 'irrelevant' not in extracted_predicates:
                hist_dict = {'hist':extracted_predicates['talk'].copy()}
                hist_dict['hist'].insert(0, str(r.round))
                hist_dict['hist'].extend([extracted_predicates['attitude'][0], 'user'])
                r.add_record(join_predicates(hist_dict))
            
                # construct the knowledge input
                if 'ask' in extracted_predicates['attitude']:
                    topic = extracted_predicates['talk'][0]
                    name = extracted_predicates['talk'][1]
                    knowledge = list(kb.knowledge.find_data(topic, {'name':name}))
                    knowledge_str = ''

                    for kn in knowledge:
                        for attr, value in kn.items():
                            if attr == 'tid':
                                continue
                            elif value:
                                if isinstance(value, list):
                                    for v in value:
                                        knowledge_str += 'data_attr(' + add_quote(topic) + ',' + add_quote(name) + ',' + add_quote(attr) + ',' + add_quote(v) + ').\n'
                                else:
                                    knowledge_str += 'data_attr(' + add_quote(topic) + ',' + add_quote(name) + ',' + add_quote(attr) + ',' + add_quote(value) + ').\n'
                    r.write_knowledge(knowledge_str)

            # start reasoning on one theme.
            reply_predicates = r.reason(join_predicates(extracted_predicates))

            # exception: no predicate or unclear error
            if reply_predicates is None or not reply_predicates:
                reply = 'Sorry could you please say that again? I am kind of not catching up with you.'
            
            mode = reply_predicates['Mode'] if 'Mode' in reply_predicates else ''
            print('mode: ', mode)
            answers = reply_predicates['Answer'] if 'Answer' in reply_predicates else ''
            print('answers: ', answers)
            reply_main = reply_predicates['Next'] if 'Next' in reply_predicates else ''
            print('reply_main: ', reply_main)
            attitude = reply_predicates['Attitude'] if 'Attitude' in reply_predicates else ''
            print('attitude: ', attitude)
            if_agree = reply_predicates['If_Agree'] if 'If_Agree' in reply_predicates else ''
            print('if_agree: ', if_agree)
            source_topic = reply_predicates['Source'] if 'Source' in reply_predicates else ''
            print('source_topic: ', source_topic)
            relation = reply_predicates['Relation'] if 'Relation' in reply_predicates else ''
            print('relation: ', relation)
            
            reply_extra = ''

            # mode identify
            if mode == 'quit':
                session_continues = False
                print('\n' + Fore.YELLOW + 'Bot:' + Style.RESET_ALL + '\n' + chat(original_query + 'I have to leave now. Please quit.'))
                continue
            elif mode == 'irrelevant':
                reply_extra = 'Sorry, I am not quite following you. But I really want to discuss with you about that, '
            
            # process the answers/response
            if answers and answers != '[]':
                answers = parse_theme(answers[1:-1] + '.', pred_attrs, special_preds)[0]
                for answer in answers.values():
                    topic, name, attr, ans = answer #loads(add_quote_list(answer).replace("\'", "\""))
                    if ans == 'None':
                        if attr in pred_attrs[topic]:
                            reply_extra += get_answer(topic, name, attr)
                        else:
                            reply_extra += 'Sorry I could not remembered the ' + attr + ' of the ' + topic + ' ' + name + '. And, '
                    else:
                        reply_extra += 'I remembered that the ' + attr + ' of the ' + topic + ' ' + name + ' is "' + ans + '". And, '
            else:
                reply_extra += get_answer('', 'deep_response', query) + '\n'
            
            if mode == 'general':
                # process the main theme
                if source_topic != 'None' and relation != 'None':
                    has_reason = True
                else:
                    has_reason = False
                
                if if_agree:
                    if_agree = if_agree.split('(')[1].split(')')[0]
                attitude = parse_theme(attitude + '.', pred_attrs, special_preds)[0]['attitude'][0]
                new_theme = parse_theme(reply_main + '.', pred_attrs, special_preds)[0]
                topic, name, attr = new_theme['talk']

                # update the bot response to the log
                hist_dict = {'hist':new_theme['talk']}
                hist_dict['hist'].insert(0, str(r.round))
                hist_dict['hist'].extend([attitude, 'bot'])
                r.add_record(join_predicates(hist_dict))
                
                # attitude identify
                if attitude == 'ask':
                    reply = 'How about the ' + attr + ' of ' + topic + ' ' + name + '? Do you like it?'
                else:
                    # get answer from LLM.
                    answer_dict = get_reply(topic, name, attr, attitude, if_agree, log_dict)
                    attitude = answer_dict['attitude']
                    answer = answer_dict['answer']
                    
                    # reply generation
                    reply = answer #'I also want to talk about the ' + attr + ' of ' + topic + ', it ' + answer + '.'
                    '''
                    if attitude == 'positive':
                        reply += 'I really like it.'
                    elif attitude == 'negative':
                        reply += 'I do not like it.'
                    '''

                if has_reason:
                    reply_reason = 'Because you mentioned ' + source_topic + ', it makes me think of ' + ' the ' + topic + ' ' + name + ', since ' + relation + '. '
                    reply = reply_reason + reply
                '''
                if if_agree == 'agree':
                    confirm = choice(['Yeah, ', 'I agree. ', 'Truly. '])
                elif if_agree == 'disagree':
                    confirm = choice(['Sorry but I don\'t think so, ', 'Really? But ', 'Yeah, but '])
                elif if_agree == 'asking':
                    confirm = choice(['Well, ', 'I see. ', 'Got your point. ', 'So '])
                '''
            
            elif mode == 'recommend':
                topic = reply_main.split('recommend(')[1].split(')')[0]
                topic = topic.split(',')
                name = ','.join(topic[1:]).strip()
                topic = topic[0].strip()
                source_topic = source_topic[1:-1]
                # Update recommend history
                if topic not in recommend_hist:
                    recommend_hist[topic] = []
                if name not in recommend_hist[topic]:
                    recommend_hist[topic].append(name)
                # generate response
                reply = 'Do you know the recent ' + topic + ' named ' + name + '? Since you like ' + source_topic + ', so you should like it. '
            
            # Add the extra: irr or answer, etc.
            reply = reply_extra + reply
            
            last_query = join_predicates(extracted_predicates)
    
    finally:
        kb.close_database()
