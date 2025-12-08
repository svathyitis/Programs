import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# --- CONFIGURATION ---
# URL for Vishal Merani's program listings on Art of Living site
AOL_URL = "https://www.artofliving.org/in-en/t/vishal-merani"
INDEX_FILE = "index.html"
START_MARKER = ""
END_MARKER = ""

# --- HELPER FUNCTION FOR HTML CARD GENERATION ---

def generate_card_html(title, date_time, location, register_link):
    """Generates the HTML structure for a single program card."""

    # Clean up the title and create a URL-friendly ID
    card_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    # Parse and format the date/time string for better readability
    # The scraping logic will try to combine date and time.
    date_line, time_line = "", ""
    parts = date_time.split(' | ')
    date_line = parts[0].strip()
    if len(parts) > 1:
        time_line = parts[1].strip()

    # Determine if the program is Online or In-Person for styling/icon
    location_parts = [p.strip() for p in location.split(',')]
    location_display = location_parts[0] if location_parts else "See Details"
    
    # Check if the program is 'Online' or 'In Person' for a subtle icon
    is_online = "online" in location.lower()
    icon_emoji = "💻" if is_online else "📍"

    # Use title as the h1, and the location/mode as the h2
    html_card = f"""
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

    {'<h4>🕒 Time:</h4><p class="subtitle">' + time_line + '</p>' if time_line else ''}

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
    return html_card

# --- MAIN SCRAPING AND FILE UPDATE LOGIC ---

def scrape_and_update_index():
    """Fetches data, processes it, and updates the index.html file."""
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scrape...")
    
    try:
        # 1. Fetch the HTML content
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(AOL_URL, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {AOL_URL}: {e}")
        return

    program_cards = []
    
    # 2. Find all program listings
    # NOTE: This selector is a general guess. If the script fails, 
    # you MUST inspect the live page and update the selector below
    # to the exact CSS class used for each program listing element.
    # Common guesses: 'div.program-card', 'div.course-listing', 'div.views-row'
    
    # Based on the text structure, we look for elements that seem to contain an entire course block.
    # A reliable way is to find a unique attribute or container. We'll use a very broad 
    # selector and then filter based on content if a specific class is unknown.
    
    # Trying to find the main list container, then children
    # Assuming programs are listed under a section or div where the title is the first text
    
    # A slightly more targeted guess: elements containing the Register text are often the program block
    
    try:
        # Look for the section that contains all the courses (e.g., the parent of 'Showing X courses')
        main_container = soup.find('div', class_='view-id-aol_programs_view') # A common pattern on their site
        if not main_container:
             # Try a wider search for all divs that are likely course wrappers
             main_container = soup
             
        # Find all program elements. The actual selector here is crucial. 
        # For this example, I am using a generic selector assuming the course wrapper is a div 
        # with a nested link element (the Register button).
        
        # Searching for the most unique element: the Register link. Then getting its parent.
        # This is a very robust strategy if the element structure is consistent.
        register_buttons = main_container.select('a:contains("Register")')
        
        # We need the parent element that contains all the program data (title, date, location)
        # Assuming the program block is the grand-parent of the register link.
        program_elements = []
        for button in register_buttons:
             # Go up two levels, as the button is often inside a small div
             # If the HTML is: <program_block> ... <div class="button-container"> <a href="...">Register</a> </div> </program_block>
             # Then the program_block is button.parent.parent
            program_block = button.parent.parent
            if program_block not in program_elements:
                 program_elements.append(program_block)


        if not program_elements:
            print("Warning: No program elements found. Check the CSS selector in scraper.py.")
            return

        for program_element in program_elements:
            # 3. Extract Data

            # Title: Assuming the title is the first strong heading element (h3, h4, or just the first big text)
            # Find the first non-small text in the block
            title_tag = program_element.find(lambda tag: tag.name in ['h3', 'h4', 'div'] and len(tag.text.strip()) > 10 and 'Program' in tag.text)
            title = title_tag.text.strip() if title_tag else "Program Title Unknown"

            # Register Link: Use the Register button link
            register_link_tag = program_element.find('a', string=re.compile(r'Register'))
            register_link = register_link_tag['href'] if register_link_tag else "#"

            # Date/Time and Location are usually siblings or in common p/div tags
            # The HTML structure is likely flat (e.g., all fields are just text nodes or simple spans/divs)
            
            # Extract date (e.g., "11-13 Dec, 2025") and time (e.g., "6:30 AM - 8:30 AM")
            date_time_text = ""
            date_tag = program_element.find(lambda tag: re.search(r'\d{1,2}-\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', tag.text, re.IGNORECASE))
            if date_tag:
                 # Clean up the text node to get date and time
                date_time_match = re.search(r'(\d{1,2}-\d{1,2}\s+[A-Za-z]{3},\s*\d{4}.*?)(\s+various\s+timings|\s*\d{1,2}:\d{2}\s+[AP]M\s*-\s*\d{1,2}:\d{2}\s+[AP]M.*?)', program_element.text, re.IGNORECASE | re.DOTALL)
                
                if date_time_match:
                    date_part = date_time_match.group(1).strip()
                    time_part = date_time_match.group(2).strip()
                    date_time_text = f"{date_part} | {time_part}"
                else:
                    # Fallback to just the date tag text, clean up leading/trailing white space
                    date_time_text = date_tag.text.strip()
                    
            # Extract Location (e.g., "Nikoo Homes, Bhartiya City...")
            # Location is often the last text node before the button, and contains commas/addresses
            location_text = "Location/Mode Details Missing"
            # Look for the address-like text which often contains the Pincode (6 digits)
            location_tag = program_element.find(lambda tag: re.search(r'\d{6}', tag.text) or re.search(r'Online', tag.text))
            
            if location_tag:
                location_text = location_tag.text.strip()
                # Clean up other data that might be stuck (e.g., phone numbers, emails, price)
                location_text = re.sub(r':\s*\d{10}\s*:\s*[^@\s]+@[^@\s]+\.[^@\s]+', '', location_text, flags=re.DOTALL).strip()
                location_text = re.sub(r'with Vishal Merani.*', '', location_text, flags=re.DOTALL).strip()
                location_text = re.sub(r'₹\s*[\d,]+\*.*', '', location_text, flags=re.DOTALL).strip()

            
            # Clean up and append the generated HTML card
            program_cards.append(generate_card_html(
                title=title,
                date_time=date_time_text,
                location=location_text,
                register_link=register_link
            ))

    except Exception as e:
        print(f"An error occurred during parsing: {e}. Check the HTML structure of the Art of Living page.")
        # Continue to file operation with whatever was found, or an empty list

    # 4. Read, Inject, and Write back to index.html
    try:
        with open(INDEX_FILE, 'r') as f:
            content = f.read()

        new_content = "\n\n".join(program_cards)
        
        # Find markers
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
