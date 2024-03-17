import streamlit as st
from features.majorCoursesCrawler import crawl_courses
import json
from features.courseToPinecone import courseToPinecone
from features.planOfStudyCrawler import planOfStudyCrawler
import os

# -- Set page config
apptitle = 'Admin'
st.set_page_config(page_title=apptitle, page_icon=":pencil:")

# Title the app
st.title('Admin Page')


## Left Panel
with st.sidebar:
    st.markdown("---")
    st.write("This is the Major Courses part")

    # Major Courses Crawler Form
    with st.form("Major Courses Crawler Form"):
        st.write("Crawl the courses from a specific major in the catalog")
        courseCrawlerURL = st.text_input(
            "Enter the link to the courses: ",
            placeholder="https://catalog.northeastern.edu/undergraduate/CATEGORY/MAJOR/#coursestext"
        )
        
        courseCrawler_form_submitted = st.form_submit_button("Submit")
        if courseCrawler_form_submitted:
            st.write("You submitted the form")
            courseCrawler_crawled_content = crawl_courses(courseCrawlerURL)

    st.markdown("---")
    st.write("This is the Plan of Study Crawler part")

    # Plan of Study Crawler Form
    with st.form("Plan of Study Crawler Form"):
        st.write("Crawl the plan of study from a specific major in the catalog")
        planOfStudyCrawlerURL = st.text_input(
            "Enter the link to the courses: ",
            placeholder="https://catalog.northeastern.edu/undergraduate/CATEGORY/MAJOR/DEGREE/#planofstudytext"
        )
        
        planOfStudyCrawler_form_submitted = st.form_submit_button("Submit")
        if planOfStudyCrawler_form_submitted:
            st.write("You submitted the form")
            planOfStudyCrawler_crawled_content = planOfStudyCrawler(planOfStudyCrawlerURL)

    st.markdown("---")
    st.write("This is the Pinecone Export part")

    # Pinecone Form
    with st.form("To Pinecone Form"):
        st.write("Export the Course Catalog JSON to Pinecone")
        PFfilePath = st.text_input(
            "Enter the file path to the courses you wish to export to pinecone: ",
            placeholder="json/courses_data.json"
        )
        PFapiKey = st.text_input(
            "Enter the API key for Pinecone: ",
            placeholder="API_KEY"
        )
        PFindexName = st.text_input(
            "Enter the index name for Pinecone: ",
            placeholder="INDEX_NAME"
        )
        pinecone_submitted = st.form_submit_button("Submit")
        if pinecone_submitted:
            st.write("You submitted the form")
            courseToPinecone(file_path=PFfilePath, api_key=os.environ.get("PINECONE_API_KEY"), index_name=os.environ.get("PINECONE_INDEX_COURSES_FROM_CATALOG"))


##Right Panel

# Generated json
st.markdown("---")
st.write("Courses in this field has been crawled to the following file path:")

# Major Courses Crawler
if courseCrawler_form_submitted:
    st.write(courseCrawler_crawled_content)
    st.balloons()

    with open(courseCrawler_crawled_content, "r") as CCfile:
        CCdata = json.load(CCfile)
        st.json(
            CCdata,
            expanded=False
        )
else:
    st.write("No json generated yet")
st.markdown("---")

# Crawl Plan of Study
if planOfStudyCrawler_form_submitted:
    st.write(planOfStudyCrawler_crawled_content)
    st.balloons()

    if planOfStudyCrawler_form_submitted:
        st.write("Crawled plans:")
        st.balloons()

        for filename in planOfStudyCrawler_crawled_content:
            with open(filename, "r") as POSfile:
                POSdata = json.load(POSfile)
                st.json(POSdata, expanded=True)
    else:
        st.write("No JSON generated yet.")
else:
    st.write("No json generated yet")
st.markdown("---")

# Export to Pinecone
st.write("Pinecone Export:")

if pinecone_submitted:
    st.write("Successfully exported!")
    st.write(courseToPinecone)
    st.balloons()
else:
    st.write("Not exported yet")
st.markdown("---")