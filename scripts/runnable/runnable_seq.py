from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

prompt1 = PromptTemplate(
    template= "write a joke about {topic}",
    input_variables=['topic']
)

parser = StrOutputParser()

prompt2 = PromptTemplate(
    template= "Explain the following joke -- {text}",
    input_variables=['text']
)

chain = RunnableSequence(prompt1,model,parser,prompt2,model,parser)
print(chain.invoke({'topic' : 'vadapav'}))