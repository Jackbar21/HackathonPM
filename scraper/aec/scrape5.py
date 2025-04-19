import requests
from bs4 import BeautifulSoup
import re
from bs4.element import Tag # Import Tag for type checking

# The URL of the website to scrape
url = 'https://www.aectech.us/hackathon-archive'

# The specific style attribute value for project paragraphs
target_paragraph_style = "white-space:pre-wrap;"

# List to store the extracted project data
project_data = []

try:
    # Fetch the HTML content from the URL
    response = requests.get(url)
    response.raise_for_status() # Raise an exception for bad status codes
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find ONLY the target paragraphs in document order.
    all_target_paragraphs = soup.find_all('p', style=target_paragraph_style)

    # Iterate through the target paragraphs to find main information paragraphs
    for p_tag in all_target_paragraphs:
        anchor_tag = p_tag.find('a') # Find any anchor tag within the paragraph

        # Check if this paragraph contains an anchor tag with a GitHub or Devpost URL
        is_main_info_paragraph = False
        project_url = None
        is_github = False
        is_devpost = False

        if anchor_tag:
            href = anchor_tag.get('href')
            if href:
                # Check if the URL is GitHub or Devpost
                if re.search(r'github\.com', href, re.IGNORECASE):
                    is_main_info_paragraph = True
                    project_url = href
                    is_github = True
                elif re.search(r'devpost\.com', href, re.IGNORECASE):
                    is_main_info_paragraph = True
                    project_url = href
                    is_devpost = True

        if is_main_info_paragraph:
            # --- This paragraph is a main information paragraph, extract data ---

            # Extract the project title from the strong tag INSIDE the anchor tag
            title_strong_tag_in_a = anchor_tag.find('strong')
            project_title = title_strong_tag_in_a.get_text().strip() if title_strong_tag_in_a else "No Title Found"

            # Determine the award: Look for a strong tag in THIS paragraph NOT inside the anchor tag.
            project_award = "No Award Found" # Default award
            # Find all strong tags in the paragraph
            all_strong_tags_in_p = p_tag.find_all('strong')
            for strong_tag_in_p_list in all_strong_tags_in_p:
                 # Check if this strong tag is NOT a descendant of the anchor tag
                 # This identifies strong tags that are siblings or ancestors of the anchor tag, but not within it.
                 # Also ensure it's not the same strong tag as the title strong tag (which is inside the anchor)
                 if not strong_tag_in_p_list.find_parent('a') == anchor_tag and not strong_tag_in_p_list == title_strong_tag_in_a:
                      project_award = strong_tag_in_p_list.get_text().strip()
                      # Assuming only one such strong tag for the award in this paragraph
                      break # Stop after finding the first non-title strong tag outside the anchor


            # --- Extract the Summary from the immediately following paragraph ---
            project_summary = "No Summary Found"
            next_sibling = p_tag.find_next_sibling() # Get the next element in the HTML tree

            # Check if the next sibling is a p tag with the target style
            if isinstance(next_sibling, Tag) and next_sibling.name == 'p' and \
               'style' in next_sibling.attrs and next_sibling['style'] == target_paragraph_style:
                project_summary = next_sibling.get_text().strip()
                if "Team: " in project_summary or "Team " in project_summary:
                    project_summary = "No Summary Found" # Reset if it contains "Team: " as per the requirement

            # Store the extracted data for this project
            project_data.append({
                'url': project_url,
                'is_github_url': is_github,
                'is_devpost_url': is_devpost,
                'title': project_title,
                'award': project_award,
                'summary': project_summary
            })


    # --- Print the extracted data in a structured way ---
    if project_data:
        print(f"Found {len(project_data)} project entries.")
        for i, project in enumerate(project_data):
            print(f"\n--- Project {i+1} ---")
            # Print the extracted information
            print(f"URL: {project.get('url', 'No URL Found')}")
            print(f"Is GitHub URL: {project.get('is_github_url', False)}")
            print(f"Is Devpost URL: {project.get('is_devpost_url', False)}")
            print(f"Title: {project.get('title', 'No Title Found')}")
            print(f"Award: {project.get('award', 'No Award Found')}")
            print(f"Summary: {project.get('summary', 'No Summary Found')}")
            print("-" * 30)

    else:
        print("No project entries found based on the criteria.")


except requests.exceptions.RequestException as e:
    print(f"Error fetching the page: {e}")
except Exception as e:
    print(f"An error occurred during parsing or processing: {e}")