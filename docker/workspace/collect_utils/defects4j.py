import os
import logging
import numpy as np
from .coverage import CoverageMatrix, parse_cobertura_output

class NoCoverageDirException(Exception):
  pass

class D4JBug:
  D4J_CONFIG = '.defects4j.config'
  SRC_DIR_INFO = 'dir.src.classes'
  COMMIT_LOG_INFO = 'commits.log'

  def __init__(self, project_root):
    self.project_root = project_root

    config_file = os.path.join(project_root, self.D4J_CONFIG)
    assert os.path.exists(config_file)

    with open(config_file, 'r') as f:
      f.readline()
      self.pid = f.readline().strip().split('=')[1]
      self.vid = f.readline().strip().split('=')[1][:-1]

    self._srcdir = None
    self._commits = None

  def __str__(self):
    return f"{self.pid}-{self.vid}b ({self.project_root})"

  @property
  def src_dir(self):
    if self._srcdir is None:
      with open(os.path.join(self.project_root, self.SRC_DIR_INFO), 'r') as f:
        # Source directory of classes (relative to working directory)
        self._srcdir = f.read().strip()
        if self.pid == "Time" and int(self.vid) > 20:
            self._srcdir = "JodaTime/" + self._srcdir
    return self._srcdir

  @property
  def commits(self):
    if self._commits is None:
      with open(os.path.join(self.project_root, self.COMMIT_LOG_INFO), 'r') as f:
        # Commits stored in reverse chronological order
        self._commits = [l.strip() for l in f.readlines()]
    return self._commits

  def get_coverage_matrix(self, path_to_coverage=None,
    test_types=['failings', 'passings']):

    coverage_available = path_to_coverage and os.path.exists(path_to_coverage)

    valid_test_types = {
      'failings': 0,
      'passings': 1
    }

    if coverage_available:
      coverage_matrix = CoverageMatrix.read_pickle(path_to_coverage)
    else:
      if not os.path.exists(os.path.join(self.project_root, 'coverage_xmls')):
        raise NoCoverageDirException

      components = []
      test_coverage = {}
      test_results = {}

      for test_type in test_types:
        coverage_dir = os.path.join(self.project_root, 'coverage_xmls', test_type)
        for coverage_file in os.listdir(coverage_dir):
          if coverage_file[-4:] != '.xml':
            continue
          # for all .xml files in the coverage directory
          test_name = coverage_file[:-4]
          logging.debug(f"Reading the coverage of {test_name} ({test_type})")
          # hits {component: hit}
          hits = parse_cobertura_output(os.path.join(coverage_dir, coverage_file))
          assert test_name not in test_coverage
          test_coverage[test_name] = set()
          for comp in hits:
            if hits[comp] > 0:
              # if 'comp' is an unseen component, add it to 'components'
              if comp not in components:
                components.append(comp)
              comp_index = components.index(comp)
              test_coverage[test_name].add(comp_index)
          test_results[test_name] = valid_test_types[test_type]

      tests = list(sorted(test_coverage.keys()))
      X = np.zeros((len(tests), len(components)), dtype=bool)
      for i, test_name in enumerate(tests):
        for j in test_coverage[test_name]:
          X[i, j] = True

      y = np.array([test_results[test_name] for test_name in tests], dtype=bool)
      coverage_matrix = CoverageMatrix(X, y, tests, components)

      if path_to_coverage:
        coverage_matrix.to_sparse_df().to_pickle(path_to_coverage)

    return coverage_matrix
