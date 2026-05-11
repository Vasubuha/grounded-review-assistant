from typing import Annotated, Optional, TypedDict

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Optional, Literal


load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    task="text-generation",
    temperature=0
)

model = ChatHuggingFace(llm=llm)

class Review(TypedDict):
    key_themes : Annotated[list[str],"Write  down all the key themes mentioned in the review"]
    summary : Annotated[str,"Write a concise summary of the review"]
    sentiment : Annotated[Literal["pos","neg"],"Classify the sentiment of the review as positive or negative"]
    pros : Annotated[Optional[list[str]],"Write down the pros mentioned in the review if any, else return null"]
    cons : Annotated[Optional[list[str]],"Write down the cons mentioned in the review if any, else return null"]
    name : Annotated[
    Optional[str],
    "Return the exact reviewer name ONLY if explicitly mentioned. Otherwise return null (not the string 'null')."
]

Structured_model = model.with_structured_output(Review)
result = Structured_model.invoke(
"""
Follow these rules strictly:
- Do NOT hallucinate
- If a field is not explicitly mentioned, return null
- Do NOT invent names


I recently upgraded to the Samsung Galaxy S24 Ultra, and I must say, it's an absolute powerhouse! The Snapdragon 8 Gen 3
processor makes everything lightning fast-whether I'm gaming, multitasking, or editing photos. The 5000mAh battery easily
lasts a full day even with heavy use, and the 45W fast charging is a lifesaver.

The S-Pen integration is a great touch for note-taking and quick sketches, though I don't use it often. What really blew me
away is the 200MP camera-the night mode is stunning, capturing crisp, vibrant images even in low light. Zooming up to 100x
actually works well for distant objects, but anything beyond 30x loses quality.

However, the weight and size make it a bit uncomfortable for one-handed use. Also, Samsung's One UI still comes with
bloatware-why do I need five different Samsung apps for things Google already provides? The $1,300 price tag is also a hard
pill to swallow.

Pros:
Insanely powerful processor (great for gaming and productivity)
Stunning 200MP camera with incredible zoom capabilities
Long battery life with fast charging
S-Pen support is unique and useful

Cons :
Bulky and heavy-not great for one-handed use
Bloatware still exists in One UI
Expensive compared to competitors

reviewer name: John Doe
""")

print(result)