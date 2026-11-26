from openai import OpenAI
from dotenv import load_dotenv
import os 
import json
from tools import TOOLS,run_tool
from Utilities.utilities import log
from types import SimpleNamespace
from memory import list_chats, load_chat, save_chat

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)



messages=[]

#safety limit 
MAX_STEPS=5

# personality 

SYSTEM_PROMPT= {
        "role": "system",
        "content":(
            "You are a helpful, humble assistant for Zorvex Technologies employees. "
            "Answer general questions (programming, science, advice) from your own knowledge. "
            "Use get_time only when the user asks for the current time, and get_city_weather only when the user asks about the weather. "
            "If the user asks about the weather without naming a city, ask which city they mean before calling the tool. "
            "For ANY question about Zorvex policies, benefits, leave, medical cover, HR, hiring, tech processes, incident reports or travel expenses, "
            "you MUST first call search_knowledge_base. "
            "Answer company questions ONLY from the text that search_knowledge_base returns. Do not use outside knowledge for company facts. "
            "After the answer, cite the source like (leave_policy.txt #3). "
            "If the returned text does not contain the answer, say exactly: I could not find this in the knowledge base. "
            "Keep answers under 100 words."
        ),
    }
messages.append(SYSTEM_PROMPT)
chat_file_path=None          # it stores the path of that file where current chat will be stored

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

def show_chats(chats):
    sl_no=1
    for chat in chats:
        title =chat["title"]
        no_of_messages = chat["count"]
        updated_last=chat["updated_last"]
        print(f"{sl_no}. {title} - {no_of_messages} messages - (Last updated:{updated_last})")
        sl_no+=1


#before chat loop ask user if they want to resume existing chats 
existing_chats=list_chats()

if existing_chats:
    last_chat=existing_chats[0]
    answer= input(f"Continue your last chat: {last_chat["title"]}....? (yes/no): ")
    if answer=="yes":
        data=load_chat(last_chat["path"])
        if data is not None:
            messages=[SYSTEM_PROMPT]+data["messages"]
            chat_file_path=last_chat["path"] #since we resumed the chat chat file path is the last chat file path 
            print(f"Resumed: {last_chat["title"]}")


# chat loop 

while True:

    user_input = input("\nSasu: ")
    if user_input.lower() in ["exit","quit","goodbye"]:
        break 

    # now user can give commands like /new, /chats, /resume
    command = user_input.strip().lower()
    if command =="/new":
        messages= [SYSTEM_PROMPT]
        chat_file_path= None #new chat so no file location 
        """so wehn we go to save this using save chat in memory.py it will go path = none so a new file will be created """
        print("Started a new chat. The old one is still saved")
        continue

    if command=="/chats":
        chats= list_chats()
        if chats:
            """if chats are present then print them as numbered list """
            show_chats(chats) 
        else :
            print("No saved chats yet")
        continue


    if command=="/resume":
        chats = list_chats()
        if not chats:
            print ("No chats to resume.")
            continue

        show_chats(chats)
        choice = input("Chat number to resume (Press Enter to cancel): ")
        choice= choice.strip()

        if not choice:
            continue
        if not choice.isdigit() or not (1<= int (choice)<= len(chats)):
            print("Canceleed. Invalid Choice.")
            continue

        picked_chat= chats[int (choice)-1] # indexing using 0 index using the picked chat number from the chats list
        data = load_chat(picked_chat["path"]) # load that chat using the path we used above 
        if data is None:
            print("That chat could not be loaded.")
            continue
        messages=[SYSTEM_PROMPT]+ data["messages"]   # if there is messages just load it 
        chat_file_path= picked_chat["path"]
        print(f"Resumed {picked_chat['title']} ({len(data["messages"])} messages)")
        continue  #now continue talking further




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
        chat_file_path=save_chat(chat_file_path,messages[1:])
        continue

    messages.append({
        "role":"assistant",
        "content": full_response
    })
    chat_file_path=save_chat(chat_file_path,messages[1:])
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



""" LIMITATIONS after adding the kb tool:

    small models might etirely skip the tool calls 
    wrong chunk might be picked cause both llm and embedding mdoel are smal 
    score of the chunk itself might be flawed cause smalll models 
    vector_store:json might become stale cause if we change the knowledge base need to do chunking again and generate this again 
    if wee change the embedding model then the vector_store:json will be invalid 
    we compare querry embedding with every chunk which is slow if we have millions of users 


    fixes:

    we need Vector_DB

 """