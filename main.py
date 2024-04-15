from dotenv import load_dotenv
import requests
import os
import anthropic
import uvicorn
from fastapi import FastAPI

load_dotenv()


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(
    api_key=CLAUDE_API_KEY,
)

def get_user_tweets(screen_name):
    screen_name_url = "https://twitter-v24.p.rapidapi.com/user/tweets"
    querystring = {"username":screen_name,"limit":"10"}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "twitter-v24.p.rapidapi.com"
    }
    response = requests.get(screen_name_url, headers=headers, params=querystring)
    data = response.json()
    pinned_tweet = None
    if data['data']['user']['result']['timeline_v2']['timeline']['instructions'][2]:
        pinned = data['data']['user']['result']['timeline_v2']['timeline']['instructions'][1]
        pinned_tweet = get_full_texts(pinned)
        description = data['data']['user']['result']['timeline_v2']['timeline']['instructions'][2]
    else:
        description = data['data']['user']['result']['timeline_v2']['timeline']['instructions'][1]    
    return f"Tweets of {screen_name}: ", get_full_texts(description), f"Pinned Tweets of {screen_name}:", pinned_tweet
index = 1  # Initialize index counter

index = 1  # Initialize index counter

def get_full_texts(data):
    global index  # Use the global index variable
    full_texts = []
    stack = [(data,)]
    
    while stack:
        current = stack.pop()
        data = current[0]

        if isinstance(data, dict):
            if 'full_text' in data:
                full_texts.append(f"{index}: {data['full_text']}")  # Append tweet with index
                index += 1  # Increment index counter only when a tweet is appended
            stack.extend([(v,) for v in data.values()])
        elif isinstance(data, list):
            stack.extend([(item,) for item in data])

    return full_texts

def generate_summary(data ,screen_name):
    message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=400,
    temperature=0.8,
    system=f"You are the world's best twitter-based summary bot. based on the user given tweets explain to me in a brutally honest way who {screen_name} is. what type of person they are, Their interests and everything else that would be relevant to sending them a personalized cold dm, output only the summary and nothing else make it readable and understandable to LLM's for further usage. summary should consits of: who he is(what type of guy/girl you think they are), interests and attitude. Note: Do NOT add stuff like 'Based on the tweets,' Based on the information provided', etc...",
    messages=[
        {"role": "user", "content": f"{data}"}
    ]
    )
    return message.content[0].text


main = FastAPI()

@main.get("/generate-summary/")
async def generate_summary_endpoint(screen_name: str):
    tweets_data = get_user_tweets(screen_name)
    summary = generate_summary(tweets_data, screen_name)
    return {"screen_name": screen_name, "summary": summary}
