# `gl-query`
`gl-query` is a tool to query the GitLab API for useful project and pipeline information.

<!-- ![Python Package](https://github.com/jay-jain/gl-query/workflows/Python%20package/badge.svg) -->

<!-- [[_TOC_]] -->

# Installation / Setup

- To install:
```
pip install gl-query
```

- [Generate a GitLab Personal Access Token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token)

  - Make sure you store this token in a safe place. As a side-note, any results from the `gl-query` tool are dependent on both the permissions you give the token when you generate it as well as the access-rights you have on the GitLab instance.

- Create the `~/.gl-query/config.cfg` file :
```
[config]
# Must include "/api/v4/"
url = https://<GITLAB_HOST>/api/v4/
token = YOUR_GITLAB_PERSONAL_ACCESS_TOKEN
```


# Usage
## Positional Arguments
Positional arguments subject/verb commands for the CLI utility.
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
Subjects are the second positional argument.

Currently the only supported subjects are `project(s)`, `pipelines(s)`, and `scans` which retrieves information with the `get` verb. For future, these are some of the proposed subjects:

- ~~`project` : `get` particular data regarding a project (by name or id); possibly also modify a project~~

- ~~`pipelines` : `get` all pipeline data with optional flag filters.~~

- ~~`pipeline` : `get` particular data regarding a pipeline (by id); possibly also `trigger` a pipeline~~

- ~~`jobs` : `get` all jobs with optional flag filters.~~ **Implemented via the `get pipeline` action**

- `job` : `get` a particular data regarding a job (by id)

- `groups` : `get` all groups with optional flag filters.

- `group` : `get` a group ( by id or name); possibly also modify the group

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

gl-query get scans --date-after 2021-08-02 --scan-type "sast,srcclear,dependency-scan,srcclr" -l scala

```

This flag must be used in conjunction with the `get scans` action and outputs job information pertaining to the scan type(s). Currently there are three scan types supported for this query:
- `sast` (JS, Python, Go, Java, C++, sbt, Rust )
- `dependency-scan` (JS, Python, Go, Java, sbt, Rust)
- `srcclear` or `srcclr` (JS, Python, Go, Java, C++, sbt, Rust )

If you choose to select multiple scan types, remember to **comma-delimit** them surround them in double quotes as in the example above.

## Usage Examples
```
gl-query get project --project-id 3430
gl-query get projects -l scala --date-filter 2021-07-30 --csv --filename test.csv -p

gl-query get pipelines --project-id 4748
gl-query get pipeline --project-id 3430 --pipeline-id 247249

```

# Dev Guide
## Useful `curl` commands for troubleshooting
```
curl --header "Authorization: Bearer <your_access_token>" "https://gitlab.gaikai.com/api/v4/projects"
```

To get `x-total-pages`:
```
curl -s -I --header "Authorization: Bearer <your_access_token>" "https://gitlab.gaikai.org/api/v4/projects/"
```
## Future Work

- ~~Support multiple `--scan-type`. i.e. `--scan-type "sast,srcclr,srcclear,dependency-scan"`~~

- Investigate if `date_before` and `date_after` are not inclusive: If `--date-after` is `2021-07-04` it will should include results after `July 4, 2021 00:00:00`.

- ~~Investigate inconsistencies in `date-filter`~~ See explanation [here](#using-date-filters)

- ~~Language filter on `get scans`~~

- Testing (CI) : Integrate `gl-query_test.sh` script into pipeline or `pre-commit` hook

- Research the names of the scanning jobs and incorporate them into the global `SCAN_TYPES` list
  - Note: SourceClear job names include both: `srcclr` and `srcclear`

- Implement the conditional query param (`date_before` versus `date_after` dilemna) [here](#using-date-filters)

- For `get scans` action, implement:
  - ~~Date Range filter~~
  - Lookup by project-id / project-name

- ~~Implement exclude_projects functionality~~

- API throttling -- backoff after a certain number of API Requests (need to find out GitLab API limits)

- Minimize / consolidate number of API calls

- Investigate more robust / centralized exception Handling

- Flags
    - `--top-level-group`
    - `--cgei-subgroup`
    - `--include-user-repositories`

- Implement search functionality: `https://gitlab.gaikai.org/api/v4/projects?search=nexus`

- Create a global query options function and child functions for each type of object (projects, pipelines, etc.)

- Integrate `--csv` output for all actions

- Investigate a `set` / `edit` action (maybe not)

## Developer Notes
### Manually Deploying to PyPi
```
bumpversion --current-version <CURRENT_VERSION> minor setup.py gl-query/__init__.py --allow-dirty

python3 setup.py sdist bdist_wheel

twine upload dist/gl-query-<VERSION_NUMBER>*
twine upload dist/gl_query-<VERSION_NUMBER>*
```

### Query Options / Parameters
Query opts should really only apply to list endpoints. i.e. list projects, groups, users, pipelines, jobs, merge requests, etc...
Query opts should not be applied to specific looks ups. For example, looking up a specific project by id

GLOBAL QUERY OPTS : per_page, sort, order_by

OBJECT-SPECIFIC QUERY OPTS:
- Projects
    - archived=false
    - last_activity_after
    - last_activity_before
    - with_programming_language
    - order_by=last_activity_at

- Pipelines
    - order_by=updated_at
    - yaml_errors=false
    - scope=finished
    - updated_after
    - updated_before

Implementing pipeline_id filter on `get scans`:
1) Iterate through pipeline pages for given project
2) Piggy back off the get_pipeline method for job info
3) Sum instance of scan

### Using Date Filters

tldr; Do not use both `date_before` and `date_after` in **projects** queries. You 

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


# Useful Queries

## All Scans & All Languages since a certain date
```
gl-query get scans --all-languages --scan-type "sast, dependency-scan, srcclr, srcclear"  --date-after 2021-07-04 --csv -f all_scans_since_07_04_21.csv
```
Note, we query for both `srcclear` and `srcclr` since they are both used as job names in GitLab CI.

## Java SAST Scans ( w/ `--date-after`)
```
# Java SAST Scans (July 3 - August 3)
gl-query get scans --scan-type sast -l Java --date-after 2021-07-03
```

**RESULT:**

`Total SAST Scan Jobs after 2021-07-03 : 576`

## ALL `sast` Scans ( w/ `--date-after`)
`gl-query get scans --scan-type sast --all-languages --date-after 2021-07-03`

## ALL `dependency-scan` ( w/ `--date-after`)
`gl-query get scans --scan-type dependency-scan --all-languages --date-after 2021-07-03`

## ALL `srcclr` or `srcclear` ( w/ `--date-after`)
`gl-query get scans --scan-type srcclr --all-languages --date-after 2021-07-03`

`gl-query get scans --scan-type srcclear --all-languages --date-after 2021-07-03`

## [DANGEROUS] ALL `sast` scans EVER
```
# This will look through every project since GL_BDAY (JANUARY 1, 2019)

TODAY=$(date '+%Y-%m-%d')
gl-query get scans --scan-type sast --all-languages --date-before $TODAY
```