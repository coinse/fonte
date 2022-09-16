import time
import os
import json

COMMIT_LOG_CMD = "java -Xmx2g -jar /root/workspace/tools/codeshovel-1.0.0-SNAPSHOT.jar -repopath {0} -filepath {1} -methodname {2} -startline {3} -outfile {4}"
ADDITIONAL_INFO = ['commitDate', 'commitAuthor', 'type']

def get_commit_log(project_root, path_to_source, method_name, begin_line, end_line):
  timestamp = str(time.time()).replace(".", "_")
  outfile = os.path.join(project_root, f"shovel-{path_to_source.split('.')[0].replace('/','_')}-{method_name}-{begin_line}.json")
  commit_log_cmd = COMMIT_LOG_CMD.format(project_root, path_to_source,
    method_name, begin_line, outfile)
  print(commit_log_cmd)
  os.system(commit_log_cmd)
  with open(outfile, "r") as f:
    result = json.load(f)
  commits = []
  for commit in result["changeHistoryDetails"]:
    details = result["changeHistoryDetails"][commit]
    paths = set()
    old_paths = set()
    if "Ymultichange" in details["type"]:
      detail_set = details["subchanges"]
    else:
      detail_set = [details]
    for item in detail_set:
      paths.add(item["path"])
      if "extendedDetails" in item:
        if "oldPath" in item["extendedDetails"]:
          old_paths.add(item["extendedDetails"]["oldPath"])
      elif "Yintroduce" == item["type"]:
        old_paths.add("/dev/null")
    assert len(paths) == 1
    if len(old_paths) == 0:
      old_paths = paths
    assert len(old_paths) == 1
    before_src_path = list(old_paths)[0]
    after_src_path = list(paths)[0]
    commits.append((commit, before_src_path, after_src_path, {
      k: details[k] for k in ADDITIONAL_INFO}))
  return commits
