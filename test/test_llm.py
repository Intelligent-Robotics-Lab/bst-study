import requests
 
IRL2LLM_URL = "http://141.210.88.210:8015"

IRL2LLM_API_KEY = "46cb30316c0ab1acb513857b3c61dd0ba43be40b82f3927b701b299944d553b3"
 
response = requests.post(

    f"{IRL2LLM_URL}/chat",

    headers={

        "Content-Type": "application/json",

        "X-API-Key": IRL2LLM_API_KEY,

    },

    json={

        "model": "llama3.3:70b",

        "messages": [

            {

                "role": "system",

                "content": "You are irl2llm, a local assistant for the IRL² robotics lab.",

            },

            {

                "role": "user",

                "content": "Write a short greeting for a robot named Maki.",

            },

        ],

        "temperature": 0.2,

        "max_context_tokens": 4096,

    },

    timeout=300,

)
 
response.raise_for_status()

result = response.json()
 
print(result["response"])
 