[config]
# Must include "/api/v4/"
url = https://<GITLAB_HOST>/api/v4/
token = YOUR_GITLAB_PERSONAL_ACCESS_TOKEN
gl_birthday = 2021-01-01
scan_types = ["sast","dast","iast", "mast", "dependency","container"]
languages = "C", "Go", "Java", "Javascript", "Python","Rust", "Scala"]
pagination = 100