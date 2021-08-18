`gl-query` is a tool to query the GitLab API for useful project and pipeline information.

<!-- ![Python Package](https://github.com/jay-jain/gl-query/workflows/Python%20package/badge.svg) -->

<!-- [[_TOC_]] -->

# Installation / Setup

- To install:
```
pip install gl-query
```

OR, To run directly from CLI as traditional Python program (from root dir):
```
python3 gl_query/gl-query.py <SUBJECT> <VERB> --OPTIONS
```

- [Generate a GitLab Personal Access Token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token)

  - Make sure you store this token in a safe place. As a side-note, any results from the `gl-query` tool are dependent on both the permissions you give the token when you generate it as well as the access-rights you have on the GitLab instance.

- Create the `~/.gl-query/config.cfg` file :
```
[config]
# Must include "/api/v4/"
url = https://<GITLAB_HOST>/api/v4/
token = YOUR_GITLAB_PERSONAL_ACCESS_TOKEN
gl_birthday = 2021-01-01
scan_types = ["sast","dast","iast", "mast", "dependency","container"]
languages = "C", "Go", "Java", "Javascript", "Python","Rust", "Scala"]
pagination = 100
```

* `url` (REQUIRED): The URL for the gitlab instance. Note the `https` and `/api/v4/` are required.

* `token` (REQUIRED): Your access token

* `gl_birthday` (REQUIRED) : This is the date your GitLab instance was launched or started being used. This value is necessary for date-filters to work in `gl-query`

* `scan_types` (REQUIRED): This is useful for the scan type queries. This value allows you to determine acceptable scan types to filter on.

* `languages` (REQUIRED): Since the tool provides language filters, you want to limit you queries to languages that are supported in your organization.

* `pagination` (OPTIONAL): This is the `per page` value for pagination on queries. The default value is the max (100)

# Usage
## Positional Arguments
Positional arguments are in the form of **subjects** and **verbs** .
The format for position arguments is:
```
gl-query <VERB> <SUBJECT> --<OPTIONAL_FLAGS>
```

An example would be:
```
gl-query get projects
```
### Verbs
Verbs are the first positional argument

Currently, the only supported verb is `get` as the current purpose of this program is to retrieve information from the GitLab API and output it. For future, it may be worth adding a `set` action in order to make modifications to the state of the GitLab instance. Some proposed actions would be to :

- Trigger a pipeline

- Modify user / group membership (access controls)

- Opening / Modifying / Closing Merge Requests

- Managing Tags / Releases

### Subjects
Subjects are the second positional argument. These are the following supported **subjects**:
- `projects`
- `pipelines`
- `jobs`

## Optional Arguments (Flags)
There are multiple command-line flags compatibile with `gl-query`.

<h3 id="csv-flag">
<code>--csv / -c</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --csv`

This flag takes no arguments. It simply tells `gl-query` to produce a CSV output of the query. When used without the `--filename` flag it will write the CSV file to a default filename in this format: `GL_PROJECT_ACTIVITY_SINCE_${DATE}.csv`


<h3 id="filename-flag">
<code>--filename / -f</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --csv --filename all_projects.csv`

The `--filename` flag is simply the name of CSV file to write to, therefore, it is recommended to have a `.csv` extension. Avoid using relative paths if you do choose to specify the path. If `--filename` flag is used, must use the `--csv` flag.


<h3 id="language-flag">
<code>--language / -l</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --language Scala`

Specify a programming language if you would like to filter GitLab projects by language. The first letter of the language must be capitalized. If flag is not used, all languages will be queried by default.

`TODO`: Exception Handling.

<h3 id="date-before-flag">
<code>--date-before</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --date-before 2019-03-04`

Displays results **before** specified date. The argument must follow the YYYY-MM-DD format.

<h3 id="date-after-flag">
<code>--date-after</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --date-after 2019-03-04`

Displays results **after** specified date. The argument must follow the YYYY-MM-DD format.

<h3 id="has-pipeline-flag">
<code>--has-pipeline / -p</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects -p`

The flag takes no arguments and causes output to only contain results that have at least one associated pipeline. This is useful for viewing projects that have pipeline functionality.

<h3 id="silent-flag">
<code>--silent</code>
</h3>

`<OPTIONAL>`

`USAGE` : `gl-query get projects --lang java -c -f java.csv --silent`

The flag blocks output to the console or standard out. This is good for security purposes (if this tool is being used in the GitLab CI/CD) or if the output is being written to CSV so you don't need console output.

<h3 id="scan-type-flag">
<code>--scan-type</code>
</h3>

`<OPTIONAL>`

`USAGE` :
```
gl-query get scans --scan-type sast --date-after 2021-08-02 -l java

gl-query get scans --date-after 2021-08-02 --scan-type "sast,dast,dependency" -l scala
```

This flag must be used in conjunction with the `get scans` action and outputs job information pertaining to the scan type(s). You can set supported scan types in your `~/.gl-query/config.cfg` file.

If you choose to select multiple scan types, remember to **comma-delimit** them surround them in double quotes as in the example above.

<h3 id="version-flag">
<code>--version</code>
</h3>

Obtains version of `gl-query` utility. This should correspond with a Git Tag.

<h3 id="search-flag">
<code>--search</code>
</h3>

This only works with `get projects`. This will search only by **project name** , not by group or subgroup.

<h3 id="has-srcclr-flag">
<code>--has-srcclr</code>
</h3>

Gets projects that utilize Veracode SourceClear scanning.

<h3 id="no-srcclr-flag">
<code>--no-srcclr</code>
</h3>

Gets projects that **DO NOT** utilize Veracode SourceClear scanning.

<h3 id="all-languages-flag">
<code>--all-languages</code>
</h3>

Only to be used with `get scans`. Gets scans from all supported languages on your GitLab instance.
# Dev Guide
## Useful `curl` commands for troubleshooting
```
curl --header "Authorization: Bearer <your_access_token>" "https://gitlab.com/api/v4/projects"
```

To get `x-total-pages`:
```
curl -s -I --header "Authorization: Bearer <your_access_token>" "https://gitlab.com/api/v4/projects/"
```
## Future Work

- Testing (CI) : Integrate `gl-query_test.sh` script into pipeline or `pre-commit` hook

- Implement the conditional query param (`date_before` versus `date_after` dilemna) [here](#using-date-filters)

- ~~Implement GitLab Birthday in config file~~

- For `get scans` action, implement:
  - Lookup by project-id / project-name

- Implement custom exclude_projects functionality

- API throttling -- backoff after a certain number of API Requests (need to find out GitLab API limits)

- Minimize / consolidate number of API calls

- Investigate more robust / centralized exception Handling

- Flags
    - `--group` : Filter by group
    - `--subgroup` : Filter by subgroup
    - `--include-user-repositories` [ User repos are excluded by default ]

- ~~Implement search functionality for projects: `https://gitlab.com/api/v4/projects?search=<KEYWORD>`~~

- Create a global query options function and child functions for each type of object (projects, pipelines, etc.)

- Integrate `--csv` output for all actions

- Handle flags / options better (maybe through GLOBAL VARIABLE)

## Developer Notes
### Build/Deploy to PyPi
The release strategy is as follows:
- Run tests locally : (`tests/gl-query_test.sh`)
- Determine version
  - Use `tests/reset_version` script
- Deploy to Test PyPi : `tests/deploy_test.sh`
  - Bumps version (modifies three files: `__init__.py`, `setup.cfg`, `setup.py`)
  - Builds `.tar.gz` and `.whl`
  - Uploads both to Tests PyPi
  - Smoke tests: Downloads from Tesst PyPi and tests
- Deploy to (Prod) PyPi : `tests/deploy_prod.sh`
  - Rebuilds `whl` and `.tar.gz`
  - Uploads both to Prod PyPi
  - Smoke tests: Downloads from PyPi and tests

### Query Options / Parameters
- Query parameters are generally of concern when executing listing operations (i.e. list projects, groups, users, pipelines, jobs, merge requests, etc...)
- Query parameters are generally not used when dealing with a specific project or pipeline.

- GLOBAL Query Parameters
  - `per_page`
  - `sort`
  - `order_by`

- Projects Query Parameters
  - `archived=false`
  - `last_activity_after`
  - `last_activity_before`
  - `with_programming_language`
  - `order_by=last_activity_at`

- Pipelines
  - `order_by=updated_at`
  - `yaml_errors=false`
  - `scope=finished`
  - `updated_after`
  - `updated_before`

- To implement `pipeline_id` filter on `get scans`:
  - Iterate through pipeline pages for given project
  - Piggy back off the get_pipeline method for job info
  - Maintain running sum of target scans

### Using Date Filters

tldr; Do not use both `date_before` and `date_after` in **projects** queries.

**Scenario:**

- Today's date is August 3, 2021

- Use Case: You are searching for `sast` scans between July 15, 2021 and July 30, 2021

- Project X has a pipeline which ran on July 15, 2021 with a `sast` scan.

- If you execute a `gl-query` with `--date-before 2021-07-30` and `--date-after 2021-07-15`, this will only include projects that were last active
between July 15, 2021 and July 30, 2021 as it is using the `&last_activity` query parameters.

- If Project X, was updated after `2021-07-30` for any reason, it will not show up in the query results since it's not between the specified date range, therefore excluding a perfectly legitimate `sast` scan from the results.

- The solution to this is to **not use both** the `&last_activity_before` and `&updated_before` query parameters when making requests to `projects` API endpoints respectively. Instead of using the `date_before` param, we will use **just** the `date_after` param. This will ensure that all projects and pipelines will be included in your query.

- Although this avoids the false negative problem, it significantly increases query time since it will query **ALL** projects/pipelines **AFTER** the given date. It is possible to speed this up by implementing the following logic:

  - Conditionally use either the `date_before` or `date_after` for the query params.

  - You will need to introduce a variable called GL_BDAY (basically the first day a project was created)
  ```
  if (DATE_BEFORE - GL_BDAY ) > ( TODAY - DATE_AFTER):
    Use date_after for `&last_activity_after` and `&updated_after` AND do not use date_before
  else:
    Use the date_before for `&last_activity_before` and `&updated_before`
  ```

  - This approach has it's own risks as GL project/pipeline activity may be skewed such that activity was low for the first couple months / year, so keep this into account if you choose to implement this.
