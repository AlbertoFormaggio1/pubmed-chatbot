import spacy
from typing import List
from yake import KeywordExtractor
import re

# load a pipeline with small model for processing English text
nlp = spacy.load('en_core_web_sm')

class QueryDescriptor:
    def __init__(self, user_input, data_retriever):
        self.user_input = user_input
        self.data_retriever = data_retriever
        self.dates = self.__get_dates(user_input)
        self.authors = self.__get_authors(user_input)
        self.keywords, self.journals = self.__get_keywords_journal_llm(user_input)

    def __get_keywords_journal_llm(self, user_input: str):
        res = self.data_retriever.invoke(user_input)
        return res.keywords, res.journal

    def __get_keywords_yake(self, user_input):
        extractor = KeywordExtractor(lan="en", n=2, top=5)
        # Extract keywords with a maximum of 2 words per phrase
        keywords = extractor.extract_keywords(user_input)
        keywords = [keyword for keyword, score in keywords if score < 0.1]
        return keywords

    def __get_dates(self, user_input: str) -> List[str]:
        doc = nlp(user_input)
        dates = [re.sub("[^0-9]","", ent.text) for ent in doc.ents if ent.label_ == 'DATE']
        return dates

    def __get_authors(self, user_input: str) -> List[str]:
        doc = nlp(user_input)
        authors = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        return authors