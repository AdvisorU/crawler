import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage
from pinecone import Pinecone
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools.retriever import create_retriever_tool
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
import json
from dotenv import load_dotenv
load_dotenv()
import os

## initialization
llm = AzureChatOpenAI(
    azure_endpoint = os.environ.get("OPENAI_AZURE_HOST"),
    api_key = os.environ.get("OPENAI_API_KEY"), 
    api_version = os.environ.get("OPENAI_API_VERSION"), 
    model = os.environ.get("OPENAI_GPT35_MODEL"),
    temperature=0, 
)

## backend code
prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template("You are a academic advisor of a university. Answer the following questions about course selection from students as best you can. "),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
    memory=memory,
    return_final_only=True
)


## frontend code
st.title("AI Chatbot")

# Use Streamlit's sidebar for conversation history
with st.sidebar:
    st.header("Conversation History")
    conversation_selectbox = st.selectbox(
        "Select a conversation:",
        options=list(range(len(st.session_state.get('saved_conversations', [])))),
        format_func=lambda x: f"Conversation {x+1}"
    )
    if st.button("Load Conversation"):
        st.session_state.chat_history = st.session_state.saved_conversations[conversation_selectbox]

# Session state to store chat history and saved conversations
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'saved_conversations' not in st.session_state:
    st.session_state.saved_conversations = []

#user input
chat_container = st.container()
for chat in st.session_state['chat_history']:
    if chat['sender'] == "You":
        chat_container.markdown(f"**You**: {chat['message']}")
    else:
        chat_container.markdown(f"**AI Advisor**: {chat['message']}")
        
def send_message():
    user_input = st.session_state.user_input
    if user_input:
        # Append user input to chat history
        st.session_state['chat_history'].append({"sender": "You", "message": user_input})
    
    # Process the conversation
    response = conversation({"question": user_input})
    
    # Assuming `conversation.memory.buffer` returns the last AIMessage
    last_aimessage = next((msg.content for msg in reversed(response['chat_history']) if isinstance(msg, AIMessage)), "No response found.")
    
    # Append AI response to chat history
    st.session_state['chat_history'].append({"sender": "AI Advisor", "message": last_aimessage})
    
    # Clear the input box after sending the message
    st.session_state.user_input = ''
    
user_input = st.text_input("Message ChatGPT...", key="user_input", on_change=send_message)

# Clear chat history button
if st.button("Clear Chat"):
    st.session_state['chat_history'] = []

# Save the current conversation to the list of saved conversations
if st.sidebar.button("Save Current Conversation"):
    st.session_state.saved_conversations.append(st.session_state.chat_history)
    st.sidebar.success("Conversation saved!")