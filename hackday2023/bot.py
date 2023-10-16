import os
from langchain.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import CTransformers
from langchain.vectorstores.pgvector import PGVector
from langchain.vectorstores import FAISS
from langchain import PromptTemplate
from langchain.chains import RetrievalQA

class Bot:
    def __init__(self):
        # Load in all docs from the /media/ directory
        loader = DirectoryLoader("./media/", glob="**/*.txt", loader_cls=UnstructuredMarkdownLoader)
        documents = loader.load()
        for document in documents:
            document.metadata = { "source": "https://ucfcdl.github.io/" + document.metadata["source"][:-2] + "html" }

        splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=50)
        texts = splitter.split_documents(documents)

        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                        model_kwargs={'device': 'cpu'})
        
        if (os.environ.get("DEV", True) == True):
            # Run a database off of disk in dev
            self.db = FAISS.from_documents(texts, self.embeddings)
        else:
            # Init database connection
            self.CONNECTION_STRING = PGVector.connection_string_from_db_params(
                driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
                host=os.environ.get("PGVECTOR_HOST", "postgres"),
                port=int(os.environ.get("PGVECTOR_PORT", "5432")),
                database=os.environ.get("PGVECTOR_DATABASE", ""),
                user=os.environ.get("PGVECTOR_USER", "user"),
                password=os.environ.get("PGVECTOR_PASSWORD", "password")
            )

            self.db = PGVector.from_documents(
                embedding=self.embeddings,
                documents=texts,
                collection_name="ucf_chatbot_docs",
                connection_string=self.CONNECTION_STRING
            )

        # Template the model will use when answering questions
        template = """\
                  Answer the question using only the context provided. Do not try to fact check the provided context
                  and do not use any other information outside of the context provided.
                  If you are unable to answer the question, please just say that you don't know the answer.
        Context: {context}
        Question: {question}
        Response:
        """

        self.llm = CTransformers(model="./llama-2-7b-chat.ggmlv3.q8_0.bin",
                            model_type="llama",
                            config={'max_new_tokens': 1024, 'temperature': 0.1, 'context_length': 2048})

        retriever = self.db.as_retriever()
        self.prompt = PromptTemplate(template=template, input_variables=['context', 'question'])

        self.qa_llm = RetrievalQA.from_chain_type(llm=self.llm,
                                            chain_type="stuff",
                                            retriever=retriever,
                                            return_source_documents=True,
                                            chain_type_kwargs={'prompt': self.prompt})
        
    # Return the response to the question
    def q_a(self, query: str):
        """
        Asks the question to the Llama model
        """
        result = self.qa_llm({"query": query})
        response = result["result"]
        if len(result["source_documents"]) != 0: 
            source = result["source_documents"][0].metadata["source"]
            response += "\nHere is a link to a relevant page in the handbook: " + source
        
        return response
    
    # Embeds additional documents into the database
    def embed(self, file: str):
        """
        Takes in a file as a string, splits and embeds it, then adds it to the vector database.
        """
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = splitter.create_documents([file])
        self.db.add_documents(texts)

        self.qa_llm = RetrievalQA.from_chain_type(llm=self.llm,
                                            chain_type="stuff",    
                                            retriever=self.db.as_retriever(),
                                            return_source_documents=True,
                                            chain_type_kwargs={'prompt': self.prompt})
