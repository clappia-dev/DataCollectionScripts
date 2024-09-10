import csv
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

"""
The script will recursively crawl the web page and its child pages, and save the child URLs to a CSV file named 'child_urls.csv'.

To install the required dependencies, run the following command:
pip install -r requirements.txt

To run the script, execute the following command:
python get-all-child-pages.py
"""


def crawl_page(url, visited_urls, child_urls, original_url):
    print(f'Crawling: {url}')
    # Add the current URL to the visited_urls set
    visited_urls.add(url)

    # Send a GET request to the URL
    response = requests.get(url)
    # print('Received response with status code:', response.status_code)

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all anchor tags in the HTML
    for anchor in soup.find_all('a'):
        href = anchor.get('href')

        # Check if the href attribute is present and not empty, also include only the links which start with https:// or /
        if href and href.startswith('https://') or href.startswith('/'):
            # remove the hash from the URL
            href = href.split('#')[0]
            # Join the href with the base URL to get the absolute URL
            absolute_url = urljoin(url, href)

            # Check if the parsed URL is a substring of the original domain
            if absolute_url.startswith(original_url):
                # Check if the absolute URL is not already visited
                if absolute_url not in visited_urls:
                    # Add the absolute URL to the child_urls list
                    child_urls.append(absolute_url)
                    print('Child URL:', absolute_url)

                    # Recursively crawl the child URL
                    crawl_page(absolute_url, visited_urls, child_urls, original_url)

def main():
    # Get the web page URL from the command line input
    url = input("Enter the web page URL: ")
    original_url = url

    # Set up the visited_urls set and child_urls list
    visited_urls = set()
    child_urls = []

    # Crawl the web page and its child pages
    crawl_page(url, visited_urls, child_urls, original_url)

    # Write the child URLs to a CSV file
    with open('child_urls.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Child URLs'])
        writer.writerows([[child_url] for child_url in child_urls])

if __name__ == '__main__':
    main()