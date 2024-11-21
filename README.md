# Chatbot interface for Pubmed API

## Requirements
To start the program locally, you need to:
1) Install all the requirements with poetry.
   ```poetry install```
2) Install spacy for running NER.
   ```python -m spacy download en```

## How to run the experiment
Before running the program, you need to configure the config.yaml file.

This project is using Ollama, therefore if you have open endpoint internally, you must modify the **ollama_url** field, pointing to the address where you are storing the LLMs locally.

Additionally, you must also modify the model names to existing model names you have install or, alternatively, install the models indicated in the config.yaml file

Using the terminal go in the project directory and then run
```shiny run```
This will start a local server, you can click on the link that will appear on the terminal to access the application.


## Example queries
1) "Can you retrieve papers related to COVID-19 vaccination?"
   Extract some details from one of the titles and then you can ask "Can you summarise the paper concerning <insert details from title>?"

2) "Can you give me information about papers on polyp segmentation with swin transformer written by Vats Anuja on the journal biomedical engineering letters?"
   "Can you give me more info on the paper related to polyp segmentation?"


# Implementation choices
- For keyword extraction I tried RAKE, YAKE, KeyBERT but none of them was able to extract relevant keywords (e.g. "papers related" was detected as a keyword). As a consequence, I opted for an LLM with structured output. This was because it is important that keywords are correct otherwise no output would be returned by the API with too much noise.
- To show diversity in the approach, dates and authors were detected using spacy NER. As an alternative, the fields "Author" and "Dates" could have been included in the structure of the structured output.
- For the intent classification, I opted for Phi, a small LLM (just 2B parameters), since the time for this operations should be rather short and can be handled by a simple LLM.
- 
