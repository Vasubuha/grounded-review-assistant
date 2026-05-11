from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="google/gemma-4-31B-it",
    task="text-generation",
    temperature=0
)

model = ChatHuggingFace(llm=llm)

temp1 = PromptTemplate(
    template = "write a detailed report on {topic}",
    input_variables = ["topic"]
)

temp2 = PromptTemplate(
    template = "write a 5 line summary on the following text: {text}",
    input_variables = ["text"]
)

prompt1 = temp1.invoke({"topic": "the current state of AI research"})
result = model.invoke(prompt1)

prompt2 = temp2.invoke({"text": result.content})
result1 = model.invoke(prompt2)

print(result1.content)


