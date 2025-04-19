import requests
from bs4 import BeautifulSoup
import re

# The URL of the website you want to scrape
url = 'https://www.aectech.us/hackathon-archive'

# The specific style attribute value you are looking for in paragraphs
target_style = "white-space:pre-wrap;"

# List to store the structured data for each project group
project_groups = []

try:
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    response.raise_for_status()

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all <p> tags with the target style
    # BeautifulSoup's find_all returns elements in document order
    all_target_paragraphs = soup.find_all('p', style=target_style)

    # Variables to hold the data for the current group being built
    current_github_url = None
    current_project_title = "No Title Found" # Initialize title placeholder
    current_project_summary_parts = [] # Use a list to collect summary text from em tags
    current_group_paragraphs_text = [] # Store the full text of each paragraph in the group

    # Iterate through the found paragraphs in document order
    for p_tag in all_target_paragraphs:
        # Check if this paragraph contains a link to GitHub
        github_link = p_tag.find('a', href=re.compile(r'github\.com', re.IGNORECASE))
        # Check if this paragraph contains a strong tag (potential title indicator)
        strong_tag = p_tag.find('strong')

        # Determine if this paragraph starts a new group
        # A new group starts if it has a GitHub link OR a strong tag
        starts_new_group = github_link is not None or strong_tag is not None

        if starts_new_group:
            # --- Found a potential start of a new group ---

            # If there was a previous group being built, save it first
            # This condition handles the transition from one group to the next
            if current_github_url is not None or current_group_paragraphs_text:
                 project_groups.append({
                    'github_url': current_github_url,
                    'title': current_project_title,
                    # Join the collected summary parts into a single string
                    'summary': " ".join(current_project_summary_parts).strip(),
                    'paragraphs_text': current_group_paragraphs_text
                })

            # Start a new group
            # Set the GitHub URL for the new group.
            current_github_url = github_link['href'] if github_link else None

            # Try to find and set the title from the first strong tag in this starting paragraph
            current_project_title = strong_tag.get_text().strip() if strong_tag else "No Title Found"

            # Reset summary and paragraph list for the new group
            current_project_summary_parts = []
            current_group_paragraphs_text = []

            # Add the text of the current paragraph to the new group's paragraph list
            current_group_paragraphs_text.append(p_tag.get_text().strip())

            # Also, check for em tags in this starting paragraph and add to summary parts
            em_tags_in_current = p_tag.find_all('em')
            for em_tag in em_tags_in_current:
                 current_project_summary_parts.append(em_tag.get_text().strip())


        else:
            # --- This paragraph does NOT start a new group ---

            # If we are currently building a group, add this paragraph's text to it
            # This condition ensures we only add to a group that has been initiated
            if current_group_paragraphs_text is not None:
                 current_group_paragraphs_text.append(p_tag.get_text().strip())
                 # Also check for em tags in this paragraph and add to current group summary parts
                 em_tags_in_current = p_tag.find_all('em')
                 for em_tag in em_tags_in_current:
                      current_project_summary_parts.append(em_tag.get_text().strip())


    # --- After the loop, check if there's a last group that hasn't been saved ---
    # This handles the case of the very last group in the document
    if current_github_url is not None or current_group_paragraphs_text:
         project_groups.append({
            'github_url': current_github_url,
            'title': current_project_title,
            'summary': " ".join(current_project_summary_parts).strip(),
            'paragraphs_text': current_group_paragraphs_text
        })


    # --- Print the extracted data in a structured way ---
    if project_groups:
        print(f"Found {len(project_groups)} potential project groups.")
        for i, group in enumerate(project_groups):
            print(f"\n--- Project Group {i+1} ---")
            # Print the extracted information
            print(f"GitHub URL: {group.get('github_url', 'No GitHub URL Found')}")
            print(f"Title: {group.get('title', 'No Title Found')}")
            print(f"Summary: {group.get('summary', 'No Summary Found')}")
            print(f"All Paragraphs in this group ({len(group['paragraphs_text'])}):")
            # Print each full paragraph text within the group
            for j, paragraph_text in enumerate(group['paragraphs_text']):
                print(f"  Paragraph {j+1}: {paragraph_text}")
            print("-" * 30) # Separator for clarity between groups

    else:
        print("No project groups found based on the criteria.")


except requests.exceptions.RequestException as e:
    print(f"Error fetching the page: {e}")
except Exception as e:
    print(f"An error occurred during parsing or processing: {e}")