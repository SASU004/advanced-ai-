from openai import OpenAI
from dotenv import load_dotenv
import os 
import json
from tools import TOOLS,run_tool
from Utilities.utilities import log

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


messages=[]

#safety limit 
MAX_STEPS=5

# personality 

messages.append(
    {
        "role": "system",
        "content":"You are a very humble and friendly agent be to the point without sugarcoating and always brutally honest"
    }
)
while True:

    user_input = input("🧑🏽\nSasu:")
    if user_input.lower() in ["exit","quit","goodbye"]:
        break 


    #first append the new user input to all the prev ones     
    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    for steps in range(MAX_STEPS): #there can be multiple tool calls
        # now send the whole message list +tools
        response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=messages,
            tools=TOOLS,
        )

        #response from the model 
        
        msg=response.choices[0].message
        
        if not msg.tool_calls: #if no tool call in the message from the llm then just move out the loop of the tool call

            break

        log(f"Step {steps + 1}: model requested {len(msg.tool_calls)}tool calls")
        
        messages.append(msg)  #history of convo

        for tool_call in msg.tool_calls:
            result=run_tool(tool_call)
            
            messages.append( #what ever my tool responded with i need to append that as well
                {
                    "role": "tool", #result is of tool call 
                    "tool_id":tool_call.id, #llm keeps the tack of tools using id inside the fomat so it remebers okay this is the output for tool call no 76 or 67 etc 
                    "content": str(result),
                }
            )
    else: #in pyhton else after a for loop runs only when the loop finished normally and not ended early by a break 
        fallback="Sorry i couldnt finish this within the step limit"
        messages.append(
            {
                "role":"assistant",
                "content":fallback
            }
        )
        print("🤖Assistant: "+ fallback)
        continue

    messages.append(
        {
            "role": "assistant",
            "content": msg.content
        }
    )
    print("🤖Assistant: "+ (msg.content or " "))

    # now append the response as well for the next user input to follow
    # messages.append(
    #     {
    #         "role": "user",
    #         "content": response.choices[0].message.content
    #     }
    # )

    # print("Assistant: " + response.choices[0].message.content)

#role is added for the llm to understand who said what
#this is done cause LLM IS STATELESS and whenever we 
#send anything ot the llm, they actually send the whole convo the llm