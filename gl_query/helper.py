### IMPORTS
import requests
import json
import config
from datetime import date
import datetime
import os
import sys
from prettytable import PrettyTable

########################################
##### HELPER FUNCTIONS
########################################

def construct_project_data(projects, temp, proj_data):
    proj_data['id'] = temp['id']
    proj_data['name'] = temp['name']
    proj_data['project_path'] = temp['path_with_namespace']
    proj_data['last_activity'] = temp['last_activity_at']
    # proj_data["commit_count"] = temp[j]['statistics']['commit_count']
    proj_data['url'] = temp['web_url']
    proj_data['visibility'] = temp['visibility']
    proj_data['type'] = temp["namespace"]["kind"]
    proj_data['languages'] = project_languages(temp['id'])
    if "default_branch" not in list(temp.keys()): proj_data["default_branch"] = "N/A - Not Found"
    else: proj_data["default_branch"] = temp['default_branch']
    if temp['path_with_namespace'].split('/')[0] == "cgei":
        proj_data['team'] = temp['path_with_namespace'].split('/')[1].capitalize()
    else:
        proj_data['team'] = "N/A"
    projects.append(proj_data)
    config.TOTAL_PROJECTS += 1
    return projects

def valid_date(job_finish_date, date_before, date_after):
    if job_finish_date == None:
        return False
    if date_before is None: # If date_before field is empty, it is set to current date (YYYY-MM-DD)
        date_before = date.today().strftime("%Y-%m-%d")
    if date_after is None:  # If date_after field is empty, it is set to GL_BDAY (2019-01-01)
        date_after = config.GL_BDAY
    # print("DATE BEFORE: ",date_before,"\tDATE_AFTER: ",date_after,"\tJOB_FINISHED AT: ",job_finish_date)
    job_finish_date = datetime.datetime.strptime(job_finish_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%Y-%m-%d') # Convernt string to DateTime back to string (YYYY-MM-DD)
    job_finish_date = datetime.datetime.strptime(job_finish_date, '%Y-%m-%d') # Convert String to DateTime (YYYY-MM-DD)
    date_before = datetime.datetime.strptime(date_before, "%Y-%m-%d")
    date_after = datetime.datetime.strptime(date_after, "%Y-%m-%d")
    if job_finish_date <= date_before and job_finish_date >= date_after:
        return True
    else:
        return False

def get_latest_pipeline(id, ref = ''):
    if ref is None: ref = ''
    response = requests.get(config.GITLAB_URL + "projects/" + str(id) + "/pipelines?per_page=1&page=1&ref=" + ref , headers=eval(config.HEADERS))
    config.API_REQUESTS += 1
    temp = json.loads(response.text)
    # pipeline_id = temp[0]['id']
    if response_validator(response) == False:
        config.HAS_PIPELINE = False
        return {"created_at" : "WARN: [ Failed API Request - Response Code: " + str(response.status_code) + "]"}
    elif len(temp) > 0:
        config.HAS_PIPELINE = True
        return {"created_at": temp[0]["created_at"], "pipeline_id": temp[0]["id"]}
    else:
        config.HAS_PIPELINE = False
        return {"created_at": "No Pipelines in this Project"}

def has_srcclr(project_id, pipeline_id):
    jobs = []
    response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + str(pipeline_id) + "/jobs", headers=eval(config.HEADERS)))
    config.API_REQUESTS += 1
    if response is False:
        print("Issue accessing pipeline: " + str(pipeline_id)+ " . SKIPPED")
        return False
    total_pages = int(response.headers['X-Total-Pages'])
    for page in range(total_pages + 1):
        response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + str(pipeline_id) + "/jobs?page=" + str(page + 1), headers=eval(config.HEADERS)))
        if response is False:
            print("Issue accessing jobs: " + str(pipeline_id)+ " . SKIPPED")
            return False
        jobs += json.loads(response.text)
    srcclr_scan_count = 0
    for m in range(len(jobs)):
        if "srcclear" in jobs[m]["name"] or "srcclr" in jobs[m]["name"] or "source clear report" in jobs[m]["name"]:
            srcclr_scan_count+=1
    if srcclr_scan_count > 0 : return True
    else: return False

def project_languages(id):
    response = requests.get(config.GITLAB_URL + "projects/" + str(id) + '/languages', headers=eval(config.HEADERS))
    config.API_REQUESTS += 1
    temp = json.loads(response.text)
    if response_validator(response) == False:
        return "WARN: [ Failed API Request - Response Code: " + str(response.status_code) + "]"
    elif len(temp) == 0:
        return "No Language Data"
    else:
        out = ''
        for key in temp:
            out += key + " : " + str(temp[key]) + " % \n"
        return out

def has_language(id,language):
    response = requests.get(config.GITLAB_URL + "projects/" + str(id) + '/languages', headers=eval(config.HEADERS))
    config.API_REQUESTS += 1
    temp = json.loads(response.text) # Parse response to JSON
    langs = [ k.lower()  for k in list(temp.keys()) ] # Convert languages dict to list of languages (lowercase)
    if response_validator(response) == False:
        return False
    elif len(temp) == 0:
        return False
    elif language.lower() in langs: # compare target lang (lowercase) to list of list of project's languages (lowercase)
        return True
    else:
        return False

def response_validator(response):
    if response.status_code != 200:
        print("WARN: [ Failed API Request - Response Code: " + str(response.status_code) + "]")
        return False
    return response

def construct_query(type,sort='desc',order_by='updated_at',archived='false', date_after = config.GL_BDAY, date_before = '', language = '', search = ''):
    search_query =  "?per_page=" + str(config.PER_PAGE) + "&sort=" + sort + "&order_by=" + order_by
    # Only using date_after due to false negative issue
    if type == 'projects':
        if language != ''                   : search_query += '&with_programming_language=' + language
        if search != None and search != ''  : search_query += '&search=' + search

        # The case where only --date-before is provided:
        if date_before is not None and date_after is None:
            search_query += "&last_activity_before=" + date_before
        # The case where --date-after is provided and --date-before may or may not be provided:
        elif date_after is not None:
            search_query += "&last_activity_after=" + date_after
        search_query += "&archived=false"
    if type == 'pipelines':
        # The case where only --date-before is provided:
        if date_before is not None and date_after is None:
            search_query += '&updated_before=' + date_before
        elif date_before is None and date_after is not None:
            search_query += '&updated_after=' + date_after
        elif date_before is not None and date_after is not None:
            # Presumably this would select pipelines that were finished between the date_after and date_before.
            #  (ie. alls stages were completed - irrespective if they passed or failed)
            # Is it possible for a pipeline to be updated after it has finished in GitLab world?
            search_query += '&updated_after=' + date_after + '&updated_before=' + date_before
        search_query += "&scope=finished&yaml_errors=false"
    return search_query

def token():
    ### Get GitLab token for API requests
    if os.path.isfile("/etc/gitlab/token.txt"):
        f = open("/etc/gitlab/token.txt","r")
        token = f.readline().rstrip() # rstrip() trailing new line
        f.close()
    else:
        token = input("Please enter you authorized GitLab Token: ")
    return "{'Authorization' : 'Bearer " + token + "'}"

def paginate(endpoint, search_query,project_id=''):
    # Get Pagination Information for Projects
    if endpoint == 'projects':
        PAGINATE_URL = config.GITLAB_URL + endpoint + search_query
        print("PAGINATE_URL:", PAGINATE_URL)
        response = requests.get(config.GITLAB_URL + endpoint + search_query, headers=eval(config.HEADERS))
        config.API_REQUESTS += 1
    elif endpoint =='pipelines':
        config.PAGINATE_URL = config.GITLAB_URL + 'projects/' + str(project_id) +'/pipelines' + search_query
        response = requests.get(config.GITLAB_URL + 'projects/' + str(project_id) + '/pipelines' + search_query, headers=eval(config.HEADERS))
        config.API_REQUESTS += 1
    else:
        print("PAGINATION ERROR -- see paginate() function")
        sys.exit()
    # print("PAGINATE URL: " + PAGINATE_URL)
    if not response_validator(response):
        print("There was an error in the request.")
        return False
    # total_pages = int(response.headers['X-Total-Pages'])
    total_results = int(response.headers['X-Total'])
    print("TOTAL PROJECTS FOUND IN SEARCH QUERY: ", total_results)
    return int(response.headers['X-Total-Pages'])

def get_pipeline(project_id, pipeline_id):
    # Gets the JOB DATA for a specific pipeline
    response = requests.get(config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + str(pipeline_id) + "/jobs", headers=eval(config.HEADERS))
    config.API_REQUESTS += 1
    jobs = json.loads(response.text)
    t = PrettyTable(['Job ID','Job Name','Stage', 'Status', 'Duration(s)', 'Triggered By'])
    if response_validator(response) == False:
        return "WARN: [ Failed API Request - Response Code: " + str(response.status_code) + "]"
    elif len(jobs) > 0:
        failed,success = 0,0
        for i in range(len(jobs)):
            if jobs[i]['status'] == 'success' : success += 1
            if jobs[i]['status'] == 'failed' : failed += 1
            try:
                dur = int(jobs[i]['duration'])
            except:
                dur = jobs[i]['duration']
            t.add_row([ jobs[i]['id'],
                        jobs[i]['name'],
                        jobs[i]['stage'],
                        jobs[i]['status'],
                        dur,
                        jobs[i]['user']['name']
                     ])
        t.add_row(['','FAILED JOBS',str(failed) + " / " + str(round(failed / (failed + success) * 100,2)) + '%','','',''])
        t.add_row(['','SUCCESSFUL JOBS',str(success) + " / " + str(round(success / (failed + success) * 100,2)) + '%','','',''])
    else:
        return "No JOBS found!"
    return t

def get_pipelines(page, search_query, project_id):
    # Gets a singles pipeline's details (NOT JOB INFO)
    search_query += "&page=" + str(page)
    # print("[DEBUG] URL: " + config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines"  + search_query )
    response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines"  + search_query, headers=eval(config.HEADERS)))
    config.API_REQUESTS += 1
    if type(response) is str : return response
    temp = json.loads(response.text)
    return temp

def get_project(id):
    """
    Takes project id and outputs : id, name, project_path, visibility, last_activity, url, type, languages
    """
    out = dict()
    response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(id), headers=eval(config.HEADERS)))
    config.API_REQUESTS += 1
    if type(response) is str : return response
    temp = json.loads(response.text)
    if temp['path_with_namespace'].split('/')[0] == "cgei":
        out['team'] = temp['path_with_namespace'].split('/')[1].capitalize()
    else:
        out['team'] = "N/A"
    out['id'] = temp['id']
    out['name'] = temp['name']
    out['project_path'] = temp['path_with_namespace']
    out['last_activity'] = temp['last_activity_at']
    # out["commit_count"] = temp['statistics']['commit_count']
    out['url'] = temp['web_url']
    out['visibility'] = temp['visibility']
    out['type'] = temp["namespace"]["kind"]
    out['languages'] = project_languages(temp['id'])
    out['last_pipeline'] = get_latest_pipeline(temp['id'])["created_at"]
    if "default_branch" not in list(temp.keys()): out["default_branch"] = "N/A - Not Found"
    else: out["default_branch"] = temp['default_branch']
    result = list()
    result.append(out)
    return result

def get_projects(page,search_query):
    """
    get projects
    """
    search_query += "&page=" + str(page)
    print("[DEBUG] URL: " + config.GITLAB_URL + "projects" + search_query )
    response = response_validator(requests.get(config.GITLAB_URL + "projects" + search_query, headers=eval(config.HEADERS)))
    config.API_REQUESTS += 1
    if type(response) is str : return response
    temp = json.loads(response.text)
    return temp

def language_flag_helper(arg):
    if arg is not None:
        print("You will get results that use the " + arg.upper() + " language.")
        return arg
    else:
        print("No --language flag provided. Querying all languages.")
        return ''

def exclude_projects(projects, filename = "exclude_projects"):
    excluded = list()
    out = list()
    if os.path.isfile(filename):
        with open(filename,"r") as file:
            for line in file:
                excluded.append(line.split("#")[0].rstrip()) # Split on '#' character and rstrip() trailing new line
    for i in range(len(projects)):
        if str(projects[i]['id']) in excluded:
            print("PROJECT ID", projects[i]['id'] ,"is in",filename, "file.")
        else:
            out.append(projects[i])
    return out

def parse_scan_type(scan_type):
    # scan_type is expected to be a comma-delimited string
    parsed = list(set([ scan_type.strip().lower() for scan_type in scan_type.split(',') ]))
    for s in parsed:
        if s not in config.SCAN_TYPES:
            print("[ERROR] Invalid Scan Type: '"+ s + "'. Check your --scan-type flag.")
            sys.exit()
    return parsed
