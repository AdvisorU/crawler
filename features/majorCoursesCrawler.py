import requests
from bs4 import BeautifulSoup
import json

# default: https://catalog.northeastern.edu/undergraduate/CATEGORY/MAJOR/#coursestext
def crawl_courses(URL):
    def clean_string(input_string):
        return input_string.replace('\u00a0', ' ').strip()

    r = requests.get(URL) 

    soup = BeautifulSoup(r.content, 'html5lib')
    soup.prettify()

    courses_list = []

    for block in soup.find_all("div", class_="courseblock"):
        title_text = clean_string(block.find("p", class_="courseblocktitle").text)
        parts = title_text.split('.')
        course_tag, course_number = parts[0].split()
        course_name = clean_string(parts[1])
        credit_hours = clean_string(parts[2].strip(" ()Hours"))
        
        # Extract description
        description = clean_string(block.find("p", class_="cb_desc").text)

        # Prerequisites
        prerequisites = ""
        for p_tag in block.find_all("p", class_="courseblockextra noindent"):
            if "Prerequisite(s):" in p_tag.text:
                prerequisites_text = clean_string(p_tag.text.split("Prerequisite(s):", 1)[1])
                prerequisites = prerequisites_text
        
        # Corequisites
        corequisites = []
        for p_tag in block.find_all("p", class_="courseblockextra noindent"):
            if "Corequisite(s):" in p_tag.text:
                corequisites_text = clean_string(p_tag.text.split("Corequisite(s):", 1)[1])
                corequisites = [clean_string(attr) for attr in corequisites_text.split(",")]
                break

        # Attributes
        attributes = []
        for p_tag in block.find_all("p", class_="courseblockextra noindent"):
            if "Attribute(s):" in p_tag.text:
                attributes_text = clean_string(p_tag.text.split("Attribute(s):", 1)[1])
                attributes = [clean_string(attr) for attr in attributes_text.split(",")]
                break

        course_data = {
            "course_tag": course_tag,
            "course_number": course_number,
            "course_name": course_name,
            "credit_hours": credit_hours,
            "prerequisites": prerequisites,
            "corequisites": corequisites,
            "attributes": attributes,
            "description": description,
        }
        
        courses_list.append(course_data)

    courses_json = json.dumps(courses_list, indent=4, ensure_ascii=False)

    major = URL.split('/')[-2]
    major = major.split('#')[0]
    major = major.replace('-', ' ')
    major = major.title()
    fileName = "majorCoursesJSON/" + major + "_courses_data.json"
    with open(fileName, 'w') as file:
        file.write(courses_json)

    return fileName
