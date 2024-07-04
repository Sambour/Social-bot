import subprocess
from parsing import add_quote_list

class reasoner():
    def __init__(self, paths):
        self.instant_path = paths[0]
        self.record_path = paths[1]
        self.rcc_path = paths[2]
        self.knowledge_path = paths[3]
        self.function_path = paths[4]
        self.extra_path = paths[5]
        self.command_path = paths[6]

        with open(self.record_path, 'w') as f:
            f.write('recent_attr([]).')
        with open(self.rcc_path, 'w') as f:
            f.write('recent_rcc([]).')
        with open(self.extra_path, 'w') as f:
            f.write('')
    
    def call(self, options: list, num_result):
        parameters = ['scasp']
        parameters.extend(options)
        parameters.append(num_result)
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
        with open(self.instant_path, 'a') as f:
            f.write(input + '\n')
        
        # query for the next move.
        with open(self.command_path, 'w') as f:
            f.write('?- next_action(Mode, Attitude, Next, Reason, Records, RCCs).\n')
        results = self.call([self.instant_path, self.record_path, self.rcc_path, self.knowledge_path, self.extra_path, self.function_path, self.command_path], '-n1')

        # save the results to result path.
        if results:
            # update discussed attribute records
            if 'Records' in results:
                record = add_quote_list(results['Records'])
                with open(self.record_path, 'w') as f:
                    f.write('recent_attr(' + record + ').\n')
                    
            # update RCC records
            if 'RCCs' in results:
                rcc = add_quote_list(results['RCCs'])
                with open(self.rcc_path, 'w') as f:
                    f.write('recent_rcc(' + rcc + ').\n')

        return results


if __name__ == "__main__":
    names = ['../data/info_list.pl', '../data/state.pl', '../data/knowledge.pl', '../scripts/functions.pl', '../scripts/query.pl']
    r = reasoner(names)
    result = r.reason('problem(busy).')
    print(result)