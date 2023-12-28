import os
import re
import subprocess

COMMIT_LOG_CMD = 'git log -M -C -L {0},{1}:{2}'
ADDITIONAL_INFO = []

def parse_git_log(s):
    lines = s.split('\n')
    commits = []
    for line in lines:
        m = re.match("commit (\w{40})", line)
        if m:
            sha = m.group(1)
            commits.append({'sha': sha, 'before':None, 'after':None})
        elif line.startswith('Date:') and "commitDate" not in commits[-1]:
            commits[-1]['commitDate'] = line.lstrip("Date:").strip()
        elif line.startswith('Author:') and "commitAuthor" not in commits[-1]:
            commits[-1]['commitAuthor'] = line.lstrip("Author:").strip()
        elif line.startswith('--- '):
            path = line[4:]
            if path.startswith("a/"):
                path = path[2:]
            assert commits[-1]['before'] is None
            commits[-1]['before'] = path
        elif line.startswith('+++ '):
            path = line[4:]
            if path.startswith("b/"):
                path = path[2:]
            assert commits[-1]['after'] is None
            commits[-1]['after'] = path
    return [
      (item['sha'], item['before'], item['after'], {})
      for item in commits
      if item['before'] and item['after']
    ]

def get_commit_log(project_root, path_to_source, method_name, begin_line, end_line, **kwargs):
    commit_log_cmd = COMMIT_LOG_CMD.format(begin_line, end_line, path_to_source)
    cmd = f"cd {project_root}; {commit_log_cmd} | grep -e '^commit' -e 'diff --git' -A 3"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    try:
        commits = parse_git_log(stdout.decode('utf-8'))
    except UnicodeDecodeError as e:
        print(cmd)
        raise e
    return commits
