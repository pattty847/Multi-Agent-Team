import requests
from bs4 import BeautifulSoup

# Base URLs
base_url = "https://dearpygui.readthedocs.io/en/latest/"
source_url = "https://dearpygui.readthedocs.io/en/latest/_sources/"

# Function to fetch the raw .rst.txt content
def fetch_rst_text(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return ""

# Function to extract all the hrefs from the base index page
def get_all_rst_links(base_url):
    page = requests.get(base_url)
    soup = BeautifulSoup(page.content, "html.parser")
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.html'):
            # Modify the URL to point to the .rst.txt file
            rst_txt_link = href.replace('.html', '.rst.txt')
            links.append(source_url + rst_txt_link)
    return links

# Gather all links
rst_links = get_all_rst_links(base_url)

# Gather all documentation content
full_documentation = ""
for link in rst_links:
    full_documentation += fetch_rst_text(link) + "\n"

# Save all documentation into one file
with open('dearpygui_docs.txt', 'w', encoding='utf-8') as file:
    file.write(full_documentation)

print("Documentation has been saved to 'dearpygui_docs.txt'.")
