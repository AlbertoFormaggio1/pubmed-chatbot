from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

class Keyword(BaseModel):
    """One or more words representing a relevant concept that can be used as keyword for a search in a scientific paper database"""
    keyword: str = Field(description="One or more words representing a keyword")

class Journal(BaseModel):
    """One or more words indicating the name of the journal in which the requested paper was published."""
    journal: str = Field(description="The name of the journal asked by the user")

class DataFields(BaseModel):
    """A wrapper to contain multiple data fields to be used for querying a scientific paper database."""
    keywords: List[str] = Field(description="One or more words representing a keyword")
    journal: Optional[str] = Field(description="The name of the journal asked by the user")

class DataRetriever:
    def __init__(self, model_name, url=None, system_prompt="", examples=""):
        self.llm = ChatOllama(model=model_name, base_url=url, temperature=0)
        self.llm = self.llm.with_structured_output(DataFields)
        examples = "\n\n".join(examples)
        self.system_prompt = f"{system_prompt}\n\n{examples}"
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
        self.few_shot_structured_llm = prompt | self.llm

    def invoke(self, user_query):
        return self.few_shot_structured_llm.invoke({"input":user_query})