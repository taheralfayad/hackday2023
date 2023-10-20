import os

import openai
import pinecone
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from dotenv import load_dotenv
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.text_splitter import CharacterTextSplitter

from .utils import import_content_from_canvas, upload_files_as_vectors

load_dotenv()

pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"), 
    environment=os.getenv("PINECONE_ENVIRON"), 
)

OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

@shared_task
def send_message_back(user_message, course_id):
    course_id = str(course_id)
    embeddings = OpenAIEmbeddings(openai_api_key = OPENAI_KEY)
    if course_id not in pinecone.list_indexes():
        pinecone.create_index(
            name=course_id,
            metric='cosine',
            dimension=1536  
        )
        # import_content_from_canvas(course_id)
        index = pinecone.Index(course_id)
        docs = upload_files_as_vectors(index)
        vectorstore = Pinecone.from_documents(docs, embeddings, index_name=course_id)
    else:
        vectorstore = Pinecone.from_existing_index(course_id, embeddings)

    llm = OpenAI(temperature=0)

    document_content_description = "Excerpts from textbooks and powerpoints."

    metadata_field_info = [
        AttributeInfo(
            name="source",
            description="The pdf source of the excerpt",
            type="string or list[string]",
        ),
        AttributeInfo(
            name="page",
            description="The page where this is can be found",
            type="string or list[string]",
        ),
    ]

    retriever = SelfQueryRetriever.from_llm(
        llm, vectorstore, document_content_description, metadata_field_info, verbose=True
    )

    results = retriever.get_relevant_documents(user_message)

    template = """
            Answer the question using only the context provided. Do not try to fact check the provided context
            and do not use any other information outside of the context provided.
            If you are unable to answer the question, please just say that you don't know the answer."""

    if len(results) == 0:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "chatbot",
            {
                'type': 'chat_message',
                'message': 'No information was found about this, please try again.' 
            }
        )
        return


    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": template
            },
            {
                "role": "system",
                "content": f'Here is the context from which you can answer {results[0].page_content}'
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    source = results[0].metadata['source'].replace("./downloaded_files/", "", 1)

    response_text = response['choices'][0]['message']['content'] + f" (Source: {source}"

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "chatbot",
        {
            'type': 'chat_message',
            'message': response_text
        }
    )
