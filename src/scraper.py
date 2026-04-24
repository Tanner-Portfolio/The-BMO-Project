import requests
from bs4 import BeautifulSoup
import json
import time
import re

API_URL = "https://adventuretime.fandom.com/api.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_transcript_titles():
    params = {"action": "query", "list": "categorymembers", "cmtitle": "Category:Transcripts", "cmlimit": "500", "format": "json"}
    r = requests.get(API_URL, params=params, headers=HEADERS).json()
    return [m["title"] for m in r.get("query", {}).get("categorymembers", [])]

all_bmo_data = []
titles = get_transcript_titles()

for title in titles:
    slug = title.replace(" ", "_")
    url = f"https://adventuretime.fandom.com/wiki/{slug}"
    print(f"--- Processing: {title} ---")
    
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Get Season/Ep info from the sidebar in the wiki
        sidebar = soup.find("aside")
        meta_info = "Unknown"
        if sidebar:
            meta_text = sidebar.get_text()
            m = re.search(r"Season\s\d+,\sepisode\s\d+", meta_text)
            if m: meta_info = m.group(0)

        # Grab all dialogue tags
        lines = soup.find_all(['dd', 'p', 'li'])
        
        for i, line in enumerate(lines):
            text = line.get_text().strip()
            
            if re.search(r'^BMO\b', text, re.IGNORECASE):
                # CONTEXT: Get the line before BMO spoke
                context = lines[i-1].get_text().strip() if i > 0 else "None"
                # Clean out speaker names from context (e.g., "Finn: Hey BMO" -> "Hey BMO")
                context = context.split(":", 1)[-1].strip()
                
                # Get BMO's actual words from response
                if ":" in text:
                    response = text.split(":", 1)[1].strip()
                    response = re.sub(r'\[.*?\]', '', response).strip() # Remove actions
                    
                    if response:
                        print(f"  [FOUND]: {response[:30]}...")
                        all_bmo_data.append({
                            "metadata": {"episode": title, "info": meta_info},
                            "instruction": context,
                            "response": response
                        })
        time.sleep(0.5) 
    except: continue

with open("bmo_soul_v5.jsonl", "w") as f:
    for entry in all_bmo_data:
        f.write(json.dumps(entry) + "\n")

print(f"\nSUCCESS! Found {len(all_bmo_data)} lines with context.")
