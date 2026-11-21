from datetime import datetime
import requests
import json
from Utilities.utilities import log

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # now llm cant see what this tool does so we need to have a format which gives info to the llm that what is this tool and hwo it works 
    # this is why the tools array exists below

def get_city_weather(city):
    url = f"https://wttr.in/{city}?format=3"
    response = requests.get(url,timeout=10)
    response.raise_for_status() #this will raise HTTPError if somehting is wrong 
    return response.text

TOOLS=[
    {
        "type":"function", #type of tool is always fucntion 
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

    }
]


FUNCTION_NAME_TO_FUCNTION_MAP={
    "get_time": get_time,
    "get_city_weather": get_city_weather,
}

def run_tool(tool_call):
    func_name= tool_call.function.name #we get the fucntion name which my code wants to call (llm understood from the tool description that the code needs to call this fucntion)
    func_args={}
    
    try : #if there is error in tool calling 
        func_args= json.loads(tool_call.function.arguments or "{}") #args is a string according to the format we convert it to a json 
    
        log(f" 🔧{func_name}({func_args})")
    
        fn= FUNCTION_NAME_TO_FUCNTION_MAP[func_name] #we have already mapped the fucntion name to get the actual pyhton function 
        result = fn(**func_args) #** here is dictionary unpacking operattor
        # this cals the fucntion with the arguments if there is any 
    except Exception as e:
        result = f"Error while running {func_name} : {e}" #this also gets appended to the msg content for llm to figure out 
    
    log(f" ↪{result}")
    return str(result)