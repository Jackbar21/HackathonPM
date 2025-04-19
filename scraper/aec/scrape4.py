import requests
from bs4 import BeautifulSoup
from bs4.element import Tag # Corrected import
import re

# The URL of the website you want to scrape
url = 'https://www.aectech.us/hackathon-archive'

# The specific style attribute value for project paragraphs
target_paragraph_style = "white-space:pre-wrap;"

# List to store the structured data for each project group
project_groups = []

try:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all elements that could be relevant:
    # 1. <p> tags with the target style (project paragraphs)
    # 2. <strong> tags (potential award titles)
    all_target_paragraphs = soup.find_all('p', style=target_paragraph_style)
    all_strong_tags = soup.find_all('strong')

    # Combine and sort the elements by their position in the document.
    # This is crucial for correctly associating preceding awards with projects.
    # We'll sort by the 'sourceline' attribute.
    all_elements_to_process = sorted(all_target_paragraphs + all_strong_tags, key=lambda x: getattr(x, 'sourceline', 0))

    # Filter out strong tags that are inside the target style paragraphs.
    # These are potential project titles or inline awards and are handled when processing the paragraph.
    elements_in_order = []
    for element in all_elements_to_process:
        if element.name == 'strong':
             # Check if the strong tag's closest parent <p> has the target style
             parent_p_with_style = element.find_parent('p', style=target_paragraph_style)
             if not parent_p_with_style:
                 # This strong tag is NOT inside a target style p, likely a standalone award title
                 elements_in_order.append(element)
        elif element.name == 'p' and 'style' in element.attrs and element['style'] == target_paragraph_style:
             # This is a target style p tag (could be a project start or continuation)
             elements_in_order.append(element)

    # Variables to hold the data for the current project group being built
    current_github_url = None
    current_project_title = "No Title Found"
    current_project_summary_parts = [] # Use a list to collect summary text from em tags
    current_group_paragraphs_text = [] # Store the full text of each paragraph in the group
    current_standalone_award_title = None # Variable to hold the most recently found standalone award title
    current_project_award = "No Award Found" # The award for the current project group being built

    # Flag to indicate if we are currently collecting data for a project
    is_collecting_project_data = False

    # Iterate through the sorted and filtered elements
    for element in elements_in_order:

        if element.name == 'strong':
            # Found a strong tag that is NOT inside a target style p tag - this is a standalone award title.

            # If we were currently collecting data for a previous project, save it.
            if is_collecting_project_data:
                 project_groups.append({
                    'github_url': current_github_url,
                    'title': current_project_title,
                    'summary': " ".join(current_project_summary_parts).strip(),
                    'paragraphs_text': current_group_paragraphs_text,
                    'award': current_project_award # Include the determined award with the just-finished group
                 })
                 # Reset project data variables, but keep the new standalone award title for the next project
                 current_github_url = None
                 current_project_title = "No Title Found"
                 current_project_summary_parts = []
                 current_group_paragraphs_text = []
                 current_project_award = "No Award Found" # Reset project award
                 is_collecting_project_data = False # Stop collecting data for the previous project

            # Set the current standalone award title. This award will be associated with the *next* project group encountered.
            current_standalone_award_title = element.get_text().strip()


        elif element.name == 'p' and 'style' in element.attrs and element['style'] == target_paragraph_style:
            # Found a paragraph with the target style. This is part of a project entry.

            # Check if this paragraph contains a GitHub link or a strong tag inside it.
            github_link = element.find('a', href=re.compile(r'github\.com', re.IGNORECASE))
            strong_tag_in_p = element.find('strong') # Find strong tag inside this p

            # A new project entry paragraph starts if it has a GitHub link OR a strong tag inside it.
            starts_new_project_entry_paragraph = github_link is not None or strong_tag_in_p is not None

            if starts_new_project_entry_paragraph:
                # --- Found the starting paragraph of a new project entry ---

                # If we were collecting data for a previous project, save it first.
                if is_collecting_project_data:
                     project_groups.append({
                        'github_url': current_github_url,
                        'title': current_project_title,
                        'summary': " ".join(current_project_summary_parts).strip(),
                        'paragraphs_text': current_group_paragraphs_text,
                        'award': current_project_award # Include the determined award with the previous group
                     })
                     # Clear the standalone award title after it's been associated with the saved project
                     current_standalone_award_title = None

                # Start collecting data for a new project
                is_collecting_project_data = True
                current_github_url = github_link['href'] if github_link else None

                # --- Extract the project title and potential inline award from THIS starting paragraph ---
                current_project_title = "No Title Found" # Default title for the new project
                inline_award_text = None # Placeholder for award text found WITHIN this paragraph

                if github_link:
                    # The project title is typically in a strong tag *within* the github link
                    title_strong_tag_in_a = github_link.find('strong')
                    if title_strong_tag_in_a:
                        current_project_title = title_strong_tag_in_a.get_text().strip()

                    # Look for a strong tag *before* the github link within this same paragraph for inline awards
                    # Iterate through the contents of the paragraph to find elements before the link
                    for content in element.contents:
                        if content == github_link:
                            break # Stop when we reach the github link
                        # Corrected the type check here
                        if isinstance(content, Tag) and content.name == 'strong':
                            inline_award_text = content.get_text().strip()
                            # Assuming only one strong tag before the link for inline award
                            break # Stop after finding the first strong before the link


                # Decide the final award for this project group: prioritize preceding standalone award
                final_project_award = current_standalone_award_title
                if final_project_award is None and inline_award_text:
                     final_project_award = inline_award_text

                # Assign the determined award to the current project being built
                current_project_award = final_project_award if final_project_award is not None else "No Award Found"


                # Reset summary and paragraph list for the new project
                current_project_summary_parts = []
                current_group_paragraphs_text = []

                # Add the text of the current paragraph to the new project's paragraph list
                current_group_paragraphs_text.append(element.get_text().strip())

                # Also, check for em tags in this starting paragraph and add to summary parts
                em_tags_in_current = element.find_all('em')
                for em_tag in em_tags_in_current:
                     current_project_summary_parts.append(em_tag.get_text().strip())

            elif is_collecting_project_data:
                 # This is a continuation paragraph for the current project (target style p, but not a new project start)
                 current_group_paragraphs_text.append(element.get_text().strip())
                 # Also check for em tags in this paragraph and add to current group summary parts
                 em_tags_in_current = element.find_all('em')
                 for em_tag in em_tags_in_current:
                      current_project_summary_parts.append(em_tag.get_text().strip())
            # If is_collecting_project_data is False and this is a target style p that doesn't start a new project,
            # it's an unexpected structure based on our current understanding, so we ignore it for grouping.


    # --- After the loop, check if there's a last group that hasn't been saved ---
    if is_collecting_project_data:
         project_groups.append({
            'github_url': current_github_url,
            'title': current_project_title,
            'summary': " ".join(current_project_summary_parts).strip(),
            'paragraphs_text': current_group_paragraphs_text,
            'award': current_project_award # Include the determined award for the last group
        })


    # --- Print the extracted data in a structured way ---
    if project_groups:
        print(f"Found {len(project_groups)} potential project groups.")
        for i, group in enumerate(project_groups):
            print(f"\n--- Project Group {i+1} ---")
            # Print the extracted information
            print(f"GitHub URL: {group.get('github_url', 'No GitHub URL Found')}")
            print(f"Title: {group.get('title', 'No Title Found')}")
            # Print the determined award
            print(f"Award: {group.get('award', 'No Award Found')}")
            print(f"Summary: {group.get('summary', 'No Summary Found')}")
            print(f"All Paragraphs Text in this group ({len(group['paragraphs_text'])}):")
            for j, paragraph_text in enumerate(group['paragraphs_text']):
                print(f"  Paragraph {j+1}: {paragraph_text}")
            print("-" * 30)

    else:
        print("No project groups found based on the criteria.")


except requests.exceptions.RequestException as e:
    print(f"Error fetching the page: {e}")
except Exception as e:
    print(f"An error occurred during parsing or processing: {e}")