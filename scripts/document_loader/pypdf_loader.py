from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("dl-curriculum.pdf")
docs = loader.load()

print(type(docs))
print(len(docs))
print(docs[0].page_content)
print(docs[1].metadata)