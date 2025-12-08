import requests
from bs4 import BeautifulSoup
import re 
from datetime import datetime 

# --- CONFIGURATION (CRUCIAL) ---
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
INDEX_FILE = "index.html"

# FIXED MARKERS (must NOT be empty)
START_MARKER = "<!-- PROGRAM_LIST_START -->"
END_MARKER = "<!-- PROGRAM_LIST_END -->"

# --- HTML CARD TEMPLATE ---
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
    location_display = location.split(',')[0].strip() if ',' in location else location
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

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(AOL_URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    programs = []

    list_container = soup.find('div', class_='view-content')
    if not list_container:
        print("List container not found.")
        return

    items = list_container.find_all('div', class_=lambda x: x and 'views-row' in x)
    for row in items:
        title_tag = row.find('h3')
        title = title_tag.text.strip() if title_tag else "Program"

        link_tag = row.find('a', string=re.compile("Register", re.I))
        register_link = link_tag["href"] if link_tag else "#"

        raw = row.get_text(" ", strip=True)

        dt = "Date Time Not Found"
        match = re.search(r"\d{1,2}-\d{1,2} [A-Za-z]{3}, \d{4}.*", raw)
        if match:
            dt = match.group(0)

        loc = "Location Not Found"
        loc_tag = row.find(string=re.compile(r"\d{6}|Online", re.I))
        if loc_tag:
            loc = loc_tag.strip()

        programs.append(generate_card_html(title, dt, loc, register_link))

    # Inject into index.html
    with open(INDEX_FILE, "r") as f:
        content = f.read()

    start = content.find(START_MARKER)
    end = content.find(END_MARKER)

    if start == -1 or end == -1:
        print("Markers missing in index.html")
        return

    new_block = START_MARKER + "\n" + "\n".join(programs) + "\n" + END_MARKER
    updated = content[:start] + new_block + content[end + len(END_MARKER):]

    with open(INDEX_FILE, "w") as f:
        f.write(updated)

    print("Updated index.html successfully.")


if __name__ == "__main__":
    scrape_and_update_index()
