from query_descriptor import QueryDescriptor
import requests
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from typing import List
import re

class Parser:
    def __init__(self, base_url):
        """
        Initialize the Parser with a base URL for PubMed queries.

        :param base_url (str): The base URL for PubMed API endpoints
        """
        self.base_url = base_url

    def build_term_field(self, desc):
        """
        Construct a search query string from the descriptor's keywords, authors, and journal.

        :param desc (QueryDescriptor): The query descriptor containing search parameters
        :return: A constructed search term string for PubMed query
        """
        query_parts = []
        for kw in desc.keywords:
            query_parts.append(f"{kw}")

        if desc.authors:
            # Authors are likely to be independent from one another
            author_parts = []
            for author in desc.authors:
                author_parts.append(f"{author}[Author]")
            query_parts.append(" OR ".join(author_parts))

        if desc.journal:
            safe_journal = re.sub('[^a-zA-Z\s]', '', desc.journal)
            query_parts.append(f"{safe_journal}[Journal]")

        return " AND ".join(query_parts)

    def run_search_query(self, desc, retmax=5):
        """
        Execute a search query on PubMed based on the given descriptor.

        :param desc (QueryDescriptor): The query descriptor containing search parameters
        :param retmax (int, optional): Maximum number of results to retrieve. Defaults to 5.
        :return: A list of PubMed article IDs matching the search criteria
        """
        search_url = f"{self.base_url}esearch.fcgi"
        term = self.build_term_field(desc)
        params = {"db": "pubmed", "term": term, "retmode": "json", "retmax": retmax}

        # The user must provide 2 dates: one will be the start date, the other will be the end date.
        if len(desc.dates) == 2:
            params["mindate"] = desc.dates[0]
            params["maxdate"] = desc.dates[1]

        response = self.query(search_url, params)

        data = response.json()
        return data["esearchresult"].get("idlist", [])

    def retrieve_articles_data(self, ids):
        """
        Retrieve and parse full article data for given PubMed article IDs.

        :param ids (List[str]): List of PubMed article IDs
        :return: A list of parsed article dictionaries
        """
        xml_root = self.run_fetch_query(ids)
        parsed_articles = self.parse_xml_tree(xml_root)
        return parsed_articles

    def run_fetch_query(self, ids):
        """
        Fetch XML data for specific PubMed article IDs.

        :param ids (List[str]): List of PubMed article IDs
        :return: XML root element containing article data
        """
        search_url = f"{self.base_url}efetch.fcgi"
        params = {"db": "pubmed", "retmode": "xml", "id":",".join(ids)}

        response = self.query(search_url, params)

        root = ET.fromstring(response.text)
        return root

    def query(self, url, params):
        """
        Send a GET request to the specified URL with given parameters.

        :param url (str): The full URL to query
        :param params (dict): Query parameters
        :return: Response from the HTTP request
        :raises Exception: If the request fails with a non-200 status code
        """
        full_url = f"{url}?{urlencode(params, safe='[]')}"
        response = requests.get(full_url)
        if response.status_code != 200:
            raise Exception(f"Search failed with status code: {response.status_code}")

        return response

    def parse_xml_tree(self, root: ET.Element) -> List:
        """
        Parse the XML tree of PubMed articles and extract relevant information.

        :param root (ET.Element): XML root element containing article data
        :return: A list of dictionaries, each representing an article with extracted information
        """
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

