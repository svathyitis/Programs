import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime # FIX: Ensures 'datetime' is available for use

# --- CONFIGURATION ---
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
INDEX_FILE = "index.html"
START_MARKER = ""
END_MARKER = ""

# --- HTML CARD TEMPLATE (Using the 'wide-card' style for correct display) ---
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
# --- END TEMPLATE ---


def generate_card_html(title, date_time, location, register_link):
    """Generates the HTML structure for a single program card using the fixed template."""

    card_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    # Split date and time for template variables
    parts = date_time.split(' | ')
    date_line = parts[0].strip()
    time_line = parts[1].strip() if len(parts) > 1 else "See Details" 

    location_parts = [p.strip() for p in location.split(',')]
    location_display = location_parts[0] if location_parts else "See Details"
    
    is_online = "online" in location.lower()
    icon_emoji = "💻" if is_online else "📍"

    # Populate the template
    return PROGRAM_CARD_TEMPLATE.format(
        card_id=card_id,
        title=title,
        icon_emoji=icon_emoji,
        location_display=location_display,
        date_line=date_line,
        time_line=time_line, 
        register_link=register_link,
        location=location
    )


# --- MAIN SCRAPING AND FILE UPDATE LOGIC (Robust Program Finding) ---

def scrape_and_update_index():
    """Fetches data, processes it, and updates the index.html file."""
    
    # This line now works because 'datetime' is imported at the top.
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scrape...") 
    
    try:
        # 1. Fetch the HTML content
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(AOL_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {AOL_URL}: {e}")
        return

    program_cards = []
    
    try:
        # 2. Find all program listings using the most reliable class names
        list_container = soup.find('div', class_='view-content') 
        
        if not list_container:
            print("Error: Could not find the main list container ('view-content'). Aborting scrape.")
            return

        program_elements = list_container.find_all('div', class_=lambda x: x and ('views-row' in x or 'course-item' in x))

        # FALLBACK: If specific classes fail, rely on finding the Register button and going up
        if not program_elements:
            print("Warning: Specific class selectors failed. Using robust fallback via 'Register' button.")
            register_buttons = list_container.find_all('a', string=re.compile(r'Register', re.IGNORECASE))
            program_elements = [button.find_parent('div', class_=lambda x: x and 'views-row' in x) or button.parent.parent for button in register_buttons]
            program_elements = [p for p in program_elements if p] # Filter out None

        if not program_elements:
            print("Warning: No program elements found even with fallback. The target structure may have changed entirely.")
            pass 

        for program_element in program_elements:
            # 3. Extract Data

            title_tag = program_element.find(lambda tag: tag.name in ['h3', 'h4', 'div', 'p'] and len(tag.text.strip()) > 10 and any(keyword in tag.text for keyword in ['Program', 'Meditation', 'Yoga', 'Course']))
            title = title_tag.text.strip() if title_tag else "Program Title Unknown"

            register_link_tag = program_element.find('a', string=re.compile(r'Register', re.IGNORECASE))
            register_link = register_link_tag['href'] if register_link_tag else
