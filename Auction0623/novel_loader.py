import os
import re
import datetime
from typing import List, Dict, Any

def load_novel() -> List[Dict[str, Any]]:
    """
    Loads all episodes of the novel directly from the files in 'c:\\AI-Agent\\auction'
    starting with '제' and ending with '.txt', sorted by episode number descending (latest first).
    """
    directory = r"c:\AI-Agent\auction"
    novels = []
    if not os.path.exists(directory):
        return novels
        
    for filename in os.listdir(directory):
        if filename.startswith("제") and filename.endswith(".txt"):
            match = re.match(r"제(\d+)화", filename)
            if match:
                ep_num = int(match.group(1))
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Get file modification date
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                    
                    # Clean title: "제1화 _ 대항력 있는 남자, 배당요구 없는 여자" -> "제1화: 대항력 있는 남자, 배당요구 없는 여자"
                    clean_title = filename.replace(".txt", "").strip()
                    if "_" in clean_title:
                        parts = clean_title.split("_", 1)
                        clean_title = f"{parts[1].strip()}" # Just return the episode title part for cleaner presentation
                        
                    novels.append({
                        "episode": ep_num,
                        "title": clean_title,
                        "date": date_str,
                        "content": content
                    })
                except Exception as e:
                    print(f"Error reading novel file {filename}: {e}")
                    
    # Sort by episode descending (recent first)
    novels.sort(key=lambda x: x["episode"], reverse=True)
    return novels

def add_episode(title: str, content: str) -> bool:
    """Mock function kept for compatibility, returns False as uploading is disabled."""
    return False
