import requests
from bs4 import BeautifulSoup
import re # Import the regular expression module for pattern matching

# The URL of the website you want to scrape
url = 'https://www.aectech.us/hackathon-archive'

# The specific style attribute value you are looking for in paragraphs
target_style = "white-space:pre-wrap;"

# List to store the structured data for each project group
# Each item in the list will be a dictionary representing a group
project_groups = []

try:
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    response.raise_for_status()

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all <p> tags with the target style
    # BeautifulSoup's find_all returns elements in document order, which is crucial here
    all_target_paragraphs = soup.find_all('p', style=target_style)

    # Variables to hold the data for the current group being built
    current_github_url = None
    current_group_paragraphs = []

    # Iterate through the found paragraphs in document order
    for p_tag in all_target_paragraphs:
        # Check if this paragraph contains an <a> tag with an href pointing to GitHub
        # We use re.compile for a case-insensitive check for 'github.com' anywhere in the href
        github_link = p_tag.find('a', href=re.compile(r'github\.com', re.IGNORECASE))

        if github_link:
            # --- Found a paragraph with a GitHub link, potentially starting a new group ---

            # If we were already building a previous group, save it first
            # This condition handles the case where we transition from one group to the next
            if current_github_url is not None or current_group_paragraphs:
                 project_groups.append({
                    'github_url': current_github_url,
                    'paragraphs': current_group_paragraphs
                })

            # Start a new group
            # Extract the href attribute as the group's GitHub URL
            current_github_url = github_link['href']
            # Initialize the list for the new group's paragraphs and add the current paragraph's text
            current_group_paragraphs = [p_tag.get_text()]

        else:
            # --- This paragraph does NOT contain a GitHub link ---

            # If we are currently building a group (i.e., we've found a GitHub link previously),
            # add this paragraph's text to the current group.
            # This assumes that paragraphs with the target style that don't have a GitHub link
            # belong to the most recently started group.
            if current_group_paragraphs is not None:
                 current_group_paragraphs.append(p_tag.get_text())
            # Note: If a paragraph with the target style appears *before* any GitHub link,
            # it will be added to an initial group where current_github_url is None.
            # This behavior aligns with collecting all target style paragraphs,
            # attributing subsequent ones to the latest encountered GitHub URL.

    # --- After the loop, check if there's a last group that hasn't been saved ---
    # This handles the case of the very last group in the document
    if current_github_url is not None or current_group_paragraphs:
         project_groups.append({
            'github_url': current_github_url,
            'paragraphs': current_group_paragraphs
        })

    # --- Print the extracted data in a structured way ---
    is_invalid = lambda group: group["github_url"] is None
    assert len(project_groups) > 1
    assert is_invalid(project_groups[0])
    project_groups.pop(0) # O(N) operation unfortunately.
    assert project_groups
    if project_groups:
        print(f"Found {len(project_groups)} potential project groups.")
        
        for i, group in enumerate(project_groups):
            assert not is_invalid(group)
            
            print(f"\n--- Project Group {i+1} ---")
            # Print the GitHub URL for the group
            print(f"GitHub URL: {group.get('github_url', 'No GitHub URL Found for this group')}") # Use .get for safer access
            print(f"Paragraphs in this group ({len(group['paragraphs'])}):")
            # Print each paragraph within the group with indentation
            for j, paragraph_text in enumerate(group['paragraphs']):
                print(f"  Paragraph {j+1}: {paragraph_text}")
            print("-" * 30) # Separator for clarity between groups

    else:
        print("No project groups found based on the criteria.")


except requests.exceptions.RequestException as e:
    print(f"Error fetching the page: {e}")
except Exception as e:
    print(f"An error occurred during parsing or processing: {e}")