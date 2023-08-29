import json
import streamlit as st
import os
import pandas as pd
import requests
from requests_aws4auth import AWS4Auth
import uuid
MAX_HISTORY_LENGTH = 5
# Huugging face

# HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]
# API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-xxl"
# headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

#Bedrock through Lambda wrapper

API_URL = st.secrets["API_URL"]
auth = AWS4Auth(st.secrets["ACCESS_KEY"],st.secrets["SECRET_KEY"] , 'us-west-2', 'lambda')


st.set_page_config(page_title="🦙💬 Ask me anything about Sagemaker")
# Store LLM generated responses

if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

# Check if the user ID is already stored in the session state
if 'user_id' in st.session_state:
    user_id = st.session_state['user_id']

# If the user ID is not yet stored in the session state, generate a random UUID
else:
    user_id = str(uuid.uuid4())
    st.session_state['user_id'] = user_id

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "input" not in st.session_state:
    st.session_state.input = ""




# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.input = ""
    st.session_state["chat_history"] = []

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)
temprature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, step=0.1, value=0.0)

# Function for generating LLM response


def generate_response(prompt_input):
    # Hugging Face Login
    # payload= {"inputs": "Please answer to the following question.. "+ prompt_input}
    
    # For Hugging face model
    # string_dialogue = "Please answer to the following question.. "
    # payload={"inputs": string_dialogue + prompt_input}
    #response = requests.post(API_URL, headers=headers, json=payload)
    
    # For Bedrock through Lambda wrapper
    question_with_id = {
        'question': prompt_input,
        'id': len(st.session_state.questions)
    }
    st.session_state.questions.append(question_with_id)

    chat_history = st.session_state["chat_history"]
    if len(chat_history) == MAX_HISTORY_LENGTH:
        chat_history = chat_history[:-1]

    payload = json.dumps({
      "question": prompt_input,
      "temperature": temprature,
      "chat_history": chat_history

    })
    print(payload)
    response = requests.post(API_URL, auth=auth,data=payload)
    answer = response.json()['answer']
   
    chat_history.append({
        'question': prompt_input,
        'answer': answer
    })
    sources=  response.json()['sources']
    print(sources)
    documents  = '\n  Articles from the Sources:\n'
    for item in sources:
     temp= "\n"+ item['title'] +":  "+ item['url']
     documents += temp + "\n"
            
    return  answer+ "\n" + documents

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
# if st.session_state.messages[-1]["role"] != "assistant":
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             response = generate_response(prompt) 
#             st.write(response) 
#     message = {"role": "assistant", "content": response}
#     st.session_state.messages.append(message)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt) 
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)