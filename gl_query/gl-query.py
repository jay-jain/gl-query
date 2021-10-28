#!/usr/bin/env python3
### IMPORTS

import os.path
import sys
import datetime
import argparse
from configparser import ConfigParser
import json

import config
from helper import *
from query import *
from output import *
from __init__ import __version__
import config

########################################
##### main() ENTRY POINT
########################################

def main():
    cfg = ConfigParser()
    try:
        with open(os.path.expanduser("~/.gl-query/config.cfg"), "r") as f: d = f.read()
        cfg.read_string(d)
        config.GITLAB_URL = cfg.get("config", "url")
        token = cfg.get("config", "token")
        config.HEADERS = "{'Authorization' : 'Bearer " + token + "'}"

        config.GL_BDAY = str(cfg.get("config", "gl_birthday"))
        config.SCAN_TYPES = json.loads(cfg.get("config", "scan_types"))
        config.LANGS = json.loads(cfg.get("config", "languages"))
        config.PER_PAGE = str(cfg.get("config", "pagination"))
    except:
        print("Looks like you didn't configure your ~/.gl-query/config.cfg file correctly.")
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
    parser.add_argument("--silent"       , help="blocks standard out"      , action="store_true")
    parser.add_argument("--all-languages", help="selects all languages"    , action="store_true")
    parser.add_argument("--version"      , help="max results"              , action='store_true')
    parser.add_argument("--has-srcclr"   , help="max results"              , action='store_true')
    parser.add_argument("--no-srcclr"    , help="max results"              , action='store_true')

    parser.add_argument("--scan-type"    , help="scan types to search for" , action='store'        , type=str)
    parser.add_argument("--pipeline-id"  , help="pipeline id"              , action='store'        , type=int)
    parser.add_argument("--project-id"   , help="project id"               , action='store'        , type=int)
    parser.add_argument("--search"       , help="search for project name"  , action='store'        , type=str)

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

    ## --has-srcclr and --no-srcclr flags
    if args.no_srcclr and args.has_srcclr:
        print("ERROR: You cannot use --no-srcclr and --has-srcclr flags at the same time. Pick one or the other")
        sys.exit(1)
    elif args.no_srcclr:
        print("You will get projects that DO NOT utilze Veracode SourceClear")
    elif args.has_srcclr:
        print("You will get projects that DO utilze Veracode SourceClear")

    ## --version flag
    if args.version:
        print("VERSION: " + __version__ )
        sys.exit(1)

    ## --search flag
    if args.search != None and args.verb != "get" and args.subject != "pipeline":
        print ("ERROR: Improper usage of --search flag. This flag can only be used with 'get pipelines' .")
        sys.exit(1)


    #####################################################################
    ### SUBJECT / VERB LOGIC -- MOVE THIS TO SEPARATE FUNCTION EVENTUALLY
    #####################################################################
    # get scans -- get_scans()
    def all_langs():
        all_languages = list()
        for lang in config.LANGS:
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
            print("Total", scan_names, "Scans between", args.date_after, "and", args.date_before, ": ", config.TOTAL_SCANS)
        elif args.date_before is not None and args.date_after is None:
            print("Total", scan_names, "Scan Jobs prior to", args.date_before, " : ", config.TOTAL_SCANS)
        elif args.date_before is None and args.date_after is not None:
            print("Total ", scan_names, " Scan Jobs after ", args.date_after, " : ", config.TOTAL_SCANS)
        else:
            print("Total", scan_names, "Scan Jobs ever : ", TOTAL_SCANS)

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
        print("TOTAL PIPELINES: ", config.TOTAL_PIPELINES)

    # get projects -- get_projects()
    if args.verb == 'get' and args.subject == 'projects':
        search_query = construct_query(type = 'projects',language = language_flag_helper(args.language), date_after = args.date_after, date_before = args.date_before, search = args.search)
        total_project_pages = paginate(args.subject, search_query)
        result = projects_query(total_project_pages, pipeline_filter_flag, search_query, args.language, args.has_srcclr, args.no_srcclr, args.include_user_repositories)
        if len(result["projects"]) > 0:
            print(pretty_print_projects(result["projects"]))
            fields = ["name","id","team","project_path","last_pipeline","last_activity","visibility","type","languages","default_branch","url"]
            if args.csv: print(csv_writer(result["projects"],fields, filename = args.filename))
        else:
            print("No CSV report generated.")
        print("TOTAL PROJECTS w/ Matching Search Criterion: ", config.TOTAL_PROJECTS)
        if "metadata" in result:
            print("Projects WITH Sourceclear:",str(result['metadata']['has_sourceclear']))
            print("Projects WITHOUT Sourceclear: ",str(result['metadata']['no_sourceclear']))
            print("User Projects: ", str(result['metadata']['user_projects']) )
            print("Projects without any pipeline: ", str(result['metadata']['no_pipelines']) )

    # get project -- get_project()
    if args.verb == 'get' and args.subject =='project':
        if args.project_id:
            result = get_project(args.project_id)
            print(pretty_print_projects(result))
        else:
            print("ERROR: Missing --project-id flag.")
            sys.exit(1)

    print("TOTAL API REQUESTS :", config.API_REQUESTS)

if __name__ == "__main__":
    main()
