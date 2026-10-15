from openai import OpenAI
from dotenv import load_dotenv
import os 
import json
from tools import TOOLS,FUNCTION_NAME_TO_FUCNTION_MAP

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


messages=[]

# personality 

messages.append(
    {
        "role": "system",
        "content":"You are a very humble and friendly agent be to the point without sugarcoating and always brutally honest"
    }
)
while True:

    user_input = input("\nSasu:")
    if user_input.lower() in ["exit","quit","goodbye"]:
        break 


    #first append the new user input to all the prev ones     
    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # now send the whole message list 
    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=messages,
        tools=TOOLS,
    )

    msg=response.choices[0].message
    if msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            func_name= tool_call.function.name
            func_args= json.loads(tool_call.function.arguments or "{}")

            fn= FUNCTION_NAME_TO_FUCNTION_MAP[func_name]
            result = fn(**func_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_id":tool_call.id,
                    "content": str(result),
                }
            )

        #2nd call to LLM API
        response=client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=messages
        )

        msg=response.choices[0].message

        messages.append(
            {
                "role": "assistant",
                "content": msg.content
            }
        )

    # now append the response as well for the next user input to follow
    # messages.append(
    #     {
    #         "role": "user",
    #         "content": response.choices[0].message.content
    #     }
    # )

    # print("Assistant: " + response.choices[0].message.content)
    print("Assistant: "+msg.content)

#role is added for the llm to understand who said what
#this is done cause LLM IS STATELESS and whenever we 
#send anything ot the llm, they actually send the whole convo the llm