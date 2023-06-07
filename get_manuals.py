from typing import List
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import argparse

HEADERS = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0' }

def fccid_code_lookup(company: str) -> str:
    """
    Query the fccid.report website to get a list of grantee codes for companies satisfying the query keyword.
    """
    url = f'https://fccid.report/?s={company}'
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all('h2', class_='dmbs-post-title')
    # get the 3 digit code in the href if url has /code/ in it
    codes = []
    for title in titles:
        if '/code/' in title.a['href']:
            codes.append(title.a['href'].split('/')[-2])
    return codes

def get_fccid_rss(code: str) -> str:
    """
    Query the fccid.io with the code to get the rss feed of the company's products.
    """
    url = f'https://fccid.io/{code}.rss'
    response = requests.get(url, headers=HEADERS)
    return response.text

def get_products(rss: str) -> List[dict]:
    """
    Query the rss feed to get the user manuals of the company's products.
    """
    soup = BeautifulSoup(rss, 'xml')
    items = soup.find_all('item')
    products = []
    for item in items:
        title = item.find('title').text
        link = item.find('link').text
        description = item.find('description').text
        products.append({'title': title, 'description': description, 'link': link, 'manual': None})
    return products

def get_manual_link(link: str) -> str:
    """
    Query the user manual link to get the user manual.
    """
    response = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find a link with "manual" in it
    links = soup.find_all('a')
    manual_link = None
    for link in links:
        if 'manual' in link.text.lower():
            manual_link = link['href']
            break
    if manual_link is None:
        return None
    response =  requests.get(manual_link, headers=HEADERS)
    # Find links with a.btn.btn-info containing ".pdf"
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_='btn btn-info')
    pdf_link = None
    for link in links:
        if '.pdf' in link['href']:
            pdf_link = link['href']
            break
    return pdf_link

def get_all_product_manuals_from_company(company: str) -> List[dict]:
    """
    Given a company name, get all the urls of the user manuals of the company's products.
    """
    codes = fccid_code_lookup(company)
    products = []
    print(f"Found {len(codes)} codes")
    for code in codes:
        rss = get_fccid_rss(code)
        products = get_products(rss)
        print(f"Found {len(products)} products")
        for i, product in enumerate(products):
            print(f"Getting manual for {product['title']}")
            manual_link = get_manual_link(product['link'])
            if manual_link is None:
                continue
            products[i]['manual'] = manual_link
    return products


def download_pdf(url: str, path: str) -> bool:
    """
    Download a pdf file from a url.
    Return True if the download is successful and is a pdf file. Otherwise, return False.
    If path is a directory, the file will be saved in the directory with the same name as the file in the url.
    """
    if url is None:
        return False
    response = requests.get(url, headers=HEADERS)
    # Check if the response is a pdf
    if response.headers['Content-Type'] != 'application/pdf':
        return False
    if os.path.isdir(path):
        path = os.path.join(path, url.split('/')[-1])
    if os.path.exists(path):
        return True
    with open(path, 'wb') as f:
        f.write(response.content)
    return True

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input_file", help="The input file containing the list of companies to download manuals from.")
    arg_parser.add_argument("output_dir", help="The output directory to save the manuals.", default="manuals")
    args = arg_parser.parse_args()

    companies = ""
    with open("companies.txt", "r") as f:
        companies = f.readlines()
    companies = [company.strip() for company in companies]
    for company in tqdm(companies, desc="Companies"):
        print(f"Downloading manuals for {company}")
        products = get_all_product_manuals_from_company(company)
        print(f"Found {len(products)} product manuals")
        if not len(products):
            continue
        if not os.path.exists(f"{args.output_dir}/{company}"):
            os.makedirs(f"{args.output_dir}/{company}")
        for product in tqdm(products, desc="Products"):
            download_pdf(product['manual'], f"{args.output_dir}/{company}")
