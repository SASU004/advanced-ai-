from datetime import datetime

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TOOLS=[
    {
        "type":"function",
        "function":{
            "name": "get_time",
            "description":"Returns the current date and time info as a formatted string",
            "parameters":{
                "type":"object",
                "properties":{},
            }
        }
    },
]


FUNCTION_NAME_TO_FUCNTION_MAP={
    "get_time": get_time,
}