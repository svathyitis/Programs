# --- MAIN SCRAPING AND FILE UPDATE LOGIC (New, highly targeted logic) ---

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
        # Look for the container element that holds all the program blocks.
        # This class name is a strong candidate for an Art of Living/Drupal view list.
        list_container = soup.find('div', class_='view-content') 
        
        if not list_container:
            print("Error: Could not find the main list container ('view-content'). Aborting scrape.")
            return

        # Now, find all the individual program blocks within that container.
        # Programs are often wrapped in a 'views-row' or similar div.
        program_elements = list_container.find_all('div', class_=lambda x: x and ('views-row' in x or 'course-item' in x))

        # FALLBACK: If specific classes fail, rely on finding the Register button and going up
        if not program_elements:
            print("Warning: Specific class selectors failed. Using robust fallback via 'Register' button.")
            register_buttons = list_container.find_all('a', string=re.compile(r'Register', re.IGNORECASE))
            program_elements = [button.find_parent('div', class_=lambda x: x and 'views-row' in x) or button.parent.parent for button in register_buttons]
            # Filter out None/null parents if find_parent fails
            program_elements = [p for p in program_elements if p]


        if not program_elements:
            print("Warning: No program elements found even with fallback. The target structure may have changed entirely.")
            # We still proceed to clear any old content by writing an empty list
            pass 

        for program_element in program_elements:
            # 3. Extract Data

            # Title: Assuming the title is often a high-level element (h3, h4, or a div)
            title_tag = program_element.find(lambda tag: tag.name in ['h3', 'h4', 'div', 'p'] and len(tag.text.strip()) > 10 and any(keyword in tag.text for keyword in ['Program', 'Meditation', 'Yoga', 'Course']))
            title = title_tag.text.strip() if title_tag else "Program Title Unknown"

            # Register Link
            register_link_tag = program_element.find('a', string=re.compile(r'Register', re.IGNORECASE))
            register_link = register_link_tag['href'] if register_link_tag else "#"

            # Date/Time (Using the same reliable regex on the entire block text)
            date_time_text = ""
            date_time_match = re.search(r'(\d{1,2}-\d{1,2}\s+[A-Za-z]{3},\s*\d{4}.*?)(\s+various\s+timings|\s*\d{1,2}:\d{2}\s+[AP]M\s*-\s*\d{1,2}:\d{2}\s+[AP]M.*?)', program_element.text, re.IGNORECASE | re.DOTALL)
                
            if date_time_match:
                date_part = date_time_match.group(1).strip()
                time_part = date_time_match.group(2).strip()
                date_time_text = f"{date_part} | {time_part}"
            
            # Location (Looking for a 6-digit pin code or 'Online')
            location_text = "Location/Mode Details Missing"
            location_tag = program_element.find(lambda tag: re.search(r'\d{6}', tag.text) or re.search(r'Online', tag.text))
            
            if location_tag:
                location_text = location_tag.text.strip()
                # Clean up unwanted data (phone, email, price, teacher name)
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
        # We must still perform file write, even if cards is empty
    
    # ... (File write logic remains the same below) ...
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
    # Ensure this is called outside of the main function if you replaced the whole file.
    # Otherwise, ensure the main call is at the end.
    scrape_and_update_index()
