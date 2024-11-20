from shiny import App, ui
from query_descriptor import QueryDescriptor
import data_retriever
from core import run_search_query, retrieve_articles_data
from htmltools.tags import ul, li, div, strong
from htmltools import TagList, HTML
import json, yaml
from data_retriever import DataRetriever

with open("messages_prompts.json", "r") as f:
    data = json.load(f)

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

app_ui = ui.page_fillable(
    ui.panel_title("Your Pubmed Chatbot Assistant"),
    ui.chat_ui("chat")
)

welcome_message = ui.markdown(data["welcome_message"])
retriever = DataRetriever(model_name=config["model_name"], url=config["url"], system_prompt=data["system_prompt"], examples=data["few_shot_examples"])

def make_panel(articles):
    panels = []
    for i, article in enumerate(articles):
        ul_tag = ul()
        for key, value in article.items():
            if key == "authors":
                author_list = ul()
                for author in value:
                    author_list.append(li(author))
                ul_tag.append(li(strong(f"{key[0].upper()}{key[1:]}: "), author_list))
            else:
                ul_tag.append(li(strong(f"{key[0].upper()}{key[1:]}: "), value))
        panel = ui.accordion_panel(strong(article["title"]), ul_tag, value=f"panel-{i+1}")
        panels.append(panel)

    return panels

def create_accordion(articles):
    return ui.accordion(*make_panel(articles), id="acc_single", multiple=False, class_="mb-3", open=False)

def server(input, output, session):
    chat = ui.Chat(id="chat", messages=[welcome_message])

    # Define a callback to run when the user submits a message
    @chat.on_user_submit
    async def _():
        # Get the user's input
        user = chat.user_input()
        desc = QueryDescriptor(user, retriever)
        paper_ids = run_search_query(desc)
        articles = retrieve_articles_data(paper_ids)
        print(articles)
        if len(articles) > 0:
            # We found at least a result that we will display
            accordion = create_accordion(articles)
            message = HTML(TagList(div("Sure! Here are the results I found related to your search query", class_="mb-3"),
                          accordion,
                          div("Let me know if you'd like more details about any of these articles")))

        else:
            # we did not find anything
            message = "I'm sorry, I was not able to find any article with the search criteria specified."

        # Append a response to the chat
        await chat.append_message(message)


app = App(app_ui, server)