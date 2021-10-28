import config as config
from helper import *

########################################
##### QUERY FUNCTIONS
########################################

def projects_query(total_project_pages, pipeline_filter_flag, search_query, language, has_srcclr_flag, no_srcclr_flag, user_repos):
    # PROJECTS QUERY: `gl-query get projects`
    global TOTAL_PROJECTS
    projects = list()
    projects_without_srcclr,projects_with_srcclr,user_projects,projects_without_pipeline = 0,0,0,0
    for i in range(1,total_project_pages+1):
        print("Requesting Page # ", i, "of ",total_project_pages, " ..................")
        temp = get_projects(i, search_query)
        temp = exclude_projects(temp) # Exclude certain project ids
        if type(temp) == str:
            print(temp)
            continue
        for j in range(len(temp)):
            if temp[j]["namespace"]["kind"] == "user" and not user_repos:
                user_projects += 1
                print("(", str(j + 1) , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "is a user repository. SKIPPED!")
                continue
            elif language != None and not has_language(temp[j]['id'], language):
                print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT CONTAIN", language,". SKIPPED!")
                continue
            else:
                proj_data = dict()
                if temp[j]["namespace"]["kind"] == "user": user_projects += 1
                if "default_branch" not in list(temp[j].keys()): default_branch = "master"
                else: default_branch = temp[j]['default_branch']
                latest_pipeline = get_latest_pipeline(temp[j]['id'], ref = default_branch)
                proj_data['last_pipeline'] = latest_pipeline["created_at"]
                if pipeline_filter_flag and not config.HAS_PIPELINE:
                    print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT have a pipeline. SKIPPED!")
                    continue
                elif has_srcclr_flag is True or no_srcclr_flag is True:
                    if not config.HAS_PIPELINE:
                        projects_without_pipeline += 1
                        print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT have a pipeline. SKIPPED!")
                        continue
                    elif not has_srcclr(temp[j]['id'], latest_pipeline["pipeline_id"]):
                        projects_without_srcclr += 1
                        print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'], "DOES NOT have a SOURCECLEAR job. SKIPPED!")
                        if no_srcclr_flag: projects = construct_project_data(projects, temp[j], proj_data)
                        continue
                    else:
                        projects_with_srcclr += 1
                        print("[*] (", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'],"IMPLEMENTED SOURCECLEAR")
                        if has_srcclr_flag: projects = construct_project_data(projects, temp[j], proj_data)
                else:
                    print("(", j + 1 , "/ " + str(len(temp)) + " ) Project ID", temp[j]['id'])
                    projects = construct_project_data(projects, temp[j], proj_data)
        print("==================================================================================================================================================================================")
    if has_srcclr_flag or no_srcclr_flag:
        metadata = {"has_sourceclear":projects_with_srcclr, "no_sourceclear": projects_without_srcclr, "user_projects": user_projects, "no_pipelines": projects_without_pipeline}
        result = {"projects":projects,"metadata":metadata}
    else:
        result = {"projects" : projects}
    return result

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
            response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(project_id) + "/pipelines/" + pipeline_id , headers=eval(config.HEADERS)))
            config.API_REQUESTS += 1
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
            config.TOTAL_PIPELINES += 1
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
            if projects[j]["namespace"]["kind"] == "user":
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
                    response = response_validator(requests.get(config.GITLAB_URL + "projects/" + str(projects[j]['id']) + "/pipelines/" + str(pipelines[l]['id']) + "/jobs", headers=eval(config.HEADERS)))
                    config.API_REQUESTS += 1
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
                            config.TOTAL_SCANS += 1
                            scans.append(scan)
                        else:
                            continue
    return scans
