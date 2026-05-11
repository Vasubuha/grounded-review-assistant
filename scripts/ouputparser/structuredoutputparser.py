from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema,StructuredOutputParser

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

schema = [
    ResponseSchema(name="fact1", description="the first fact about the topic"),
    ResponseSchema(name="fact2", description="the second fact about the topic"),
    ResponseSchema(name="fact3", description="the third fact about the topic"),
    ResponseSchema(name="fact4", description="the fourth fact about the topic"),
    ResponseSchema(name="fact5", description="the fifth fact about the topic")
]

parser = StructuredOutputParser.from_response_schemas(schema)

template = PromptTemplate(
    template  = "Give me 5 facts about {topic} \n {formate_instructions}",
    input_variables=["topic"],
    partial_variables={"formate_instructions": parser.get_format_instructions()}
)

chain = template | model | parser

result = chain.invoke({"topic": "black hole"})
print(result)