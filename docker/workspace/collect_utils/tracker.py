import os
import json

COMMIT_LOG_CMD = "java -Xmx2g -jar /root/workspace/tools/code-tracker-2.6-SNAPSHOT-jar-with-dependencies.jar {0} {1} {2} {3} {4} {5}"
ADDITIONAL_INFO = ['changeList', 'commitDate']

def get_commit_log(project_root, path_to_source, method_name, begin_line, end_line, **kwargs):
    outfile = os.path.join(project_root,
                           f"tracker-{path_to_source.split('.')[0].replace('/','_')}-{method_name}-{begin_line}.json")
    commit_log_cmd = COMMIT_LOG_CMD.format(project_root, path_to_source, kwargs["start_commit"],
                                           method_name, begin_line, outfile)
    print(commit_log_cmd)
    os.system(commit_log_cmd)
    with open(outfile, "r") as f:
        result = json.load(f)
    commits = []
    for commit in reversed(result):
        commits.append((
            commit["commitId"],
            commit["elementBeforeFilePath"],
            commit["elementAfterFilePath"],
            {k: commit[k] for k in ADDITIONAL_INFO}))
    return commits
