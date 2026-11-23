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
                    "text": f.read(),
                }
            )  
    return documents



def add_embeddings(documents):
    for document in documents:
        vector = get_embedding(document["text"])   #get the semantic value of the documents 
        document["vector"]=vector # add that embedding value to the document itslef 

