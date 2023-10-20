import requests
import os

from dotenv import load_dotenv

import pinecone
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

load_dotenv()

CANVAS_API_KEY = os.environ.get('CANVAS_API_KEY')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

def import_content_from_canvas(course_id):
    folders = get_folders(course_id)
    folder_id = find_folder_by_name(folders)

    folder = get_files_in_folder(folder_id)

    download_lectures(folder)

    return

def get_folders(course_id):
    url = f'https://canvas.dev.cdl.ucf.edu/api/v1/courses/{course_id}/folders'
    api_key = f'Bearer {CANVAS_API_KEY}'

    headers = {
        'Authorization': api_key
    }

    response = requests.get(url, headers=headers)

    return response.json()

def get_files_in_folder(folder_id):
    url = f'https://canvas.dev.cdl.ucf.edu/api/v1/folders/{folder_id}/files'
    api_key = f'Bearer {CANVAS_API_KEY}'

    headers = {
        'Authorization': api_key
    }

    response = requests.get(url, headers=headers)

    return response.json()

def find_folder_by_name(folders):
    folder_id = None
    for folder in folders:
        if folder['name'] == 'lectures':
            folder_id = folder['id']
            break
    
    return folder_id

def download_lectures(data):
    download_dir = 'downloaded_files'
    os.makedirs(download_dir, exist_ok=True)

    api_key = f'Bearer {CANVAS_API_KEY}'

    headers = {
        'Authorization': api_key
    }

    for item in data:
        url = item['url']
        filename = item['filename']
        filepath = os.path.join(download_dir, filename)

        # Download and save the file
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded: {filename}")

    print("All files downloaded!")


def upload_files_as_vectors(index):
    documents = []
    for dirpath, dirnames, filenames in os.walk("./downloaded_files"):
        for filename in filenames:
            absolute_path = os.path.join(dirpath, filename)
            docs = load_file(absolute_path)
            for doc in docs:
                documents.append(doc)
    return documents

def load_file(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(pages)
    return docs
