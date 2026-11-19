from datetime import datetime

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # now llm cant see what this tool does so we need to have a format which gives info to the llm that what is this tool and hwo it works 
    # this is why the tools array exists below

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
]


FUNCTION_NAME_TO_FUCNTION_MAP={
    "get_time": get_time,
}