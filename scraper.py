import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime 

# --- CONFIGURATION (CRUCIAL) ---
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
INDEX_FILE = "index.html"

# FIXED MARKERS (must NOT be empty)
START_MARKER = ""
END_MARKER = ""

# --- HTML CARD TEMPLATE (Unchanged) ---
PROGRAM_CARD_TEMPLATE = """
<div class="wide-card" id="card-{card_id}">
    <header>
        <h1>{title}</h1>
        <h2>{icon_emoji} {location_display}</h2>
    </header>
    
    <div class="detail-group">
        <div class="detail-item">
            <strong>📅 Date:</strong>
            {date_line}
        </div>
        <div class="detail-item">
            <strong>🕒 Time:</strong>
            {time_line}
        </div>
    </div>

    <a href="{register_link}" class="action-button" target="_blank">Register Now ♡</a>
    <div class="reindeer-icon"></div>
</div>
"""


def generate_card_html(title, date_time, location, register_link):
    card_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    parts = date_time.split(' | ')
    date_line = parts[0].strip()
    time_line = parts[1].strip() if len(parts) > 1 else "See Details"
    
    location_parts = [p.strip() for p in location.split(',')]
    location_display = location_parts[0] if location_parts and location_parts[0] else "See Details"
    
    icon_emoji = "💻" if "online" in location.lower() else "📍"

    return PROGRAM_CARD_TEMPLATE.format(
        card_id=card_id,
        title=title,
        icon_emoji=icon_emoji,
        location_display=location_display,
        date_line=date_line,
        time_line=time_line,
        register_link=register_link
    )


def scrape_and_update_index():
    print("Scraping...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(AOL_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {AOL_URL}: {e}")
        return

    programs = []

    # Use the 'Register' button as the most reliable anchor
    register_links = soup.find_all('a', string=re.compile(r'Register', re.IGNORECASE))
    
    for link_tag in register_links:
        register_link = link_tag['href']
        
        # Find the main program container (may be views-row or a generic parent div)
        program_element = link_tag.find_parent('div', class_=lambda x: x and ('views-row' in x or 'course-item' in x))
        if not program_element:
            program_element = link_tag.find_parent('div') 
        
        if not program_element:
            continue
        
        # Data Extraction: Title (look for h3/h4/strong text)
        title_tag = program_element.find(lambda tag: tag.name in ['h3', 'h4'] and len(tag.text.strip()) > 10)
        title = title_tag.text.strip() if title_tag else "Program Title Unknown"

        # Data Extraction: Date/Time (using complex regex on the whole block's text)
        raw_text = program_element.get_text(" ", strip=True)
        date_time_text = "Date/Time Details Missing"
        
        dt_match = re.search(r'(\d{1,2}-\d{1,2}\s+[A-Za-z]{3},\s*\d{4}.*?)(\s*\|\s*.*?|\s+various\s+timings|\s*\d{1,2}:\d{2}\s+[AP]M\s*-\s*\d{1,2}:\d{2}\s+[AP]M.*?)', raw_text, re.IGNORECASE | re.DOTALL)
        
        if dt_match:
            date_part = dt_match.group(1).strip()
            # Use group 2 if it exists, otherwise assume time is part of group 1 if it contains time data
            time_part = dt_match.group(2).strip() if dt_match.group(2) else "See Details"
            date_time_text = f"{date_part} | {time_part.lstrip('|').strip()}"
        
        # Data Extraction: Location (Simple check for online/pincode/known keywords)
        location_text = "Location/Mode Details Missing"
        
        loc_match = re.search(r'(Online|[\w\s]+,\s*India\s*-\s*\d{6})', raw_text, re.IGNORECASE)
        if loc_match:
            location_text = loc_match.group(0).strip()
        elif "online" in raw_text.lower():
            location_text = "Online"
            
        programs.append(generate_card_html(title, date_time_text, location_text, register_link))

    # Inject into index.html
    if not programs:
        print("Warning: Scraper found 0 programs, injecting empty content block.")

    try:
        with open(INDEX_FILE, "r") as f:
            content = f.read()

        start = content.find(START_MARKER)
        end = content.find(END_MARKER)

        if start == -1 or end == -1:
            print("FATAL ERROR: Markers missing in index.html. Aborting.")
            return
        
        # CORRECT INJECTION LOGIC: Replaces content *between* markers, keeps markers intact.
        start_of_injection = start + len(START_MARKER)
        
        new_content_block = "\n" + "\n".join(programs) + "\n"
        
        updated = (
            content[:start_of_injection] + 
            new_content_block +
            content[end:]
        )

        with open(INDEX_FILE, "w") as f:
            f.write(updated)

        print(f"Updated index.html successfully with {len(programs)} programs.")

    except Exception as e:
        print(f"An error occurred during file update: {e}")


if __name__ == "__main__":
    scrape_and_update_index()
