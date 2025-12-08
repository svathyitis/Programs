import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# --- CONFIGURATION ---
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
INDEX_FILE = "index.html"
START_MARKER = ""
END_MARKER = ""

# --- HTML CARD TEMPLATE (Guarantees Correct Styling) ---
PROGRAM_CARD_TEMPLATE = """
<div class="iphone-frame" id="card-{card_id}">
    <header>
        <div class="card-title-group">
            <h1>{title}</h1>
            <h2>{icon_emoji} {location_display}</h2>
        </div>
        <div class="reindeer-icon"></div>
    </header>
    
    <h4>📅 Date:</h4>
    <p class="subtitle">{date_line}</p>

    {time_html}

    <section>
        <a href="{register_link}" class="button" target="_blank">Register Now ♡</a>
    </section>
    
    <footer>
        <div class="location-text">
            <strong>Location Details:</strong> {location}
        </div>
        <div class="footer"> ॐ Jai Guru Dev ॐ </div>
    </footer>
</div>
"""
# --- END TEMPLATE ---


def generate_card_html(title, date_time, location, register_link):
    """Generates the HTML structure for a single program card using the fixed template."""

    card_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    # Split date and time for template variables
    parts = date_time.split(' | ')
    date_line = parts[0].strip()
    time_line = parts[1].strip() if len(parts) > 1 else ""

    location_parts = [p.strip() for p in location.split(',')]
    location_display = location_parts[0] if location_parts else "See Details"
    
    is_online = "online" in location.lower()
    icon_emoji = "💻" if is_online else "📍"

    # Conditional Time HTML
    time_html = f'<h4>🕒 Time:</h4><p class="subtitle">{time_line}</p>' if time_line else ''

    # Populate the template
    return PROGRAM_CARD_TEMPLATE.format(
        card_id=card_id,
        title=title,
        icon_emoji=icon_emoji,
        location_display=location_display,
        date_line=date_line,
        time_html=time_html,
        register_link=register_link,
        location=location
    )


# --- MAIN SCRAPING AND FILE UPDATE LOGIC (Same as before, but with robust selectors) ---

def scrape_and_update_index():
    """Fetches data, processes it, and updates the index.html file."""
    
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
        # 2. Find all program listings
        # Find all 'Register' links and get the parent block
        register_buttons = soup.select('a[href]:contains("Register")')
        
        program_elements = []
        for button in register_buttons:
            # Go up two levels to find the main program container (robust guess)
            program_block = button.parent.parent
            if program_block and program_block not in program_elements:
                 program_elements.append(program_block)

        if not program_elements:
            print("Warning: No program elements found. Check the CSS selector in scraper.py.")
            pass 

        for program_element in program_elements:
            # 3. Extract Data

            # Title: Find the first bold text that looks like a title
            title_tag = program_element.find(lambda tag: tag.name in ['h3', 'h4', 'div', 'p'] and len(tag.text.strip()) > 10 and any(keyword in tag.text for keyword in ['Program', 'Meditation', 'Yoga', 'Course']))
            title = title_tag.text.strip() if title_tag else "Program Title Unknown"

            # Register Link
            register_link_tag = program_element.find('a', string=re.compile(r'Register'))
            register_link = register_link_tag['href'] if register_link_tag else "#"

            # Date/Time
            date_time_text = ""
            date_time_match = re.search(r'(\d{1,2}-\d{1,2}\s+[A-Za-z]{3},\s*\d{4}.*?)(\s+various\s+timings|\s*\d{1,2}:\d{2}\s+[AP]M\s*-\s*\d{1,2}:\d{2}\s+[AP]M.*?)', program_element.text, re.IGNORECASE | re.DOTALL)
                
            if date_time_match:
                date_part = date_time_match.group(1).strip()
                time_part = date_time_match.group(2).strip()
                date_time_text = f"{date_part} | {time_part}"
            
            # Location
            location_text = "Location/Mode Details Missing"
            location_tag = program_element.find(lambda tag: re.search(r'\d{6}', tag.text) or re.search(r'Online', tag.text))
            
            if location_tag:
                location_text = location_tag.text.strip()
                # Clean up known unwanted surrounding text (phone, email, price)
                location_text = re.sub(r':\s*\d{10}\s*:\s*[^@\s]+\s*@[^@\s]+\.[^@\s]+', '', location_text, flags=re.DOTALL).strip()
                location_text = re.sub(r'with Vishal Merani.*', '', location_text, flags=re.DOTALL).strip()
                location_text = re.sub(r'₹\s*[\d,]+\*.*', '', location_text, flags=re.DOTALL).strip()
            
            program_cards.append(generate_card_html(
                title=title,
                date_time=date_time_text,
                location=location_text,
                register_link=register_link
            ))

    except Exception as e:
        print(f"An error occurred during parsing: {e}. The structure of the AOL page may have changed.")


    # 4. Read, Inject, and Write back to index.html
    try:
        with open(INDEX_FILE, 'r') as f:
            content = f.read()

        new_content = "\n\n".join(program_cards)
        
        start_index = content.find(START_MARKER)
        end_index = content.find(END_MARKER)

        if start_index == -1 or end_index == -1:
            print(f"Error: Markers not found in {INDEX_FILE}. Aborting update.")
            return

        # Replace old content with new content
        new_file_content = (
            content[:start_index + len(START_MARKER)] + 
            "\n" + new_content + "\n" +
            content[end_index:]
        )

        with open(INDEX_FILE, 'w') as f:
            f.write(new_file_content)

        print(f"Successfully scraped {len(program_cards)} programs and updated {INDEX_FILE}.")

    except IOError as e:
        print(f"File operation error on {INDEX_FILE}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during file processing: {e}")


if __name__ == "__main__":
    scrape_and_update_index()
