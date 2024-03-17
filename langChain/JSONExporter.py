from pinecone import Pinecone
from langchain_openai import AzureOpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
load_dotenv()
import os

def use_academic_advisor_agent(input, llm):
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"),
        environment="gcp-starter")

    embedding_client = AzureOpenAIEmbeddings(
        azure_endpoint = os.environ.get("OPENAI_AZURE_HOST"),
        api_key = os.environ.get("OPENAI_API_KEY"), 
        api_version = os.environ.get("OPENAI_API_VERSION"), 
        model = os.environ.get("OPENAI_EMBEDDING_MODEL")
    )

    vector_store = PineconeVectorStore(
        pinecone_api_key = os.environ.get("PINECONE_API_KEY"), 
        embedding = embedding_client, 
        index = pc.Index(name=os.environ.get("PINECONE_INDEX_COURSES_FROM_CATALOG"))
    )

    retriever = vector_store.as_retriever()

    tools = [
        create_retriever_tool(
            retriever,
            "course_from_catalog",
            "Retrieve courses basic information from catalog by given query text."
        )
    ]

    template = '''You are a academic advisor of a university. Answer the following questions about course selection from students as best you can. 

                Here is a sample plan for a student majoring in computer science: 
                ```json
                {plan_of_study}
                ```

                You have access to the following tools:

                {tools}

                Use the following format:

                Question: the input question you must answer
                Thought: you should always think about what to do
                Action: the action to take, should be one of [{tool_names}]
                Action Input: the input to the action
                Observation: the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
                Thought: I now know the final answer
                Final Answer: in json format

                The answer should be in compact json format, including following fields:
                - msg: your final answer
                - data: the data in an array you used to get the answer
                    - 0
                        - major: the major of the course
                        - number: the number of the course
                    - 1
                    ...


                Begin!

                Question: {input}
                Thought:{agent_scratchpad}'''

    prompt = PromptTemplate.from_template(template)

    agent = create_react_agent(
        tools=tools,
        llm=llm,
        prompt=prompt,
    )

    agent_executor = AgentExecutor(
        agent = agent, 
        tools = tools, 
        verbose = True, 
        handle_parsing_errors = True ,
        return_intermediate_steps = True
    )

    result = agent_executor.invoke({
        'plan_of_study': '[{"name":"Year 1","terms":[{"type":"FALL","items":[{"type":"COURSE","data":{"major":"CS","number":1200}},{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":1800}},{"type":"COURSE","data":{"major":"CS","number":1802}}]},{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":2500}},{"type":"COURSE","data":{"major":"CS","number":2501}}]},{"type":"COURSE","data":{"major":"ENGW","number":1111}},{"type":"COURSE","data":{"major":"MATH","number":1365}}]},{"type":"SPRING","courses":[{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":2500}},{"type":"COURSE","data":{"major":"CS","number":2501}}]},{"type":"COURSE","data":{"major":"CS","number":2810}},{"type":"PLACEHOLDER","data":{"description":"Science elective with lab"}},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]},{"type":"SUMMER1","courses":[{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":3500}},{"type":"COURSE","data":{"major":"CS","number":3501}}]},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]},{"type":"SUMMER2","courses":[{"type":"COURSE","data":{"major":"MATH","number":1341}},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]}]},{"name":"Year 2","terms":[{"type":"FALL","items":[{"type":"COURSE","data":{"major":"CS","number":1210}},{"type":"COURSE","data":{"major":"CS","number":3000}},{"type":"COURSE","data":{"major":"CS","number":3650}},{"type":"PLACEHOLDER","data":{"description":"Concentration course"}},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]},{"type":"SPRING","courses":[{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":2500}},{"type":"COURSE","data":{"major":"CS","number":2501}}]},{"type":"COURSE","data":{"major":"CS","number":2810}},{"type":"PLACEHOLDER","data":{"description":"Science elective with lab"}},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]},{"type":"SUMMER1","courses":[{"type":"GROUP","items":[{"type":"COURSE","data":{"major":"CS","number":3500}},{"type":"COURSE","data":{"major":"CS","number":3501}}]},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]},{"type":"SUMMER2","courses":[{"type":"COURSE","data":{"major":"MATH","number":1341}},{"type":"PLACEHOLDER","data":{"description":"Elective"}}]}]}]', 
        'input': input
        })
    
    return result