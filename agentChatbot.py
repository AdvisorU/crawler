import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
)
from pinecone import Pinecone
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.agents import AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()
import os

## LLM
llm = AzureChatOpenAI(
    azure_endpoint = os.environ.get("OPENAI_AZURE_HOST"),
    api_key = os.environ.get("OPENAI_API_KEY"), 
    api_version = os.environ.get("OPENAI_API_VERSION"), 
    model = os.environ.get("OPENAI_GPT35_MODEL"),
    temperature=1, 
)

# Database
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"),
    environment="gcp-starter")

embedding_client = AzureOpenAIEmbeddings(
    azure_endpoint = os.environ.get("OPENAI_AZURE_HOST"),
    api_key = os.environ.get("OPENAI_API_KEY"), 
    api_version = os.environ.get("OPENAI_API_VERSION"), 
    model = os.environ.get("OPENAI_EMBEDDING_MODEL")
)

index_name = os.environ.get("PINECONE_INDEX_COURSES_FROM_CATALOG")
vector_store = PineconeVectorStore(
    pinecone_api_key = os.environ.get("PINECONE_API_KEY"), 
    embedding = embedding_client, 
    index = pc.Index(name=index_name)
)

retriever = vector_store.as_retriever()

tools = [
    create_retriever_tool(
        retriever,
        "course_from_catalog",
        "Retrieve courses basic information from catalog by given query text."
    )
]

## backend code

# temp
plan_of_study = '{"plan_name":"Sample Plan of Study: Four Years, Two Co-ops in Spring/Summer 1","data":[{"name":"Year 1","terms":[{"type":"FALL","items":[{"type":"COURSE","data":{"major":"CS","number":1200}},{"type":"COURSE","data":{"major":"CS","number":1800}},{"type":"COURSE","data":{"major":"CS","number":1802}},{"type":"COURSE","data":{"major":"CS","number":2500}},{"type":"COURSE","data":{"major":"CS","number":2501}},{"type":"COURSE","data":{"major":"ENGW","number":1111}},{"type":"COURSE","data":{"major":"MATH","number":1365}}]},{"type":"SPRING","items":[{"type":"COURSE","data":{"major":"CS","number":2510}},{"type":"COURSE","data":{"major":"CS","number":2511}},{"type":"COURSE","data":{"major":"CS","number":2810}}]},{"type":"SUMMER 1","items":[{"type":"COURSE","data":{"major":"CS","number":3500}},{"type":"COURSE","data":{"major":"CS","number":3501}}]},{"type":"SUMMER 2","items":[{"type":"COURSE","data":{"major":"MATH","number":1341}}]}]},{"name":"Year 2","terms":[{"type":"FALL","items":[{"type":"COURSE","data":{"major":"CS","number":1210}},{"type":"COURSE","data":{"major":"CS","number":3000}},{"type":"COURSE","data":{"major":"CS","number":3650}}]},{"type":"SUMMER 2","items":[{"type":"COURSE","data":{"major":"EECE","number":2322}},{"type":"COURSE","data":{"major":"EECE","number":2323}}]}]},{"name":"Year 3","terms":[{"type":"FALL","items":[{"type":"COURSE","data":{"major":"CS","number":3800}}]},{"type":"SUMMER 2","items":[{"type":"COURSE","data":{"major":"ENGW","number":3302}}]}]},{"name":"Year 4","terms":[{"type":"SPRING","items":[{"type":"COURSE","data":{"major":"CS","number":4530}}]}]}]}'

template = '''You are a academic advisor of a university. Answer the following questions about course selection from students as best you can. You can have multiple chat with the student. 

            Here is a sample plan for a student majoring in computer science: 
            ```json
            {plan_of_study}
            ```

            You have access to the following tools:

            {tools}

            Use the following format, you can skip some of steps if you cannot finish your mission with the information you currently have:

            "Question": the input question you must answer
            "Thought": you should always think about what to do
            "Action": the action to take, should be one of [{tool_names}]
            "Action Input": the input to the action
            "Observation": the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            "Thought": I now know the final answer
            "Final Answer": in json format

            The answer should be in compact json format, including following fields:
            - msg: your final answer
            - data: the data in an array you used to get the answer
                - 0
                    - major: the major of the course
                    - number: the number of the course
                - 1
                ...

                
            If the user says something not related to your job as an academic advisor, return a message that explain you cannot answer the question. 

            Begin!

            Question: {input}
            Thought:{agent_scratchpad}
'''

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            template,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        MessagesPlaceholder(variable_name="tool_names"),
        HumanMessagePromptTemplate.from_template("{input}"),
    ]
)

agent = create_openai_tools_agent(
    tools=tools,
    llm=llm,
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent = agent, 
    tools = tools, 
    verbose = True, 
    handle_parsing_errors = True,
    return_intermediate_steps = False,
)

chat_history_for_chain = ChatMessageHistory()

conversational_agent_executor = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: chat_history_for_chain,
    input_messages_key="input",
    output_messages_key="output",
    history_messages_key="chat_history",
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
    
    agent_scratchpad = {
        "recent_queries": [],
        "user_preferences": {
            "preferred_majors": [],
            "avoided_courses": [],
        "output_preferences": 'json'
        },
        "session_data": {
            "current_step": "initial",
            "gathered_info": {}
        }
    }

    def update_scratchpad_with_query(query):
        # Append the query to the list of recent queries
        agent_scratchpad["recent_queries"].append(query)
        
    update_scratchpad_with_query("I want most of my classes to be the same as the plan of study")

    response = conversational_agent_executor.invoke(
        {
            "input": [HumanMessage(content=user_input)],
            "chat_history": chat_history_for_chain.messages,
            "agent_scratchpad": agent_scratchpad,
            "plan_of_study": plan_of_study,
            "tools": tools,
            'tool_names': ['course_from_catalog'],
        },
        {"configurable": {"session_id": "chatbot"}}
    )
    
    last_aimessage = response['output']
    chat_history_for_chain.add_user_message(user_input)
    chat_history_for_chain.add_ai_message(last_aimessage)
    
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