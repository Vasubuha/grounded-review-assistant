from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence, RunnableParallel

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

prompt1 = PromptTemplate(
    template= "Generate tweet about {topic}",
    input_variables= ["topic"]
)

prompt2 = PromptTemplate(
    template= "Generate a LinkedIn post about {topic}",
    input_variables= ["topic"]
)

parser = StrOutputParser()
parallel_chian = RunnableParallel({
    'tweet' : RunnableSequence(prompt1,model,parser),
    'linkedin' : RunnableSequence(prompt2,model,parser)
})

result = parallel_chian.invoke({'topic' : 'AI'})    
print(result['tweet'])
print(result['linkedin'])
