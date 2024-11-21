from shiny import App, ui, reactive
from shiny.ui import AccordionPanel
from typing import List
from query_descriptor import QueryDescriptor
import data_retriever
from parser import Parser
from htmltools.tags import ul, li, div, strong
from htmltools import TagList, HTML
import json, yaml
from data_retriever import DataRetriever
from intent_classifier import IntentClassifier
from summarizer import Summarizer

with open("messages_prompts.json", "r") as f:
    data = json.load(f)

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

welcome_message = ui.markdown(data["welcome_message"])
retriever = DataRetriever(model_name=config["model_name_keyword_extraction"], url=config["url"], system_prompt=data["retriever_system_prompt"], examples=data["retriever_few_shot_examples"])
classifier = IntentClassifier(model_name=config["model_name_intent"], url=config["url"], system_prompt=data["classifier_system_prompt"], examples=data["classifier_few_shot_examples"])
summarizer = Summarizer(config["embedding_model_name"], config["summarization_model_name"])
parser = Parser(config["database_base_url"])


def make_panel(articles, max_abs_len) -> List[AccordionPanel]:
    """This function builds a list of panels to add to the accordion that will be displayed by the chatbot
    :param articles: list of articles
    :param max_abs_len: max length of the abstract that will be displayed
    :returns: A list of AccordionPanel objects that will form the accordion"""
    panels = []
    for i, article in enumerate(articles):
        # For each article create a bullet list for title, authors, etc.
        ul_tag = ul()
        for key, value in article.items():
            match key:
                case "authors":
                    author_list = ul()
                    for author in value:
                        author_list.append(li(author))
                    value = author_list
                case "abstract":
                    if value:
                        min_len = min(len(value), max_abs_len)
                        value = value[:min_len]
                        if min_len == max_abs_len:
                            value += "..."
                    else:
                        value = "No abstract is available"
                case "journal":
                    if not value:
                        value = "No journal is available"
            ul_tag.append(li(strong(f"{key[0].upper()}{key[1:]}: "), value))
        panel = ui.accordion_panel(strong(article["title"]), ul_tag, value=f"panel-{i+1}")
        panels.append(panel)

    return panels

def create_accordion(articles, max_abs_len):
    return ui.accordion(*make_panel(articles, max_abs_len), id="acc_single", multiple=False, class_="mb-3", open=False)

app_ui = ui.page_fillable(
    ui.layout_sidebar(
    ui.sidebar(ui.input_slider("max_returns", "Maximum number of articles to return",  min=1, max=15, value=5),
                    ui.input_numeric("max_abstract_len", "Maximum character length for abstract", value=300),
                    ui.input_numeric("max_summary_len", "Maximum word length of the summary", value=150), position="left", title="Settings", fill=True, width=350),
    ui.panel_title("Your Pubmed Chatbot Assistant"),
    ui.chat_ui("chat"), fillable=True),
    fillable_mobile=True
)

def server(input, output, session):
    chat = ui.Chat(id="chat", messages=[welcome_message])
    retmax = reactive.Value()
    abstract_len = reactive.Value()
    last_articles = reactive.Value({})
    summary_len = reactive.Value()

    @reactive.effect
    def _():
        # Updates the number of max elements to return based on the input slider
        retmax.set(input.max_returns())

    @reactive.effect
    def _():
        # Updates the value of the maximum abstract length to avoid truncation
        abstract_len.set(input.max_abstract_len())

    @reactive.effect
    def _():
        # Updates the number of max length of the summary
        summary_len.set(input.max_summary_len())

        # Define a callback to run when the user submits a message
    @chat.on_user_submit
    async def _():
        # Get the user's input
        user = chat.user_input()

        # Get the user's intent (retrieval/summary), indicating whether the user wants to retrieve articles or summarise previously returned articles.
        intent = classifier.invoke(user).content

        if "retrieval" in intent:
            # Generate a query descriptor describing the user's query
            desc = QueryDescriptor(user, retriever)
            # Retrieve the paper ids using the eSearch API
            paper_ids = parser.run_search_query(desc, retmax=retmax.get())
            # Retrieve the paper data using the eFetch API
            articles = parser.retrieve_articles_data(paper_ids)

            if len(articles) > 0:
                # We found at least a result that we will display
                accordion = create_accordion(articles, max_abs_len = abstract_len.get())
                message = HTML(TagList(div("Sure! Here are the results I found related to your search query:", class_="mb-3"),
                              accordion,
                              div("Let me know if you'd like more details about any of these articles.")))

                # set the history of extracted articles to the articles that were just retrieved.
                tmp_articles = {}
                for article in articles:
                    tmp_articles[article["title"]] = article

                last_articles.set(tmp_articles)

            else:
                # we did not find anything
                message = "I'm sorry, I was not able to find any article with the search criteria specified."

        elif "summary" in intent:
            if len(last_articles.get().keys()) > 0:
                # Get the most similar article to the user's query
                article = summarizer.find_article(last_articles.get(), user)
                summary = summarizer.summarize_article(article, summary_len.get())
                message = f"This is the summary of the article \'{article['title']}\':\n\n{summary}\n\nIs there anything else I can assist you with?"
            else:
                message = "I'm sorry, but you need to ask me to retrieve some articles before summarizing any of those. Please ask me to retrieve an article."

        else:
            message = "I'm sorry, but I did not understand. I can only retrieve or summarize a document. What do you want me to do?"

        # Append a response to the chat
        await chat.append_message(message)


app = App(app_ui, server)