from openai import OpenAI
from dotenv import load_dotenv
import os 
import json
from tools import TOOLS,run_tool
from Utilities.utilities import log
from types import SimpleNamespace

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
        "content":"You are a very humble and friendly agent be to the point without sugarcoating and always brutally honest only call the tools when time and weather are requested always 100 words "
    }
)

def build_tool_calls_payload(tool_calls):
    """
    Converts our collected tool calls into the dict format 
    which the API inside the assistant expects
    """
    payload=[]
    for tool_call in tool_calls:
        tool_call_dict={
            "id": tool_call.id,
            "type":"function",
            "function":{
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }
        payload.append(tool_call_dict)

    return payload

def stream_chat(history):
    stream = client.chat.completions.create(
        model=os.getenv("MODEL"),                        
            messages=messages,
            tools=TOOLS,
            stream=True,
    )

    full_response=""
    calls={}
    user_assistant_label=False



    #streaming started 
    try:
        for chunk in stream:
            if not chunk.choices:               #if no chunk present 
                continue

            delta = chunk.choices[0].delta    # in openai api message and delta are just different thing sin terms of total message and a chunk of message 

            # content streaming : do we have content from llm 
            if delta.content:                                   # if there is a chunk 
                if not user_assistant_label:
                    print("🤖 Assistant: ",end="",flush=True)
                    user_assistant_label=True
                print(delta.content,end="",flush=True)
                full_response += delta.content              #we are continously building the full response by appending the delta contents 

            # tool call
            for tc in (delta.tool_calls or [] ):     # tc = tool call---if there is tool call in delta as well as tool call in that list of tool calls
                """
                here we are taking in the tool call and creating an object first 
                because its very much possible that the tool call details dont come all at once 
                """
                obj = calls.setdefault(
                    tc.index,
                    SimpleNamespace(id=None, function= SimpleNamespace(name="",arguments ="")),             
                ) 
                if tc.id:
                    obj.id=tc.id
                if tc.function and tc.function.name:
                    obj.function.name +=tc.function.name   #if name comes in differenet chunks we add it up 
                if tc.function and tc.function.arguments:
                    obj.function.arguments += tc.function.arguments

    except KeyboardInterrupt:
        print("\nRok diya na dalle")
        calls={}
        exit()


    
    if user_assistant_label:
        print()        #move to the next line after assistant response 

    calls_list =[]
    for key in sorted(calls):
        calls_list.append(calls[key])   #we sort the tool calls cause it might come in different orders

    return full_response,calls_list


# chat loop 

while True:

    user_input = input("\nSasu: ")
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
        # response = client.chat.completions.create(
        #     model=os.getenv("MODEL"),                         moving this portion to new function 
        #     messages=messages,
        #     tools=TOOLS,
        # )
        full_response,tool_calls=stream_chat(messages)     #moving the above snippet here for streaming 
        #response from the model 
        
        # msg=response.choices[0].message     this also will not be used for streaming the output 
        
        if not tool_calls: #if no tool call in the message from the llm then just move out the loop of the tool call

            break

        log(f"Step {steps + 1}: model requested {len(tool_calls)}tool calls")
        
        messages.append({
            "role": "assistant",
            "content":full_response,
            "tool_calls": build_tool_calls_payload(tool_calls)           # multiple tool + their details 
        })  #history of convo
        

        for tool_call in tool_calls:
            result=run_tool(tool_call)
            
            messages.append( #what ever my tool responded with i need to append that as well
                {
                    "role": "tool", #result is of tool call 
                    "tool_call_id":tool_call.id, #llm keeps the tack of tools using id inside the fomat so it remebers okay this is the output for tool call no 76 or 67 etc 
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
        print("🤖 Assistant: "+ fallback)
        continue

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