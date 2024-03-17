from dotenv import load_dotenv
load_dotenv()
import json
from openai import AzureOpenAI
import os
from pinecone import Pinecone, ServerlessSpec

## Embedding textual data
client = AzureOpenAI(
    api_version = os.environ.get("OPENAI_API_VERSION"),
    api_key = os.environ.get("OPENAI_API_KEY"),
    azure_endpoint=os.environ.get("OPENAI_AZURE_HOST"),
)

def courseToPinecone(file_path: str, api_key: str, index_name: str):
    courses_json = None

    with open(file_path, 'r') as file:
        courses_json = json.load(file)

    # # example course data
    # course_descriptions = [
    #     {
    #         "course_tag": "CS",
    #         "course_number": "4991",
    #         "course_name": "Research",
    #         "credit_hours": "4,8",
    #         "prerequisites": "CS 3500 or CS 3800",
    #         "corequisites": [],
    #         "attributes": [
    #             "NUpath Capstone Experience",
    #             "NUpath Integration Experience",
    #             "NUpath Writing Intensive"
    #         ],
    #         "description": "Offers an opportunity to conduct research under faculty supervision. May be repeated up to three times."
    #     },
    # ]

    def get_embeddings_from_custom_endpoint(courses):
        embeddings = []
        
        for course in courses:
            print(course['course_number'])
            # Ensure payload is defined here
            response = client.embeddings.create(
                model=os.environ.get("OPENAI_EMBEDDING_MODEL"),
                input=json.dumps(course),
                encoding_format="float"
            )
            embedding_vector = response.data[0].embedding

            temp_dict = {
                "id": course['course_tag'] + course['course_number'],
                "values": embedding_vector,
                "metadata": {
                    "major": course['course_tag'],
                    "number": course['course_number'],
                    "name": course['course_name'],
                    "credits": course['credit_hours'],
                    "prerequisites": course['prerequisites'],
                    "corequisites": course['corequisites'],
                    "attributes": course['attributes'],
                    "text": json.dumps(course)
                }
            }

            embeddings.append(temp_dict)
        
        return embeddings

    course_embeddings = get_embeddings_from_custom_endpoint(courses_json)

    print(course_embeddings)

    ## import to Pinecone
    def importToPinecone(embeddings):
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        index.upsert(vectors=embeddings)

    # dimension: 3072
    importToPinecone(course_embeddings)