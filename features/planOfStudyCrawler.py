from bs4 import BeautifulSoup
import json
import requests
import re

def planOfStudyCrawler(url): 
    response = requests.get(url)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')

    def parse_plan(plan_div):
        parsed_data = []
        for year_div in plan_div.find_all('tr', class_='plangridyear'):
            year_section = {
                "name": year_div.th.text.strip(),
                "terms": []
            }
            terms_header = year_div.find_next_sibling('tr', class_='plangridterm')

            terms = [th.text.strip().upper() for th in terms_header.find_all('th') if th.text.strip() != "Hours"]

            course_rows = terms_header.find_next_siblings('tr')

            term_courses = {term: [] for term in terms if term}

            for row in course_rows:
                if 'plangridyear' in row.get('class', []):
                    break

                course_cells = row.find_all('td', class_='codecol')
                for term, cell in zip(terms, course_cells):
                    links = cell.find_all('a', class_='bubblelink')
                    for link in links:
                        course_code_match = re.match(r'([A-Z]+)\s+(\d+)', link.get('title', ''))
                        if course_code_match:
                            major, number = course_code_match.groups()
                            term_courses[term].append({
                                "type": "COURSE",
                                "data": {"major": major, "number": int(number)}
                            })

            for term, courses in term_courses.items():
                if courses: 
                    year_section["terms"].append({
                        "type": term,
                        "items": courses
                    })

            parsed_data.append(year_section)
        
        return parsed_data

    h2_tags = soup.find_all('h2')
    all_plans_parsed = []

    for h2 in h2_tags:
        if h2.text.startswith('Sample Plan of Study: '):
            plan_div = h2.find_next_sibling('table', class_='sc_plangrid')
            if plan_div:
                plan_name = h2.text.strip()
                plan_data = {
                    "plan_name": plan_name,
                    "data": parse_plan(plan_div)
                }
                all_plans_parsed.append(plan_data)

    parts = url.split('/')
    major = parts[-3]
    degree = parts[-2]

    major = major.replace('-', '_').lower()
    degree = degree.replace('-', '_').lower()

    fileNames = []
    for i, plan in enumerate(all_plans_parsed, start=1):
        fileName = f"planOfStudyJSON/plan_of_study_{major}_{degree}_{i}.json"
        with open(fileName, 'w') as json_file:
            json.dump(plan, json_file, indent=4)
        fileNames.append(fileName)

    return fileNames

url = "https://catalog.northeastern.edu/undergraduate/computer-information-science/information-science/bsis/#planofstudytext"
print(planOfStudyCrawler(url))