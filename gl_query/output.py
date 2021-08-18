
import csv
from prettytable import PrettyTable
import config
from datetime import date
import datetime

########################################
##### OUTPUT FUNCTIONS
########################################

def pretty_print_projects(projects):
    t = PrettyTable(['Project ID','Project Name','Team','Last Pipeline', 'Project Path', 'Last Activity','Visibility', 'Type','Languages', 'Default Branch'])
    t.sortby = "Last Activity"
    for i in range(len(projects)):
        t.add_row([projects[i]['id'],projects[i]['name'],projects[i]['team'],projects[i]['last_pipeline'],projects[i]['project_path'],projects[i]['last_activity'],projects[i]['visibility'],projects[i]['type'],projects[i]['languages'], projects[i]['default_branch'] ])
    return(t)

def pretty_print_pipelines(pipelines):
    # list(input_list[0].keys())
    # table_headers = [header.capitalize() for header in list(input_list[0].keys())]
    t = PrettyTable([header.capitalize() for header in list(pipelines[0].keys())])
    t.sortby = "Finished_at"
    for i in range(len(pipelines)):
        t.add_row([pipelines[i]['id'],pipelines[i]['branch'],pipelines[i]['status'],pipelines[i]['finished_at'],pipelines[i]['tag_pipeline'],pipelines[i]['duration'] ])
    return(t)

def pretty_print_scans(scans):
    t = PrettyTable([header.capitalize() for header in list(scans[0].keys())])
    t.sortby = "Started_at"
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
