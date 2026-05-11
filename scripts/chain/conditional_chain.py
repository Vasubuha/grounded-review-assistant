from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.runnables import RunnableLambda,Runnable,RunnableBranch
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

parser = StrOutputParser()

class Feedback(BaseModel):
    feedback: Literal["positive", "negative"] = Field(description="GIve the sentiment of the feedback")


pydantic_parser = PydanticOutputParser(pydantic_object=Feedback)

prompt1 = PromptTemplate(
    template='Classify the sentiment of the following feedback text into postive or negative \n {feedback} \n {format_instruction}',
    input_variables=['feedback'],
    partial_variables={'format_instruction':pydantic_parser.get_format_instructions()}
)

classifier_chain = prompt1 | model | pydantic_parser

prompt2 = PromptTemplate(
    template='Write an appropriate response to this positive feedback \n {feedback}',
    input_variables=['feedback']
)

prompt3 = PromptTemplate(
    template='Write an appropriate response to this negative feedback \n {feedback}',
    input_variables=['feedback']
)

branch_chain = RunnableBranch(
    (lambda x: x.feedback == 'positive', prompt2 | model | parser),
    (lambda x: x.feedback == 'negative', prompt3 | model | parser),
    RunnableLambda(lambda x: "could not find sentiment")
)

chain = classifier_chain | branch_chain

print(chain.invoke({'feedback': 'This is a beautiful phone'}))

chain.get_graph().print_ascii()
