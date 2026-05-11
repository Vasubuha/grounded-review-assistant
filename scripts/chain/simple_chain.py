from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

parser = StrOutputParser()

template = PromptTemplate(
    template = "Give me 5 facts about {topic}",
    input_variables=["topic"]
)

chain = template | model | parser

result = chain.invoke({"topic": "cricket"})
print(result)

chain.get_graph().print_ascii()