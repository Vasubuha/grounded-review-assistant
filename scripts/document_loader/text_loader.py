from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

prompt = PromptTemplate(
    template = "write a summary for the following poem - \n {poem}",
    inpit_variables=["poem"]
)

parser = StrOutputParser()

loader = TextLoader("cricket.txt",encoding="utf-8")
docs = loader.load()
print(type(docs))
print(len(docs))
print(docs[0].page_content)
print(docs[0].metadata)

chain = prompt | model | parser

print(chain.invoke({"poem": docs[0].page_content}))

