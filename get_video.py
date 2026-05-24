import urllib.request
import re

url = "https://acorn.lk/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    with open('acorn_videos.txt', 'w', encoding='utf-8') as f:
        for line in html.split('\n'):
            if 'video' in line.lower() or 'mp4' in line.lower() or 'webm' in line.lower() or 'vimeo' in line.lower() or 'youtube' in line.lower() or 'iframe' in line.lower():
                f.write(line.strip() + '\n')
except Exception as e:
    print(e)
