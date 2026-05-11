from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

parser = JsonOutputParser()

template = PromptTemplate(
    template = "Give me 5 facts about {topic} \n {formate_instructions}",
    input_variables=["topic"],
    partial_variables={"formate_instructions": parser.get_format_instructions()}
)

chain = template | model | parser

result = chain.invoke({"topic": "black hole"})
print(result)