from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

class IntentClassifier:
    def __init__(self, model_name, url, system_prompt, examples):
        self.llm = ChatOllama(model=model_name, base_url=url, temperature=0, num_predict=1)
        self.system_prompt = f"{system_prompt}\n\n{examples}"
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
        self.llm = prompt | self.llm

    def invoke(self, user_query):
        return self.llm.invoke({"input":user_query})

