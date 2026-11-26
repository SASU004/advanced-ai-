# same as rag.py but the chunks go into a persistent chroma db instead of the json file

import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from rag import create_chunks   #we only need the chunking part from rag.py

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


EMBED_MODEL=os.getenv("EMBED_MODEL")


def get_embedding(text):

    response=client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding


#persistent client---it writes the db to disk so the vectors are not lost when we close the program 
chroma=chromadb.PersistentClient(path="./chromadbStorage")

#cosine instead of the default l2---cosine only looks at the angle between the vectors 
#which works better for text embeddings
zorvex_collection=chroma.get_or_create_collection(
    name="zorvex_technology",
    configuration={
        "hnsw": {
            "space": "cosine",
        }
    }
)


#take all the chunks from the knowledge base and push them inside chroma
def build():
    chunks=create_chunks()   #same chunking we already had in rag.py

    ids=[c["id"] for c in chunks]            #every chunk already has a unique id like leave_policy.txt#3
    documents=[c["text"] for c in chunks]    #the actual text of the chunk 

    embeddings=[]
    for s in documents:
        embedding=get_embedding(s)   #get the semantic value of the chunk 
        embeddings.append(embedding)

    zorvex_collection.upsert( #It will update if an Id is existing, otherwise it will insert a new record
        ids=ids,
        documents=documents,
        embeddings=embeddings,
    )
    return len(chunks)


# search top k chunk for a user querry
def search(query, k=3):
    total=zorvex_collection.count()   #how many chunks we have in the db 
    if total==0:                      #if the db is empty we cant query it 
        return []

    query_embedding=get_embedding(query)

    results=zorvex_collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k,total),   #chroma throws an error if we ask for more results than we have 
    )

    found=[]
    for i,text in enumerate(results["documents"][0]):
        source,_,num=results["ids"][0][i].partition("#")   #id is like leave_policy.txt#3 so we split it back 
        found.append(
            {
                "score": 1-results["distances"][0][i],   #chroma gives distance (0=exact match) so we convert it to a score 
                "source": source,                        #which file 
                "chunk_id": int(num),
                "text": text,                            #what was the text 
                "size": len(text),
            }
        )
    return found


if __name__=="__main__":
    print(f"stored {build()} chunks")