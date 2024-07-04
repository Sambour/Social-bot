from call_gpt import sentence_diversity, name_correction, update_relation_rules, get_answer, chat, keyword_classify
#from reasoner import reasoner
from functions import reasoner
from parsing import split_attr_value, add_quote, add_quote_list
from colorama import Fore, Style
from json import loads
import random

'''
def syntax_check(predicates:str, attrs:list) -> str:
    special_pred = ['irrelevant', 'thank', 'quit']
    ret_pred = ''
    if '.' not in predicates:
        return ret_pred
    predicates = predicates.split('.')
    for predicate in predicates:
        if predicate in special_pred:
            ret_pred += predicate + '. '
            continue
        if '(' not in predicate:
            continue
        (attr, value) = split_attr_value(predicate)
        if value[0] not in attrs:
            continue
        if value[2] not in attrs[value[0]] and (len(value) > 3 and value[3] != 'ask'):
            continue
        ret_pred += attr + '(' + ', '.join([add_quote(v) for v in value]) + '). '
    return ret_pred.strip()
'''

def random_group(path):
    attitude_list = ['positive', 'negative']
    change_topic = True if random.random() > 0.8 else False
    change_attr = False if not change_topic and random.random() < 0.66 else True
    if change_topic or change_attr:
        attitude_list.append('ask')
    attitude = random.choice(attitude_list)
    output = 'attitude(\'' + attitude + '\'). '
    if not change_topic:
        output += 'continue_topic. '
    if not change_attr:
        output += 'continue_attr.\n'
    with open(path, 'w') as f:
        f.write(output)


if __name__ == '__main__':
    paths = {'movie':'../knowledge/movies.json', 'book':'../knowledge/books.json', 'person':'../knowledge/people.json', 'attend_in':'../knowledge/principals.json'}
    #paths = ['../src/info_list.pl', '../src/record.pl', '../src/rcc.pl', '../knowledge/knowledge.pl', '../scripts/functions.pl', '../scripts/extra_rule.pl', '../scripts/query.pl']
    person_list_short = '../knowledge/principals_names.pl'
    person_list = '../knowledge/people_names.pl'
    movie_list = '../knowledge/movies_names.pl'
    book_list = '../knowledge/books_names.pl'
    with open('../data/examples.txt', 'r') as f:
        coach_context = ''.join(f.readlines())

    pred_attrs = {'movie': ['plot episode', 'line', 'scene', 'costume', 'language', 'genres', 'rating', 'year', 'award', 'music', 'value expressed', 'characterization', 'technique', 'cinematography', 'editing', 'actor performance', 'adaptation', 'director', 'social impact'],
                  'people':['filmography', 'skill', 'award', 'appearance', 'personal life', 'birth year', 'death year', 'profession', 'works'], 
                  'book': ['storyline', 'writing style', 'symbolism', 'emotion impact', 'social background', 'series', 'author', 'language', 'rating', 'genres', 'characters', 'awards', 'setting', 'description']}
    r = reasoner(paths)

    log_dict = {}
    session_continues = True
    mode = 'recommend'
    confirm = ''
    last_query = 'None'
    query_predicates = ''
    reply_predicates = ''
    reply = chat("Hello!")

    try:
        while(session_continues):
            # input-output interface
            reply = sentence_diversity(reply).strip()
            print('\n' + Fore.YELLOW + 'Bot:' + Style.RESET_ALL)
            print(confirm + reply + Fore.CYAN + '\n\nYou: ' + Style.RESET_ALL)
            original_query = input()
            
            # check if need context and what context
            if mode == 'ask':
                query = '[Question] ' + reply + ' [End Question] ' + '[Main Sentence] ' +  original_query + ' [End Main Sentence]'
            elif mode != 'ask':
                query = '[Context] user said last time: ' + last_query + ' the last sentence generated: ' + reply + ' [End Context] ' + '[Main Sentence] ' +  original_query + ' [End Main Sentence]'

            query_predicates = keyword_classify(coach_context, query).strip()
            
            # predicates syntax check
            print(Fore.GREEN + '\n[extracted semantics] ' + Style.RESET_ALL + query_predicates)
            #query_predicates = syntax_check(query_predicates, pred_attrs)
            #print(Fore.GREEN + '\n[extracted semantics] ' + Style.RESET_ALL + query_predicates)

            # predictes-LLM interaction
            if 'movie' in query_predicates or 'person' in query_predicates or 'book' in query_predicates:
                query_predicates = name_correction(query_predicates, {'movie': movie_list, 'person': person_list_short, 'book': book_list})
                #update_relation_rules(query_predicates, {'movie': movie_list, 'person': person_list_short, 'book': book_list}, r.extra_path)

            #random_group(r.instant_path)
            reply_predicates = r.reason(query_predicates)

            # exception: no predicate or unclear error
            if reply_predicates is None or not reply_predicates:
                reply = 'Sorry could you please say that again? I am kind of not catching up with you.'
            
            mode = reply_predicates['Mode'] if 'Mode' in reply_predicates else 'None'
            print('mode: ', mode)
            reply_main = reply_predicates['Next'] if 'Next' in reply_predicates else 'None'
            print('reply_main: ', reply_main)
            answers = reply_predicates['Answer'] if 'Answer' in reply_predicates else 'None'
            print('answers: ', answers)
            reason = reply_predicates['Reason'] if 'Reason' in reply_predicates else 'None'
            print('reason: ', reason)
            
            reply_extra = ''

            # mode identify
            if mode == 'quit':
                session_continues = False
                print('\n' + Fore.YELLOW + 'Bot:' + Style.RESET_ALL + '\n' + chat(original_query + 'I have to leave now. Please quit.'))
                continue
            elif mode == 'irrelevant':
                reply_extra = 'Sorry, I am not quite following you. But I really want to discuss with you about that, '
            elif mode == 'answer':
                for answer in answers:
                    topic, attr, ans = answer #loads(add_quote_list(answer).replace("\'", "\""))
                    if ans == None:
                        ans = 'I don\'t know'
                    reply_extra += 'I remembered that the ' + attr + ' of the ' + topic + ' is "' + ans + '". And, '
            
            reason = add_quote_list(reason).replace("\'", "\"")
            source_topic, relation = loads(reason)
            if source_topic != 'None' and relation != 'None':
                has_reason = True
            else:
                has_reason = False
            
            reply_main = add_quote_list(reply_main).replace("\'", "\"")
            if_agree, attitude, topic, attr, answer = loads(reply_main)
            
            # attitude identify
            if attitude == 'ask':
                reply = 'How about the ' + attr + ' of ' + topic + '? Do you like it?'
            else:
                # get answer from LLM.
                if answer == 'None':
                    answer_dict = get_answer(topic, attr, attitude, if_agree, log_dict)
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
                reply_reason = 'Because you mentioned ' + relation + ' of ' + source_topic + ', it makes me think of '
                reply = reply_reason + reply
            '''
            if if_agree == 'agree':
                confirm = choice(['Yeah, ', 'I agree. ', 'Truly. '])
            elif if_agree == 'disagree':
                confirm = choice(['Sorry but I don\'t think so, ', 'Really? But ', 'Yeah, but '])
            elif if_agree == 'asking':
                confirm = choice(['Well, ', 'I see. ', 'Got your point. ', 'So '])
            '''
            reply = reply_extra + reply
            
            last_query = query_predicates
    
    finally:
        r.close_database()
