from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


EMBED_MODEL=os.getenv("EMBED_MODEL")
KB_FOLDER=os.getenv("KB_FOLDER")


def get_embedding(text):

    response=client.embedding.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding


def compare_embedding(a,b):
    dot_product=numpy.dot(a,b)
    len_a=numpy.linalg.norm(a)          #length of the embedding 
    len_b=numpy.linalg.norm(b)
    return dot_product/(len_a,len_b)


def load_documents(folder=KB_FOLDER):   
    documents=[]

    for filename in sorted(os.listdir(folder)):                     #lisitng all files of  kb_folder in sorted order which are only txt files
        if not filename.endswith(".txt"):
            continue

        path=os.path.join(folder, filename)  #we derive the path to all the docs individually by using the doler paths ie kowledge_base from the pc appened with the doc name 
        with open(path,"r",encoding="UTF-8") as f: # we open the docs by using the derived paths using only read mode "r" and encoding utf 8 (univesal binary code for each character irrespective fo windows mac linux) # opening it as variable f 
            documents.append(
                {
                    "source": filename,
                    "text": f.read()
                }
            )  
    return documents


def add_embeddings(documents):
    for document in documents:
        vector = get_embedding(document["text"])   #get the semantic value of the documents 
        document["vector"]=vector # add that embedding value to the document itslef 


# search top k documents for a user querry
def search(query, documents, k=3):
    query_embedding= get_embedding(query)

    results=[] # empty list to story the top k docs related to the query
    for document in documents:
        score= compare_embedding(query_embedding, document["vector"])
        results.append(
            {
                "score": float(score),
                "source": document["source"],  #which file 
                "text": document["text"],      #what was the text
                "size": len(document["text"])  #length of the doc
            }
        )

    results.sort(key=lambda record: record["score"],reverse=True)
    return results[:k]