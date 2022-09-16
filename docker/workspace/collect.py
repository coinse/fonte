import argparse
import os
import logging
import numpy as np
import pandas as pd
from collect_utils.defects4j import D4JBug
from collect_utils.javaparser import NodeRanges
import collect_utils.git as git
import collect_utils.shovel as shovel

class NodeInfo:
  def __init__(self, class_file, rel_src_path, method_name, method_signature, begin_line, end_line, commit_log):
    self.class_file = class_file
    self.rel_src_path = rel_src_path
    self.method_name = method_name
    self.method_signature = method_signature
    self.begin_line, self.end_line = begin_line, end_line
    self.commit_log = commit_log
    self.scores = dict()

def rank_BIC(bug, path_to_coverage, formula='ochiai', commit_history_retriever='git'):
  if commit_history_retriever == 'git':
    log_retriever = git
  elif commit_history_retriever == 'shovel':
    log_retriever = shovel
  else:
    raise Exception(f"Unsupported commit history retriever: {commit_history_retriever}")

  coverage_matrix = bug.get_coverage_matrix(
    path_to_coverage=path_to_coverage,
    test_types=['failings', 'passings']
  )

  logging.info(f"Loaded {coverage_matrix}")
  logging.info(f"The number of total commits: {len(bug.commits)}")

  ranges_cache = dict()
  node_infos = dict()

  suspiciousness_scores = coverage_matrix.sbfl(formula=formula)
  for score, component in zip(suspiciousness_scores, coverage_matrix.components):
    if score == 0.0:
      continue
    class_file, method_name, method_signature, lineno = component
    rel_src_path = os.path.join(bug.src_dir, class_file)
    abs_src_path = os.path.join(bug.project_root, rel_src_path)

    """
    Get the range parsing information
    """
    if rel_src_path not in ranges_cache:
      ranges_cache[rel_src_path] = NodeRanges(abs_src_path)
    node_ranges = ranges_cache[rel_src_path]

    """
    Get the range of the current node
    """
    node_range = node_ranges.get_range(lineno)
    if node_range:
      begin_line, end_line = node_range.begin_line, node_range.end_line
    else:
      begin_line, end_line = lineno, lineno

    """
    Create Node Info
    """
    node_key = (rel_src_path, begin_line, end_line)
    if node_key not in node_infos:
      use_git_log = False
      if not node_range or node_range.node_type != 'method':
        use_git_log = True
      else:
        try:
          commit_log = log_retriever.get_commit_log(bug.project_root,
            rel_src_path, method_name,
            node_range.name_begin_line if log_retriever == shovel else begin_line, end_line)
        except Exception as e:
          print(e)
          use_git_log = True

      if use_git_log:
        commit_log = git.get_commit_log(bug.project_root,
          rel_src_path, method_name, begin_line, end_line)

      node_infos[node_key] = NodeInfo(class_file, rel_src_path, method_name,
        method_signature, begin_line, end_line, commit_log)

    """
    Save the suspiciousness score
    """
    node_infos[node_key].scores[lineno] = score


  """
  Create dataframe
  """
  commit_rows = []
  for node_key in node_infos:
    node = node_infos[node_key]
    for depth, commit_info in enumerate(node.commit_log):
      commit_hash, before_path, after_path, additional_info = commit_info
      from_head = bug.commits.index(commit_hash)
      commit_rows.append([node.class_file, node.rel_src_path, node.method_name, node.
        method_signature, node.begin_line, node.end_line, depth, commit_hash,
        from_head, before_path, after_path] + [additional_info.get(key, None) for key in log_retriever.ADDITIONAL_INFO])

  commit_df = pd.DataFrame(data=commit_rows, columns=['class_file',
    'src_path', 'method_name', 'method_signature', 'begin_line',
    'end_line', 'depth', 'commit_hash', 'from_head', 'before_src_path',
    'after_src_path'] + log_retriever.ADDITIONAL_INFO)

  BIC_candidates = set(commit_df.commit_hash.unique())
  logging.info(f"The number of BIC candidates: {len(BIC_candidates)}")
  return commit_df

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('project_root', type=str)
  parser.add_argument('--formula', '-f', type=str, default='ochiai')
  parser.add_argument('--log-retriever', '-l', type=str, default='git')
  parser.add_argument('--verbose', '-v', action='store_true')
  parser.add_argument('--output_dir', '-o', type=str)
  args = parser.parse_args()

  output_dir = args.output_dir

  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  if not os.path.exists(args.project_root):
    exit(1)

  bug = D4JBug(args.project_root)

  # setup logging configuration
  logging.basicConfig(
    level=logging.DEBUG if args.verbose else logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    handlers=[
      logging.FileHandler(
        os.path.join(output_dir, args.log_retriever, "log"), mode='w'),
      logging.StreamHandler()
  ])

  logging.info(f"Search BICs for {args.project_root}")
  commit_df = rank_BIC(bug,
    path_to_coverage=os.path.join(output_dir, "coverage.pkl"),
    formula=args.formula,
    commit_history_retriever=args.log_retriever
  )
  commit_df.to_pickle(
    os.path.join(output_dir, args.log_retriever, "commits.pkl"))

