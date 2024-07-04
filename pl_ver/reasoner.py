import subprocess
from parsing import add_quote_list, add_quote

class reasoner():
    def __init__(self, paths):
        self.instant_path = paths[0]
        self.record_path = paths[1]
        self.rcc_path = paths[2]
        self.knowledge_path = paths[3]
        self.function_path = paths[4]
        self.extra_path = paths[5]
        self.command_path = paths[6]
        self.recommend_path = paths[7]

        self.round = 0

        with open(self.record_path, 'w') as f:
            f.write('')
        with open(self.rcc_path, 'w') as f:
            f.write('')
        with open(self.extra_path, 'w') as f:
            f.write('')
        with open(self.knowledge_path, 'w') as f:
            f.write('')
    
    def call(self, options: list, num_result):
        parameters = ['scasp']
        parameters.append(num_result)
        parameters.append('--prev_forall')
        parameters.extend(options)
        call = subprocess.Popen(
            parameters, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
            text=True, universal_newlines=True
            )
        
        output, _ = call.communicate(timeout=10800)

        if 'BINDINGS' in output:
            if num_result == '-n1':
                output = output[output.find('BINDINGS') + 10:-2].strip()
                output = output.split('\n')
                output = [item.split(' = ') for item in output]
                output = {name:value.strip() for [name, value] in output}
            elif num_result == '-n0':
                options = []
                output = output.split('ANSWER:')[1:]
                for option in output:
                    opt = option[option.find('BINDINGS') + 10:-2].strip()
                    opt = opt.split('\n')
                    opt = [item.split(' = ') for item in opt]
                    opt = {name:value.strip() for [name, value] in opt}
                    options.append(opt)
                output = options
        elif 'no models' in output:
            output = {}
        
        else:
            output = None

        return output 
    
    
    def reason(self, input:str):
        '''
        input style: aAA(aaa). bBB(bbb). cCC(ccc).
        output style: a dict of mode and output. None for error cases.
        '''
        
        # write the input to the file.
        with open(self.instant_path, 'w') as f:
            f.write(input + '\n')
        
        # query for the next move.
        query = '?- next_action(Mode, Answer, Next, Attitude, If_Agree, Source, Relation).\n'
        round = 'round(' + str(self.round) + ').\n'
        with open(self.command_path, 'w') as f:
            f.write(round + query)
        results = self.call([self.instant_path, self.record_path, self.rcc_path, self.recommend_path, self.knowledge_path, self.extra_path, self.function_path, self.command_path], '-n1')

        return results
    

    def add_record(self, hist:str):
        with open(self.record_path, 'a') as f:
            f.write(hist + '\n')
    

    def write_rcc(self, rccs:str):
        with open(self.rcc_path, 'w') as f:
            f.write(rccs + '\n')
    

    def write_knowledge(self, knowledge:str):
        with open(self.knowledge_path, 'w') as f:
            f.write(knowledge + '\n')
    

    def write_matched_preference(self, preference_dict:dict, recommend_hist:dict):
        pref_str = ''
        for topic in preference_dict:
            for name in preference_dict[topic]:
                num_matched = preference_dict[topic][name]['num_matched']
                reason = preference_dict[topic][name]['reason']
                reason = [add_quote('the ' + topic + ' with ' + re['attr'] + ' ' + re['value']) for re in reason]
                pref_str += 'matched_attr(' + add_quote(topic) + ', ' + add_quote(name) + ', [' + ', '.join(reason) + '], ' + add_quote(str(num_matched)) + ').\n'
        for topic in recommend_hist:
            for name in recommend_hist[topic]:
                pref_str += 'hist_recommend(' + add_quote(topic) + ', ' + add_quote(name) + ').\n'
        
        with open(self.recommend_path, 'w') as f:
            f.write(pref_str)


if __name__ == "__main__":
    names = ['../data/info_list.pl', '../data/state.pl', '../data/knowledge.pl', '../scripts/functions.pl', '../scripts/query.pl']
    r = reasoner(names)
    result = r.reason('problem(busy).')
    print(result)