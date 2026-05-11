from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

class Person(BaseModel):
    name : str = Field(description="the person's name")
    age : int = Field(description="the person's age")   
    city : str = Field(description="the city the person lives in")

parser = PydanticOutputParser(pydantic_object=Person)

template = PromptTemplate(
    template = "Generate the name, age and city of a fictional {place} \n {format_instructions}",
    input_variables = ["place"],
    partial_variables = {"format_instructions": parser.get_format_instructions()}
)

chain = template | model | parser
result = chain.invoke({"place": "india"})
print(result)   