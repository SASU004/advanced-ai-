from datetime import datetime
import requests
import json
from Utilities.utilities import log
from chroma_store import search


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # now llm cant see what this tool does so we need to have a format which gives info to the llm that what is this tool and hwo it works 
    # this is why the tools array exists below

def get_city_weather(city):
    url = f"https://wttr.in/{city}?format=3"
    response = requests.get(url,timeout=10)
    response.raise_for_status() #this will raise HTTPError if somehting is wrong 
    return response.text


"""commneted this code cause its the json version """
# def search_knowledge_base(query):
#     results=search(query,3)
#     log(f" 📚 Knowledge Base search: {query} ")  # printing which querry is being searched as a log 
#     for r in results:
#         log(f"  {r["score"]:.2f}-{r["source"]} # {r["chunk_id"]}") # printing all the score etc for all the chunks we fetched

#     blocks=[]
#     for r in results :
#         source_file_name = r["source"]
#         chunk_id         =r["chunk_id"]
#         chunk_text       =r["text"]

#         header = f"[{source_file_name} #{chunk_id}]"        #basic formatting 
#         block=f"{header}\n{chunk_text}"             #header then block text 
#         blocks.append(block)                                        #appending (we can use a string insted as well no issues )

#     return "\n\n".join(blocks) # python utility easy and cool join using 2 \n 

def search_knowledge_base(query):
    results = search(query, 3)

    log(f" 📚 Knowledge Base search: {query}")

    blocks = []
    for r in results:
        log(f"  {r['score']:.2f} - {r['source']} #{r['chunk_id']}")
        blocks.append(f"[{r['source']} #{r['chunk_id']}]\n{r['text']}")

    return "\n\n".join(blocks)


TOOLS=[
    {
        "type":"function", #type of tool is always function 
        "function":{
            "name": "get_time", #name the model will call
            "description":"Returns the current date and time info as a formatted string",
            "parameters":{          #suppose we need time for india specifically then we pass india in this parameter 
                "type":"object",     #always object at top level 
                "properties":{},     #in the format of openai we can also define the mandatory parameter 
            }
        }
    },
    {
        "type":"function",
        "function": {
        "name":"get_city_weather",
        "description":"Returns the current weather for the given city",
        "parameters":{
                "type":"object",
                "properties":{
                    "city":{
                        "type":"string",
                        "description": "city to get the weather for.",
                    }
                },
                "required": ["city"]
            },
        
        },

    },

    {   "type": "function",
        "function":{
            "name":"search_knowledge_base",
            "description":"Searches the Zorvex Technologies company knowledge base: leave, medical, HR, hiring, tech, incident "
                            "reports and travel expense policies. Use it for any question about company policies or documents. "
                            "Returns the most relevant passages with their source.",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":"The user's question, rewritten as a short self-contained short query", 
                    }
  
                },
            }
        }
    }
]


FUNCTION_NAME_TO_funcTION_MAP={
    "get_time": get_time,
    "get_city_weather": get_city_weather,
    "search_knowledge_base":search_knowledge_base,
}

def run_tool(tool_call):
    func_name= tool_call.function.name #we get the function name which my code wants to call (llm understood from the tool description that the code needs to call this function)
    func_args={}
    
    try : #if there is error in tool calling 
        func_args= json.loads(tool_call.function.arguments or "{}") #args is a string according to the format we convert it to a json 
    
        log(f" 🔧{func_name}({func_args})")
    
        fn= FUNCTION_NAME_TO_funcTION_MAP[func_name] #we have already mapped the function name to get the actual pyhton function 
        result = fn(**func_args) #** here is dictionary unpacking operattor
        # this cals the function with the arguments if there is any 
    except Exception as e:
        result = f"Error while running {func_name} : {e}" #this also gets appended to the msg content for llm to figure out 
    
    log(f" ↪{result}")
    return str(result)



