# copied from doc_search.py

from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy
import json 

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


EMBED_MODEL=os.getenv("EMBED_MODEL")
KB_FOLDER=os.getenv("KB_FOLDER")
VECTOR_STORE_FILE=os.getenv("VECTOR_STORE_FILE")


def get_embedding(text):

    response=client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding


def compare_embedding(a,b):
    dot_product=numpy.dot(a,b)
    len_a=numpy.linalg.norm(a)          #length of the embedding 
    len_b=numpy.linalg.norm(b)
    return dot_product/(len_a*len_b)


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

#add embedding in chunks 
def add_embeddings(chunks):
    for chunk in chunks:
        vector = get_embedding(chunk["text"])   #get the semantic value of the documents 
        chunk["vector"]=vector # add that embedding value to the document itslef 
    return chunks

# search top k chunk for a user querry
def search(query,chunks, k=3):
    query_embedding= get_embedding(query)

    results=[] # empty list to story the top k docs related to the query
    for chunk in chunks:
        score= compare_embedding(query_embedding, chunk["vector"])
        results.append(
            {
                "score": float(score),
                "source": chunk["source"],  #which file 
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],      #what was the text
                "size": len(chunk["text"])  #length of the doc
            }
        )

    results.sort(key=lambda record: record["score"],reverse=True)
    return results[:k]


#takes one doc and create multiple chunk 
def chunks_in_document(document):
    chunks=[]
    chunk_id=0
    for part in document["text"].split("\n\n"):  # for characters in document text split it using the double endl
        part=part.strip() #remove extra spaces
        if part:
            chunks.append({
                "source":document["source"],
                "text":part,
                "chunk_id":chunk_id,
            })
            chunk_id+=1
    return chunks
         

def create_chunks():
    documents=load_documents()  # load the docs 
    chunks=[] #empty list for chunk adding after creation 

    for document in documents:   # iterate the docs 
        chunks.extend(chunks_in_document(document))    #generate chunks from each doc then add it to the empty list 
    return chunks

def test(user_query,chunks, k=3):
    print(f"\nUser Querry: {user_query}\n")
    results= search (user_query,chunks,k)

    for r in results:
        print(f"{r["score"]:.2f} - {r["source"]} - {r["size"]} characters")   #:.2f is for 2 decimal places formatting 
        print (f"{r['text']}\n")

def save_vector_store(chunks):
    with open(VECTOR_STORE_FILE,"w",encoding="utf-8") as f:
        json.dump(chunks,f,indent=4)   # indent 4 is just beautify

def load_vector_store():
    with open(VECTOR_STORE_FILE,"r",encoding="utf-8") as f:
        return json.load(f) #returns the chunks  

chunks = []

if os.path.exists(VECTOR_STORE_FILE):   #if already the chunk exists 
    chunks=load_vector_store()
    print(f"loaded {len(chunks)} chunks from the vector store")
else:
    chunks = create_chunks()
    chunks=add_embeddings(chunks)
    save_vector_store(chunks)
    print(f"created {len(chunks)} chunks and saved to the vector store file")
    
print(f"we have embedded {len(chunks)} chunks")

user_query= "benefits of maternity leave"

test(user_query,chunks,3)