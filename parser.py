from query_descriptor import QueryDescriptor
import requests
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from typing import List

base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def build_term_field(desc):
    query_parts = []
    for kw in desc.keywords:
        query_parts.append(f"{kw}")

    if desc.authors:
        for author in desc.authors:
            query_parts.append(f"{author}[Author]")

    if desc.journals:
        for journal in desc.journal:
            query_parts.append(f"{journal}[Journal]")

    return " AND ".join(query_parts)


def run_search_query(desc, retmax=5):
    search_url = f"{base_url}esearch.fcgi"
    term = build_term_field(desc)
    params = {"db": "pubmed", "term": term, "retmode": "json", "retmax": retmax}

    print(desc.dates)
    if len(desc.dates) == 2:
        params["mindate"] = desc.dates[0]
        params["maxdate"] = desc.dates[1]

    response = query(search_url, params)

    data = response.json()
    return data["esearchresult"].get("idlist", [])

def retrieve_articles_data(ids):
    xml_root = run_fetch_query(ids)
    parsed_articles = parse_xml_tree(xml_root)
    return parsed_articles

def run_fetch_query(ids):
    search_url = f"{base_url}efetch.fcgi"
    params = {"db": "pubmed", "retmode": "xml", "id":",".join(ids)}

    response = query(search_url, params)

    root = ET.fromstring(response.text)
    return root

def query(url, params):
    full_url = f"{url}?{urlencode(params, safe='[]')}"
    print(full_url)
    response = requests.get(full_url)
    if response.status_code != 200:
        raise Exception(f"Search failed with status code: {response.status_code}")

    return response

def parse_xml_tree(root: ET.Element) -> List:
    articles = []
    for article in root:
        cur_article = {}

        # Get the title of the article
        article_title = article.find('.//ArticleTitle')
        if article_title is not None:
            cur_article['title'] = article_title.text or None

        # Get name and surname of the authors
        authors = []
        for author in article.findall(".//Author"):
            full_name = ""
            forename = author.find("ForeName")
            lastname = author.find("LastName")
            if lastname is not None:
                full_name += lastname.text
            if forename is not None:
                if full_name:
                    full_name += " "
                full_name += forename.text
            authors.append(full_name)
        cur_article["authors"] = authors

        # Get the abstract
        abstract_text = article.find(".//Abstract/AbstractText")
        if abstract_text is not None:
            cur_article['abstract'] = abstract_text.text or None

        # Get information concerning the Journal
        journal = article.find(".//Journal/Title")
        if journal is not None:
            cur_article["journal"] = journal.text or None

        # Get the submission date of the article
        article_date = article.find(".//ArticleDate")
        if article_date is not None:
            cur_article["date"] = f'{article_date.find("Day").text}/{article_date.find("Month").text}/{article_date.find("Year").text}' or None

        articles.append(cur_article)

    return articles

