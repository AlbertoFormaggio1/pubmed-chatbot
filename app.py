from shiny import App, ui, reactive
from query_descriptor import QueryDescriptor
import data_retriever
from parser import run_search_query, retrieve_articles_data
from htmltools.tags import ul, li, div, strong
from htmltools import TagList, HTML
import json, yaml
from data_retriever import DataRetriever
from transformers import pipeline

with open("messages_prompts.json", "r") as f:
    data = json.load(f)

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)



welcome_message = ui.markdown(data["welcome_message"])
retriever = DataRetriever(model_name=config["model_name"], url=config["url"], system_prompt=data["system_prompt"], examples=data["few_shot_examples"])
summarizer = pipeline("summarization", model="google-t5/t5-small")

def make_panel(articles, max_abs_len):
    panels = []
    for i, article in enumerate(articles):
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
                    ui.input_numeric("max_abstract_len", "Maximum character length for abstract", value=300), position="left", title="Settings", fill=True, width=350),
    ui.panel_title("Your Pubmed Chatbot Assistant"),
    ui.chat_ui("chat"), fillable=True),
    fillable_mobile=True
)

def server(input, output, session):
    chat = ui.Chat(id="chat", messages=[welcome_message])
    retmax = reactive.Value()
    abstract_len = reactive.Value()

    @reactive.effect
    def _():
        # Updates the number of max elements to return based on the input slider
        retmax.set(input.max_returns())

    @reactive.effect
    def _():
        # Updates the value of the maximum abstract length to avoid truncation
        abstract_len.set(input.max_abstract_len())

        # Define a callback to run when the user submits a message
    @chat.on_user_submit
    async def _():
        # Get the user's input
        user = chat.user_input()
        desc = QueryDescriptor(user, retriever)
        paper_ids = run_search_query(desc, retmax=retmax.get())
        articles = retrieve_articles_data(paper_ids)

        if len(articles) > 0:
            # We found at least a result that we will display
            accordion = create_accordion(articles, max_abs_len = abstract_len.get())
            message = HTML(TagList(div("Sure! Here are the results I found related to your search query:", class_="mb-3"),
                          accordion,
                          div("Let me know if you'd like more details about any of these articles.")))

        else:
            # we did not find anything
            message = "I'm sorry, I was not able to find any article with the search criteria specified."

        # Append a response to the chat
        await chat.append_message(message)


app = App(app_ui, server)