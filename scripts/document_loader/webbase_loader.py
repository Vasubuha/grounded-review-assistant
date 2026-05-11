from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

prompt = PromptTemplate(
    template = "Answer the following question - \n {question} from the following text - \n {text}",
    input_variables=["question", "text"]
)

parser = StrOutputParser()

url = "https://www.geeksforgeeks.org/machine-learning/ml-linear-regression/"
loader = WebBaseLoader(url)

docs = loader.load()

chain = prompt | model | parser
print(chain.invoke({"question": "What is the defination of  linear regression?", "text": docs[0].page_content}))

