# importing libraries
import langchain
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import httpx
import os
import re
import streamlit as st


st.title("🤖 Custom Build AI Assistant")


# Loading the environment variables
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')


# Chatbot for Agent
from typing import Any

class ChatBot:
    def __init__(self,system=""):
        self.system=system
        self.message=[]
        if self.system:
            self.message.append({"role":"system","content":system})
    def __call__(self,message):
        self.message.append({"role":"user","content":message})
        result=self.execute()
        self.message.append({"role":"assistant","content":result})
        return result
        
    def execute(self):
        llm = ChatGroq(model_name="Gemma2-9b-It")
        result = llm.invoke(self.message)
        return result.content
    

# Prompt for Chatbot
prompt="""

You are working based on three things such as Thought, Action, Observation:
Thought: Should be what you want to do
Action: Should be the set of tools that can be used 

Observation: Should be your answer

FInal outut: It should be your final answer after observation


i.e. Calculate 6*9

Thought: I want to calculate 6*9

Action: I can use the evaluate function

Observation: 6*9 equals 54

Final Answer: 54

wikipedia:
e.g. wikipedia: Django
Returns a summary from searching Wikipedia

Example session:
Question: What is the capital of France?
Thought: I should look up France on Wikipedia
Action: wikipedia: France
PAUSE

You will be called again with this:
Observation: France is a country. The capital is Paris.

You then output:
Answer: The capital of France is Paris

Please Note: if you get basic conversation questions like "hi","hello","how are you?",\n
you have to answer "hi","hello","i am good".
""".strip()

# Compiling the regular expression pattern
action_re = re.compile('^Action: (\w+): (.*)')

# Define a function for Wikipedia Search
def wikipedia(q):
    response=httpx.get("https://en.wikipedia.org/w/api.php", params={
        "action": "query",
        "list": "search",
        "srsearch": q,
        "format": "json"
    })
    return response.json()["query"]["search"][0]["snippet"]

# Create a function for calculate

def calculate(q):
        return eval(q)

# Also lets create a dictionary for matching obesrvations

known_actions = {
    'calculate': calculate,
    'wikipedia': wikipedia
}

# Creating a query function
# Lets define the query function
def query(question, max_turns=5):
    i = 0
    bot = ChatBot(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        st.write(result)
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        if actions:
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception(f"Unknown action: {action}: {action_input}")
            st.write(" -- running {} {}".format(action, action_input))
            observation = known_actions[action](action_input)
            st.write("Observation:", observation)
            next_prompt = f"Observation: {observation}"
        else:
            return result

input_prompt =st.text_input("Please Enter your question")


if st.button('Generate Response'):
    result=query(input_prompt)
    st.write(result)
