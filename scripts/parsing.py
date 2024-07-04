def push(obj:any, l:list, depth:int):
    while depth:
        l = l[-1]
        depth -= 1

    l.append(obj)

def parse_parentheses(s:str) -> list:
    groups = []
    depth = 0
    temp = ''

    for char in s:
        if char == '(' or  char =='[':
            push(temp + char, groups, depth)
            push([], groups, depth)
            depth += 1
            temp = ''
        elif char == ')' or  char ==']':
            if depth < 0:
                return None
            push(temp, groups, depth)
            depth -= 1
            temp = char
        else:
            temp += char
    push(temp, groups, depth)
    
    if depth != 0:
        return None
    else:
        return groups

def add_quote(item:str) -> str:
    item = item.replace('\'', '\\\'')
    if item.isdigit():
        return item
    return '\'' + item + '\''

def _cond_add_quote(item):
    if not ('(' in item or ')' in item or '[' in item or ']' in item):
        return add_quote(item)
    else:
        return item

def _add_quote_list_helper(nested:list) -> str:
    ret = ''
    for item in nested:
        if type(item) == list:
            ret += _add_quote_list_helper(item)
        else:
            temp = ','.join([_cond_add_quote(e.strip()) for e in item.split(',')])
            ret += temp
    return ret

def add_quote_list(preds:str) -> str:
    '''
    Given a list of predicates (even nested), add quote to each element.
    '''
    preds = preds.replace('\,', '#\\#')
    nested = parse_parentheses(preds)
    return _add_quote_list_helper(nested).replace('#\\#', '\,')

def split_predicate(preds:str) -> list:
    '''
    input: a string of predicates separated by ','
    '''
    preds = preds.split(')')
    preds.remove('')
    preds = [pred + ')' for pred in preds]
    preds = [pred.strip(', ') for pred in preds]
    return preds

def split_attr_value(pred):
    '''
    input: a predicate
    '''
    pred = pred.split('(')
    attr = pred[0]
    values = pred[1].strip(').')
    values = values.split(',')
    values = [v.strip() for v in values]
    return (attr, values)

def concat_preds(pred, values):
    '''
    concatenate the predicate name with its values to get the full formatted predicate.
    pred: predicate name.
    values: a list of predicate values.
    '''
    result = ''
    value_list = []
    if not values:
        return result
    for item in values:
        value_list.append(',,,'.join(list(item.values())))
    value_list = list(dict.fromkeys(value_list))
    value_list = [item.split(',,,') for item in value_list]
    for item in value_list:
        result += pred + '(' + ','.join([add_quote(value) for value in item]) + '). '
    return result

if __name__ == "__main__":
    txt = '[recommend(name,UnbelievaBOWL!),satisfy_require(establishment,restaurant),satisfy_require(food type,Japanese),satisfy_require(price range,cheap),satisfy_require(customer rating,high),satisfy_require(prefer,sushi)]'
    print(add_quote_list(txt))