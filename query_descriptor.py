import spacy
from typing import List
from yake import KeywordExtractor
import re

# load a pipeline with small model for processing English text
nlp = spacy.load('en_core_web_sm')

class QueryDescriptor:
    """
    A class to extract and process key information from a user input query.

    This class analyzes user input to extract relevant metadata such as dates,
    authors, keywords, and associated journal using various extraction methods.
    """
    def __init__(self, user_input, data_retriever):
        """Initialize the QueryDescriptor with user input and a data retrieval service.

        Args:
        :param user_input (str): The query text to be processed
        :param data_retriever: A service capable of extracting keywords and journal info"""
        self.user_input = user_input
        self.data_retriever = data_retriever
        self.dates = self.__get_dates(user_input)
        self.authors = self.__get_authors(user_input)
        self.keywords, self.journal = self.__get_keywords_journal_llm(user_input)

    def __get_keywords_journal_llm(self, user_input: str):
        """
        Extract keywords and journal using a language model-based approach.

        :param user_input (str): The query text to process

        :return: Tuple containing extracted keywords and associated journal"""
        res = self.data_retriever.invoke(user_input)
        return res.keywords, res.journal

    def __get_keywords_yake(self, user_input):
        extractor = KeywordExtractor(lan="en", n=2, top=5)
        # Extract keywords with a maximum of 2 words per phrase
        keywords = extractor.extract_keywords(user_input)
        keywords = [keyword for keyword, score in keywords if score < 0.1]
        return keywords

    def __get_dates(self, user_input: str) -> List[str]:
        """
        Extract date references from the user input using spaCy NER.

        :param user_input (str): The query text to extract dates from

        :return:    List of extracted dates (numeric strings)
        """
        doc = nlp(user_input)
        dates = [re.sub("[^0-9]","", ent.text) for ent in doc.ents if ent.label_ == 'DATE']
        return dates

    def __get_authors(self, user_input: str) -> List[str]:
        """
        Extract person names from the user input using spaCy NER.
        :param user_input (str): The query text to extract author names from

        :return: List of extracted person names
        """
        doc = nlp(user_input)
        authors = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        return authors