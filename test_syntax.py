import re
c=open('templates/b2c_flight_results.html', encoding='utf-8').read()
scripts=re.findall(r'<script.*?>(.*?)</script>', c, flags=re.DOTALL)

for i, s in enumerate(scripts):
    print(f'Script {i} length: {len(s)}')
    # simple brace count
    open_b = s.count('{')
    close_b = s.count('}')
    print(f'  Braces: {open_b} open, {close_b} close')
    if open_b != close_b:
        print(f'  MISMATCH in script {i}!')

