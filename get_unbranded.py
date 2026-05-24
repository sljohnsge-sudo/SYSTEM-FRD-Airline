import urllib.request
import re
import urllib.parse

query = "commercial airplane flying over clouds stock video free no watermark"
url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    video_ids = re.findall(r'"videoId":"(.*?)"', html)
    
    unique_ids = []
    for vid in video_ids:
        if len(vid) == 11 and vid not in unique_ids:
            unique_ids.append(vid)
            
    for vid in unique_ids[:5]:
        page = urllib.request.urlopen(f"https://www.youtube.com/watch?v={vid}").read().decode('utf-8')
        title = re.search(r'<title>(.*?)</title>', page).group(1)
        print(f"{vid} : {title}")
except Exception as e:
    print(e)
