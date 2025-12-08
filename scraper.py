import requests
from bs4 import BeautifulSoup
import re

# --- Configuration ---
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
HTML_FILE = "index.html"
START_MARKER = ""
END_MARKER = ""
# ---------------------

def fetch_programs():
    """Fetches and parses the program data from the Art of Living page."""
    try:
        response = requests.get(AOL_URL, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    program_cards = []
    
    # 🚨 Selector Guidance:
    # 1. Find the main container that holds ALL programs.
    # 2. Find the individual card/program element within that container.
    # 3. Use specific selectors to pull out the Name, Date, Link, and Location.
    
    # Placeholder selectors - replace with actual selectors from the AOL page
    # Example: If programs are inside a div with class 'program-list'
    program_list_container = soup.find('div', class_=re.compile(r'program-list|view-content'))
    if not program_list_container:
        print("Could not find the main program list container. Check the selector.")
        return []

    # Example: If each program is a div with class 'program-card'
    for program_div in program_list_container.find_all('div', class_=re.compile(r'program-card|event-item|program-wrapper')):
        try:
            # 1. Program Title (H2/H3/DIV with class for the name)
            title_tag = program_div.find(re.compile(r'h[1-6]|div'), class_=re.compile(r'program-title|event-name'))
            title = title_tag.get_text(strip=True) if title_tag else "Program"
            
            # 2. Registration Link (A tag)
            link_tag = program_div.find('a', href=True)
            link = link_tag['href'] if link_tag else "#"

            # 3. Dates & Location (often in a p/div tag with details)
            details_tag = program_div.find('div', class_=re.compile(r'program-details|event-details'))
            
            # Use placeholders if details are hard to scrape
            date_time = "Check Registration Link for Details"
            location = "See Link"
            
            if details_tag:
                # Attempt to extract date/time and location from the details
                date_tag = details_tag.find('span', class_=re.compile(r'date-time|event-date'))
                loc_tag = details_tag.find('span', class_=re.compile(r'location|event-location'))
                
                date_time = date_tag.get_text(strip=True) if date_tag else "Dates/Times Unknown"
                location = loc_tag.get_text(strip=True) if loc_tag else "Location/Online Unknown"


            program_cards.append({
                "title": title,
                "date_time": date_time,
                "location": location,
                "link": link
            })
            
        except Exception as e:
            print(f"Skipping program due to error: {e}")
            continue

    return program_cards

def generate_program_html(programs):
    """Generates the HTML card structure for the scraped programs."""
    html_cards = []
    
    if not programs:
        return f"""
        <div class="iphone-frame" id="card-error">
            <header><div class="card-title-group"><h1>Program List</h1></div></header>
            <section>
                <h2>No upcoming programs found.</h2>
                <p class="subtitle">Please check back later or use the direct link below.</p>
                <a href="{AOL_URL}" class="button" target="_blank">View Programs on AOL Site</a>
            </section>
        </div>
        """
        
    for program in programs:
        # Generate HTML based on your existing card structure
        card_html = f"""
<div class="iphone-frame" id="card-{re.sub(r'[^a-z0-9]', '', program['title'].lower())[:15]}">
    <header>
        <div class="card-title-group">
            <h1>{program['title']}</h1>
            <h2>Upcoming Program</h2>
            <p class="subtitle">with Vishal Merani/ Team</p>
        </div>
    </header>

    <section class="course-details">
        <h3>Details from AOL site:</h3>
    </section>

    <section class="schedule-booking">
        <h4>Schedule:</h4>
        <ul class="timeline">
            <li> {program['date_time']} </li>
        </ul>
        <a href="{program['link']}" class="button" target="_blank">Register/Check Details ♡</a>
    </section>

    <section class="logistics-contact">
        <span class="location-text">📍 {program['location']}</span>
    </section>

    <footer>
        <div class="footer"> Updated by Automation 🤖 <br> ॐ Jai Guru Dev ॐ </div>
    </footer>
</div>
"""
        html_cards.append(card_html)
    
    return "\n".join(html_cards)

def update_html_file(program_html):
    """Reads the existing HTML file, injects the new program HTML, and writes it back."""
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {HTML_FILE} not found.")
        return False
        
    start_index = content.find(START_MARKER)
    end_index = content.find(END_MARKER)

    if start_index == -1 or end_index == -1:
        print(f"Error: Markers '{START_MARKER}' or '{END_MARKER}' not found in {HTML_FILE}.")
        return False

    # Insert the new program HTML between the markers
    new_content = (
        content[:start_index + len(START_MARKER)] +
        program_html +
        content[end_index:]
    )

    # Only write if content has changed to avoid unnecessary commits
    if new_content != content:
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully updated {HTML_FILE} with {len(program_html.split('</div>'))} program cards.")
        return True
    else:
        print("No changes in program listings detected. HTML file not modified.")
        return False

if __name__ == "__main__":
    print(f"Starting program scraper for {AOL_URL}...")
    
    # Fetch data
    programs_data = fetch_programs()
    
    # Generate HTML
    program_cards_html = generate_program_html(programs_data)
    
    # Update file (returns True if file was changed)
    update_html_file(program_cards_html)
