import ast
with open('output.txt', 'r') as f:
    s = f.read().replace('true', 'True').replace('false', 'False')
    data = eval(s)
    print('Flights:', len(data['flights']))
    if len(data['flights']) > 0:
        print(data['flights'][0])
