from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence,RunnableParallel

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

joke_chain = RunnableSequence(prompt1,model,parser)

parallel_chain = RunnableParallel({
    'joke' : joke_chain,
    'explanation' : RunnableSequence(prompt2,model,parser)
})

final_chain = RunnableSequence(joke_chain,parallel_chain)

result = final_chain.invoke({'topic' : 'vadapav'})
print(result['joke'])
print(result['explanation'])

