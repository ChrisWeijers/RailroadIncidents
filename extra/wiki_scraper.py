import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load the abbreviations from the CSV file
file_path = 'railroad_fix/missing_railroad_names.csv'
railroad_data = pd.read_csv(file_path)
railroad_abbreviations = railroad_data.iloc[:, 0].tolist()

# URL template for scraping abbreviations.com
base_url = "https://www.abbreviations.com/acronyms/railroads/{}"

# Dictionary to hold abbreviation matches
matched_abbreviations = {}

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def scrape_page(page_num):
    url = base_url.format(page_num)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve page {page_num}, status code: {response.status_code}")
        return

    # Parse the page content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the tbody containing abbreviation information
    tbody = soup.find('tbody')
    if not tbody:
        print(f"No tbody found on page {page_num}, skipping.")
        return

    # Locate all rows containing abbreviation information within tbody
    rows = tbody.find_all('tr')

    # Extract the abbreviation and its corresponding full name from each row
    local_matches = {}
    for row in rows:
        # Locate the abbreviation link within each <tr>
        abbreviation_tag = row.find('td', class_='tal tm fsl')
        if abbreviation_tag:
            abbreviation_link = abbreviation_tag.find('a')
            if abbreviation_link:
                abbreviation = abbreviation_link.text.strip().upper()
                # Locate the full name of the railroad in the next <td>
                full_name_tag = row.find('td', class_='tal dm fsl')
                if full_name_tag:
                    full_name = full_name_tag.text.strip()

                    # Check if the abbreviation matches one from our CSV file
                    # and has not been added already
                    if abbreviation in railroad_abbreviations and abbreviation not in matched_abbreviations:
                        local_matches[abbreviation] = full_name
                        print(f"Matched on page {page_num}: {abbreviation} -> {full_name}")

    return local_matches


# Using ThreadPoolExecutor to scrape pages concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_page = {executor.submit(scrape_page, page_num): page_num for page_num in range(1, 371)}

    for future in as_completed(future_to_page):
        page_num = future_to_page[future]
        try:
            data = future.result()
            if data:
                matched_abbreviations.update(data)
        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")

# Updating the original CSV file with the matched abbreviations
railroad_data['Full Name'] = railroad_data.iloc[:, 0].map(matched_abbreviations)

# Save the updated CSV file
updated_file_path = 'railroad_fix/updated_railroad_names.csv'
railroad_data.to_csv(updated_file_path, index=False)