#!/usr/bin/env python3
### IMPORTS
import requests
import json
import csv
import os.path
import sys
from datetime import date
import datetime
from prettytable import PrettyTable
import argparse
from configparser import ConfigParser
from importlib import resources  # Python 3.7+
from .__init__ import __version__

### VARIABLES
GITLAB_URL=""
HEADERS = ""
TOTAL_PROJECTS = 0
TOTAL_PIPELINES = 0
TOTAL_SCANS = 0
HAS_PIPELINE = True
PER_PAGE = 100
SCAN_TYPES = ["sast","dependency-scan","srcclear", "srcclr"]
API_REQUESTS = 0
LANGS = ["C", "Go", "Java", "Javascript", "Python","Rust", "Scala"] # Supported Security Scan Languages
GL_BDAY = "2019-01-01"

################################################################################
##### FUNCTIONS
################################################################################

########################################
##### QUERY FUNCTIONS
########################################

def projects_query(total_project_pages, pipeline_filter_flag, search_query, language):
    # PROJECTS QUERY: `gl-query get projects`
    global TOTAL_PROJECTS
    projects = list()
    for i in range(1,total_project_pages+1):
        print("Requesting Page # ", i, "of ",total_project_pages, " ..................")
        temp = get_projects(i, search_query)
        temp = exclude_projects(temp) # Exclude certain project ids
        if type(temp) == str:
            print(response)
            continue
        for j in range(len(temp)):
            if temp[j]["namespace"]["kind"] == "user" :
                print("(", str(j + 1) , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "is a user repository. SKIPPED!")
                continue
            elif language != None and not has_language(temp[j]['id'], language):
                print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT CONTAIN", language,". SKIPPED!")
                continue
            else:
                proj_data = dict()
                proj_data['last_pipeline'] = get_latest_pipeline(temp[j]['id'])
                if pipeline_filter_flag and not HAS_PIPELINE:
                    print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT have a pipeline. SKIPPED!")
                    continue
                else:
                    print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'])
                    proj_data['id'] = temp[j]['id']
                    proj_data['name'] = temp[j]['name']
                    proj_data['project_path'] = temp[j]['path_with_namespace']
                    proj_data['last_activity'] = temp[j]['last_activity_at']
                    # proj_data["commit_count"] = temp[j]['statistics']['commit_count']
                    proj_data['url'] = temp[j]['web_url']
                    proj_data['visibility'] = temp[j]['visibility']
                    proj_data['type'] = temp[j]["namespace"]["kind"]
                    proj_data['languages'] = project_languages(temp[j]['id'])
                    if temp[j]['path_with_namespace'].split('/')[0] == "cgei":
                        proj_data['team'] = temp[j]['path_with_namespace'].split('/')[1].capitalize()
                    else:
                        proj_data['team'] = "N/A"
                    projects.append(proj_data)
                    TOTAL_PROJECTS += 1
        print("==================================================================================================================================================================================")
    return projects

def pipelines_query(total_project_pages, search_query, project_id):
     # PIPELINES QUERY: `gl-query get pipelines`
    global TOTAL_PIPELINES, API_REQUESTS
    pipelines = list()
    for i in range(1,total_project_pages+1):
        print("Requesting Page # ", i, "of ",total_project_pages, " ..................")
        temp = get_pipelines(i, search_query, project_id)
        if type(temp) == False:
            print(temp)
            continue
        for j in range(len(temp)):
            pipeline_data = dict()
            pipeline_id = str(temp[j]['id'])
            response = response_validator(requests.get(GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + pipeline_id , headers=eval(HEADERS)))
            API_REQUESTS += 1
            if response == False : continue
            pipeline = json.loads(response.text)
            pipeline_data['id'] = pipeline_id
            pipeline_data['branch'] = pipeline['ref']
            pipeline_data['status'] = pipeline['status']
            pipeline_data['finished_at'] = pipeline['finished_at']
            pipeline_data['tag_pipeline'] = pipeline['tag']
            if type(pipeline['duration']) == type(None):
                pipeline_data['duration'] = "N/A: " + pipeline['status']
            else:
                pipeline_data['duration'] = str(round(pipeline['duration'] / 60 ,2)) + " min"
            pipelines.append(pipeline_data)
            TOTAL_PIPELINES += 1
            print('.', end="", flush=True)
        print("\n==================================================================================================================================================================================")
    return pipelines

def scan_frequency_query(total_project_pages, search_query, scan_type, date_after, date_before, language ):
    """
    # possibly add timeframe filter (so they can search a start and end date )
    # Add following params: project_id
    """
    global TOTAL_SCANS, API_REQUESTS
    pipelines = list()
    scans = list()
    pipeline_search_query = construct_query(type = 'pipelines',order_by='updated_at', date_after = date_after, date_before = date_before )
    for i in range(1,total_project_pages+1): # Iterate through project pages
        print("Requesting Project Page # ", i, "of ",total_project_pages, " ..................")
        projects = get_projects(i, search_query)
        projects = exclude_projects(projects) # Exclude certain project ids
        if type(projects) == str:
            print(projects)
            continue
        for j in range(len(projects)): # Iterate through projects
            print("Analyzing project " + str(j + 1) + " of " + str(len(projects)) + ".")
            if projects[j]["namespace"]["kind"] == "user" :
                print("(", j + 1 , "/ " + str(len(projects)) + " ) Project ID", projects[j]['id'], "is a user repository. SKIPPED!")
                continue
            if language != None and not has_language(projects[j]['id'], language):
                print("(", j + 1 , "/ " + str(len(projects)) + " ) Project ID", projects[j]['id'], "DOES NOT CONTAIN", language,". SKIPPED!")
                continue
            total_pipeline_pages = paginate('pipelines', pipeline_search_query, projects[j]['id'])
            if total_pipeline_pages is False:
                print("Looks like there was an issue accessing the pipelines for project ID: " + str(projects[j]['id']) + " . SKIPPED")
                continue
            for k in range(1,total_pipeline_pages + 1): # Iterate through pipeline pages
                print("Requesting Pipeline Page # ", k, "of ",total_pipeline_pages, "for project ID # " + str(projects[j]['id']))
                pipelines = get_pipelines(k, pipeline_search_query, projects[j]['id'])
                for l in range(len(pipelines)): # Iterate through pipelines
                    print("Analyzing Pipeline # ", pipelines[l]['id'], "for project ID # " + str(projects[j]['id']))
                    response = response_validator(requests.get(GITLAB_URL + "projects/" + str(projects[j]['id']) + "/pipelines/" + str(pipelines[l]['id']) + "/jobs", headers=eval(HEADERS)))
                    API_REQUESTS += 1
                    if response is False:
                        print("Issue accessing pipeline: " + str(pipelines[l]['id']) + " . SKIPPED")
                        continue
                    jobs = json.loads(response.text)
                    for m in range(len(jobs)): # Iterate through jobs
                        is_scan_type = [ s for s in scan_type if s in jobs[m]['name'] ]
                        if len(is_scan_type) > 0 and valid_date(jobs[m]['finished_at'], date_before, date_after):
                            # print("\n\n SAST JOB FOUND")
                            scan  = dict()
                            print(jobs[m]['name'] + " scan was found")
                            scan['job_name'] = jobs[m]['name']
                            scan['project_name'] = projects[j]['name']
                            scan['job_id'] = jobs[m]['id']
                            scan['stage'] = jobs[m]['stage']
                            scan['status'] = jobs[m]['status']
                            scan['duration'] = jobs[m]['duration']
                            scan['triggered_by'] = jobs[m]['user']['name']
                            scan['pipeline_id'] = pipelines[l]['id']
                            scan['project_id'] = projects[j]['id']
                            if jobs[m]['started_at'] == None :
                                scan['started_at'] = 'N/A: Skipped or Cancelled'
                            else:
                                scan['started_at'] = str(jobs[m]['started_at']) + ' UTC'
                            scan['type'] = is_scan_type[0]
                            # scan['finished_at'] = jobs[m]['finished_at']
                            TOTAL_SCANS += 1
                            scans.append(scan)
                        else:
                            continue
    return scans
########################################
##### HELPER FUNCTIONS
########################################

def valid_date(job_finish_date, date_before, date_after):
    if job_finish_date == None:
        return False
    if date_before is None: # If date_before field is empty, it is set to current date (YYYY-MM-DD)
        date_before = date.today().strftime("%Y-%m-%d")
    if date_after is None:  # If date_after field is empty, it is set to GL_BDAY (2019-01-01)
        date_after = GL_BDAY
    # print("DATE BEFORE: ",date_before,"\tDATE_AFTER: ",date_after,"\tJOB_FINISHED AT: ",job_finish_date)
    job_finish_date = datetime.datetime.strptime(job_finish_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%Y-%m-%d') # Convernt string to DateTime back to string (YYYY-MM-DD)
    job_finish_date = datetime.datetime.strptime(job_finish_date, '%Y-%m-%d') # Convert String to DateTime (YYYY-MM-DD)
    date_before = datetime.datetime.strptime(date_before, "%Y-%m-%d")
    date_after = datetime.datetime.strptime(date_after, "%Y-%m-%d")
    if job_finish_date <= date_before and job_finish_date >= date_after:
        return True
    else:
        return False

def get_latest_pipeline(id):
    global HAS_PIPELINE, API_REQUESTS
    response = requests.get(GITLAB_URL + "projects/" + str(id) + "/pipelines?per_page=1&page=1", headers=eval(HEADERS))
    API_REQUESTS += 1
    temp = json.loads(response.text)
    # pipeline_id = temp[0]['id']
    if response_validator(response) == False:
        return "WARN: [ Failed API Request - Response Code: " + str(response.status_code) + "]"
    elif len(temp) > 0:
        HAS_PIPELINE = True
        return temp[0]["created_at"]
    else:
        HAS_PIPELINE = False
        return "No Pipelines in this Project"

def project_languages(id):
    global API_REQUESTS
    response = requests.get(GITLAB_URL + "projects/" + str(id) + '/languages', headers=eval(HEADERS))
    API_REQUESTS += 1
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
    global API_REQUESTS
    response = requests.get(GITLAB_URL + "projects/" + str(id) + '/languages', headers=eval(HEADERS))
    API_REQUESTS += 1
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

def construct_query(type,sort='desc',order_by='updated_at',archived='false', date_after = '', date_before = '', language = ''):
    search_query =  "?per_page=" + str(PER_PAGE) + "&sort=" + sort + "&order_by=" + order_by
    # Only using date_after due to false negative issue
    if type == 'projects':
        if language != ''            : search_query += '&with_programming_language=' + language
        # The case where only --date-before is provided:
        if date_before is not None and date_after is None:
            search_query += "&last_activity_before=" + date_before
        # The case where --date-after is provided and --date-before may or may not be provided:
        else: #if date_after is not None:
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
    global API_REQUESTS
    # Get Pagination Information for Projects
    if endpoint == 'projects':
        PAGINATE_URL = GITLAB_URL + endpoint + search_query
        response = requests.get(GITLAB_URL + endpoint + search_query, headers=eval(HEADERS))
        API_REQUESTS += 1
    elif endpoint =='pipelines':
        PAGINATE_URL = GITLAB_URL + 'projects/' + str(project_id) +'/pipelines' + search_query
        response = requests.get(GITLAB_URL + 'projects/' + str(project_id) + '/pipelines' + search_query, headers=eval(HEADERS))
        API_REQUESTS += 1
    else:
        print("PAGINATION ERROR -- see paginate() function")
        sys.exit()
    # print("PAGINATE URL: " + PAGINATE_URL)
    if not response_validator(response):
        print("There was an error in the request.")
        return False
    # total_pages = int(response.headers['X-Total-Pages'])
    # total_results = int(response.headers['X-Total'])
    return int(response.headers['X-Total-Pages'])

def get_pipeline(project_id, pipeline_id):
    global API_REQUESTS
    # Gets the JOB DATA for a specific pipeline
    response = requests.get(GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + str(pipeline_id) + "/jobs", headers=eval(HEADERS))
    API_REQUESTS += 1
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
    global API_REQUESTS
    # Gets a singles pipeline's details (NOT JOB INFO)
    search_query += "&page=" + str(page)
    # print("[DEBUG] URL: " + GITLAB_URL + "projects/" + str(project_id) + "/pipelines"  + search_query )
    response = response_validator(requests.get(GITLAB_URL + "projects/" + str(project_id) + "/pipelines"  + search_query, headers=eval(HEADERS)))
    API_REQUESTS += 1
    if type(response) is str : return response
    temp = json.loads(response.text)
    return temp

def get_project(id):
    global API_REQUESTS
    """
    Takes project id and outputs : id, name, project_path, visibility, last_activity, url, type, languages
    """
    out = dict()
    response = response_validator(requests.get(GITLAB_URL + "projects/" + str(id), headers=eval(HEADERS)))
    API_REQUESTS += 1
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
    out['last_pipeline'] = get_latest_pipeline(temp['id'])
    result = list()
    result.append(out)
    return result

def get_projects(page,search_query):
    global API_REQUESTS
    """
    get projects
    """
    search_query += "&page=" + str(page)
    print("[DEBUG] URL: " + GITLAB_URL + "projects" + search_query )
    response = response_validator(requests.get(GITLAB_URL + "projects" + search_query, headers=eval(HEADERS)))
    API_REQUESTS += 1
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
            print("PROJECT ID is in",filename, "file.")
        else:
            out.append(projects[i])
    return out

def parse_scan_type(scan_type):
    # scan_type is expected to be a comma-delimited string
    parsed = list(set([ scan_type.strip().lower() for scan_type in scan_type.split(',') ]))
    for s in parsed:
        if s not in SCAN_TYPES:
            print("[ERROR] Invalid Scan Type: '"+ s + "'. Check your --scan-type flag.")
            sys.exit()
    return parsed


########################################
##### OUTPUT FUNCTIONS
########################################

def pretty_print_projects(projects):
    t = PrettyTable(['Project ID','Project Name','Team','Last Pipeline', 'Project Path', 'Last Activity','Visibility', 'Type','Languages'])
    for i in range(len(projects)):
        t.add_row([projects[i]['id'],projects[i]['name'],projects[i]['team'],projects[i]['last_pipeline'],projects[i]['project_path'],projects[i]['last_activity'],projects[i]['visibility'],projects[i]['type'],projects[i]['languages'] ])
    return(t)

def pretty_print_pipelines(pipelines):
    # list(input_list[0].keys())
    # table_headers = [header.capitalize() for header in list(input_list[0].keys())]
    t = PrettyTable([header.capitalize() for header in list(pipelines[0].keys())])
    for i in range(len(pipelines)):
        t.add_row([pipelines[i]['id'],pipelines[i]['branch'],pipelines[i]['status'],pipelines[i]['finished_at'],pipelines[i]['tag_pipeline'],pipelines[i]['duration'] ])
    return(t)

def pretty_print_scans(scans):
    t = PrettyTable([header.capitalize() for header in list(scans[0].keys())])
    for i in range(len(scans)):
        t.add_row([ scans[i]['job_name'], scans[i]['project_name'], scans[i]['job_id'],scans[i]['stage'],scans[i]['status'], scans[i]['duration'],
                   scans[i]['triggered_by'],scans[i]['pipeline_id'],scans[i]['project_id'],scans[i]['started_at'],scans[i]['type'] ])
    return(t)

def csv_writer(data, fields, filename):
    # Takes a list of dictionaries (data), a list of fieldnames (fields), and optionally a filename to write to
    if filename is None:
        date = date.today().strftime("%m_%d_%y")
        filename = "output_" + date + ".csv"
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = fields)
        writer.writeheader()
        writer.writerows(data)
    return "Results written to " + filename + "!"

########################################
##### main() ENTRY POINT
########################################

def main():
    global TOTAL_PROJECTS
    global HEADERS
    global GITLAB_URL
    cfg = ConfigParser()
    try:
        with open(os.path.expanduser("~/.gl-query/config.cfg"), "r") as f: d = f.read()
        cfg.read_string(d)
        GITLAB_URL = cfg.get("config", "url")
        token = cfg.get("config", "token")
        HEADERS = "{'Authorization' : 'Bearer " + token + "'}"
    except:
        print("Looks like you didn't configure you ~/.gl-query/config.cfg file")
        sys.exit(1)
    # HEADERS = token()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="A tool for querying the GitLab API.")

    #####################################################################
    ### ACTIONS / COMMANDS
    #####################################################################
    parser.add_argument(
        'verb',
        nargs='?',
        action='store',
        metavar='VERB',
        help='verbs such as get, set, etc ',
        choices=["get"]
    )
    parser.add_argument(
        'subject',
        nargs='?',
        action='store',
        metavar='SUBJECT',
        help='subjects such as project, pipeline, job, groups, etc. ',
        choices=["projects", "project", "pipelines", "pipeline", "scans"]
    )

    #####################################################################
    ### OPTIONS
    #####################################################################
    parser.add_argument("--silent"       , help="blocks standard out", action="store_true")
    parser.add_argument("--all-languages", help="selects all languages", action="store_true")
    parser.add_argument("--scan-type"    , help="sast, dependency-scan, srcclr, srcclear", type=str, action='store')
    parser.add_argument("--pipeline-id"  , help="pipeline id", type=int, action='store')
    parser.add_argument("--project-id"   , help="project id", type=int, action='store')
    parser.add_argument("--max-results"  , help="max results", type=int, action='store')
    parser.add_argument("--version"      ,help="max results",           action='store_true')

    # --date-after
    parser.add_argument(
        '-d',
        '--date-after',
        action='store',
        metavar='DATEAFTER',
        help='filters results after given date',
    )

    # --date-before
    parser.add_argument(
        '--date-before',
        action='store',
        metavar='DATEBEFORE',
        help='filters results before given date',
    )

    # --csv
    parser.add_argument(
        '-c',
        '--csv',
        action='store_true',
        help='generates CSV file',
    )

    # --filename
    parser.add_argument(
        '-f',
        '--filename',
        action='store',
        help='name and path of CSV file to write to',
    )

    # --language
    parser.add_argument(
        '-l',
        '--language',
        action='store',
        help='programming language to filter by',
    )

    # --has-pipeline
    parser.add_argument(
        '-p',
        '--has-pipeline',
        action='store_true',
        help='display results that have at least one pipeline',
    )

    # To implement: --include-user-repositories
    parser.add_argument(
        '-e',
        '--include-user-repositories',
        action='store_true',
        help='include user/personal repos in results',
    )

    args = parser.parse_args()

    #####################################################################
    ### OPTIONAL FLAG LOGIC
    #####################################################################

    ## --silent
    if args.silent == True:
        sys.stdout = open(os.devnull, 'w')

    ## --scan-type
    if args.scan_type != None:
        args.scan_type = parse_scan_type(args.scan_type)

    ## --csv / --filename flags
    if args.csv and args.filename != None:
            print("You will get a CSV report named " + args.filename)
    elif args.csv:
        print("You will get a CSV report.")

    ## --date-after flag
    if args.date_after != None:
        try:
            datetime.datetime.strptime(args.date_after, '%Y-%m-%d')
            print("You will get results from activity after : " + args.date_after)
        except ValueError:
            print("The date is invalid or incorrectly formatted! It must be in YYYY-MM-DD format. Please try again.")
            sys.exit()

    ## --date-before flag
    if args.date_before != None:
        try:
            datetime.datetime.strptime(args.date_before, '%Y-%m-%d')
            print("You will get results from activity before : " + args.date_before)
        except ValueError:
            print("The date is invalid or incorrectly formatted! It must be in YYYY-MM-DD format. Please try again.")
            sys.exit()


    ## --has-pipeline flag
    if args.has_pipeline:
        pipeline_filter_flag = True
        print("Only results with at least one pipeline will be returned.")
    else:
        pipeline_filter_flag = False

    #####################################################################
    ### SUBJECT / VERB LOGIC -- MOVE THIS TO SEPARATE FUNCTION EVENTUALLY
    #####################################################################
    # get scans -- get_scans()
    def all_langs():
        all_languages = list()
        for lang in LANGS:
            search_query = construct_query(type='projects',language = language_flag_helper(lang), date_after = args.date_after, date_before = args.date_before)
            total_project_pages = paginate('projects', search_query)
            result = scan_frequency_query(total_project_pages, search_query, args.scan_type, date_after = args.date_after, date_before = args.date_before, language = lang)
            all_languages += result # merging the lists
        if len(all_languages) > 0 and args.csv:
            print(pretty_print_scans(all_languages))
            fields = ["job_name","project_name","job_id","stage","status","duration","triggered_by","pipeline_id","project_id", "started_at","type"]
            print(csv_writer(all_languages, fields, args.filename))
        if len(all_languages) > 0:
            print(pretty_print_scans(all_languages))

    def specific_lang(language):
        search_query = construct_query(type='projects',language = language_flag_helper(language), date_after = args.date_after, date_before = args.date_before)
        total_project_pages = paginate('projects', search_query)
        result = scan_frequency_query(total_project_pages, search_query, args.scan_type, date_after = args.date_after, date_before = args.date_before, language = language)
        if len(result) > 0 and args.csv:
            print(pretty_print_scans(result))
            fields = ["job_name","project_name","job_id","stage","status","duration","triggered_by","pipeline_id","project_id", "started_at", "type"]
            print(csv_writer(result, fields, args.filename))
        if len(result) > 0:
            print(pretty_print_scans(result))

    def print_total_scans():
        scan_names = ' / '.join(args.scan_type).upper()
        if args.date_before is not None and args.date_after is not None:
            print("Total", scan_names, "Scans between", args.date_after, "and", args.date_before, ": ", str(TOTAL_SCANS))
        elif args.date_before is not None and args.date_after is None:
            print("Total " + scan_names + " Scan Jobs prior to " + args.date_before + " : " + str(TOTAL_SCANS))
        elif args.date_before is None and args.date_after is not None:
            print("Total " + scan_names + " Scan Jobs after " + args.date_after + " : " + str(TOTAL_SCANS))
        else:
            print("Total" , scan_names , "Scan Jobs ever : " + str(TOTAL_SCANS))

    if args.verb == 'get' and args.subject == 'scans':
        if (args.scan_type is None) :
            print("[ERROR] No --scan-type argument provided. Exiting!")
            sys.exit()
        elif args.date_before is None and args.date_after is None:
            print("[ERROR] --date-before and --date-after flags are empty. You must specify at least one.")
            sys.exit()
        elif args.all_languages is not False and args.language is not None:
            print("You've specified BOTH --language flag and the --all-languages flag. Pick one or the other.")
            sys.exit()
        if args.all_languages: all_langs()
        elif not args.all_languages and args.language is not None:
            specific_lang(args.language)
        print_total_scans()

    # get pipeline  -- get_pipeline()
    if args.verb == 'get' and args.subject == 'pipeline':
        if args.pipeline_id and args.project_id:
            print(get_pipeline(int(args.project_id),int(args.pipeline_id)))
        elif args.pipeline_id and not args.project_id:
            print ("ERROR: Missing the --project-id flag!")
        elif not args.pipeline_id and args.project_id:
            print ("ERROR: Missing the --pipeline-id flag!")

    # get pipelines -- get_pipelines()
    if args.verb == 'get' and args.subject == 'pipelines':
        search_query = construct_query(type = 'pipelines', order_by='updated_at', date_after = args.date_after, date_before = args.date_before)
        total_pipeline_pages = paginate(args.subject, search_query, args.project_id)
        result = pipelines_query(total_pipeline_pages, search_query, args.project_id)
        print(pretty_print_pipelines(result))
        print("TOTAL PIPELINES: " + str(TOTAL_PIPELINES))

    # get projects -- get_projects()
    if args.verb == 'get' and args.subject == 'projects':
        search_query = construct_query(type = 'projects',language = language_flag_helper(args.language), date_after = args.date_after, date_before = args.date_before)
        total_project_pages = paginate(args.subject, search_query)
        result = projects_query(total_project_pages, pipeline_filter_flag, search_query, args.language)
        if len(result) > 0:
            print(pretty_print_projects(result))
            fields = ["name","id","project_path","last_pipeline","last_activity","visibility","type","languages","url"]
            if args.csv: print(csv_writer(result,fields, filename = args.filename))
        else:
            print("No CSV report generated.")
        print("TOTAL PROJECTS: " + str(TOTAL_PROJECTS))

    # get project -- get_project()
    if args.verb == 'get' and args.subject =='project':
        if args.project_id:
            result = get_project(args.project_id)
            print(pretty_print_projects(result))
        else:
            print("ERROR: Missing --project-id flag.")

    if args.version:
        print("VERSION: " + __version__ )
        sys.exit(1)

    print("TOTAL API REQUESTS :", API_REQUESTS)
# if __name__ == "__main__":
#     main()