import os 
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

CHAT_FOLDER = os.getenv("CHAT_FOLDER", "chats")


"""now save chat might have a new chat to save or a existing one so we need to send path + messages to the save chat fucntion """


def save_chat(path,messages):
    os.makedirs(CHAT_FOLDER,exist_ok=True)  # if the chat folder doesnt exit make it 
    if path is None:     # for case of new chat 
        filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")   # file name is the date time 
        path= os.path.join(CHAT_FOLDER,f"{filename}.json")
    data ={
        "title": messages[0]["content"][:40],  #title is just the first few text of the first msg of the user  cause user always texts first (not considering the few cases where its different)
        "updated_last":datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "messages":messages,
    }

    """now we could have directly written like
    with open(path,"w",encoding="utf-8")as f:
            json.dump(data, f , indent=2 )


            but suppose it opens and while only half the dumping is over it crashes 
            so not only does the old saveed chat gets deleted but also the new one is only half saved 
            so we use temp

    """
    temp_path=path+".temp"
    with open(temp_path,"w",encoding="utf-8")as f:
            json.dump(data, f , indent=2 )
    os.replace(temp_path,path)   # very powerful python fucntion which renames the temp path to the og path 
    return path 



def load_chat(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
        

def list_chats():
    if not os.path.exists(CHAT_FOLDER):
        return []

    chats=[]

    for chat_file_name in os.listdir(CHAT_FOLDER):
        if not chat_file_name.endswith(".json"):
            continue

        path = os.path.join(CHAT_FOLDER,chat_file_name)  #this is written like this cause fwd and bwd slah used in windows and linux/mac so python has this feature 
        data = load_chat(path)
        if data is None:
            print(f"Corrupted file {chat_file_name}")
            continue

        chats.append({
            "path":path,
            "title": data.get("title"),
            "updated_last":data.get("updated_last"),
            "count": len(data["messages"]),
        })

    chats.sort(key=lambda chat:chat["updated_last"],reverse=True)
    return chats 




"""
PERSONAL DOUBT / UNDERSTANDING:

Does save_chat() preserve previous messages when saving a resumed conversation?

No. save_chat() itself does NOT preserve or append previous messages. It simply takes the messages list passed to it and completely rewrites the JSON file using that list.

So how are previous messages preserved?

The responsibility lies with simple_ai_assistant.py, not save_chat().

Workflow:

1. When resuming a chat, simple_ai_assistant.py loads the existing JSON file using load_chat().

2. It transfers all the previous messages into the active 'messages' list.

3. Whenever a new user message arrives, it appends that message to the existing list.

4. After the assistant responds, its response is also appended to the same list.

5. Now the 'messages' list contains BOTH the entire previous conversation AND the new messages.

6. This complete list is passed to save_chat().

7. save_chat() writes the entire list into a temporary JSON file and uses os.replace() to replace the old JSON file.

IMPORTANT:

We are replacing the FILE, not losing or replacing the CONVERSATION.

The old messages survive because simple_ai_assistant.py explicitly maintains the complete conversation history before calling save_chat().

In short:
simple_ai_assistant.py = Maintains conversation history.
save_chat() = Saves whatever conversation history it receives.
os.replace() = Replaces the old file with the newly saved file.

save_chat() has no independent knowledge of previous conversations.
"""