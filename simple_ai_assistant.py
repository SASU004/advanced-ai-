from openai import OpenAI
from dotenv import load_dotenv
import os 

load_dotenv() #by defalut looks for the .env file and puts the values 

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


messages=[]

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
        messages=messages
    )


    # now append the response as well for the next user input to follow
    messages.append(
        {
            "role": "user",
            "content": response.choices[0].message.content
        }
    )

    print("Assistant: " + response.choices[0].message.content)

#role is added for the llm to understand who said what
#this is done cause LLM IS STATELESS and whenever we 
#send anything ot the llm, they actually send the whole convo the llm