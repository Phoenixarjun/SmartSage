import os
import tempfile
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, SeleniumURLLoader
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def file_processing(files):
    all_docs = []

    for file in files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.read())
            path = tmp.name

        try:
            if file.name.endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif file.name.endswith(".docx"):
                loader = Docx2txtLoader(path)
            elif file.name.endswith(".txt"):
                loader = TextLoader(path)
            else:
                raise ValueError(f"Unsupported file: {file.name}")

            docs = loader.load()
            all_docs.extend(docs)
        finally:
            os.unlink(path)

    return all_docs

def load_url(url):
    loader = SeleniumURLLoader(urls=[url])
    docs = loader.load()
    docs = [doc for doc in docs if doc.page_content.strip()]
    if not docs:
        raise ValueError("URL returned no usable content.")
    return docs

def llm_pipeline(files, url, api_key):
    documents = []
    if files:
        documents += file_processing(files)
    if url:
        documents += load_url(url)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", google_api_key=api_key
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def ask_llm(query, vectorstore, api_key):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    context_docs = retriever.get_relevant_documents(query)
    context = "\n\n".join([doc.page_content for doc in context_docs])

    prompt = PromptTemplate.from_template("""
    You are a helpful assistant. Use the following context to answer the question:

    Context:
    {context}

    Question: {question}

    Answer:
    """)

    llm = GoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=api_key, temperature=0.5)
    chain = LLMChain(llm=llm, prompt=prompt)

    return chain.run(question=query, context=context)
