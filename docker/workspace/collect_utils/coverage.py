import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET

def parse_cobertura_output(cov_file_path):
  # cobertura output parser
  tree = ET.parse(cov_file_path)
  root = tree.getroot()
  hits = {}
  packages = root[1]
  for package in packages:
    for classes in package:
      for _class in classes:
        class_name = _class.attrib['name']
        class_file_name = _class.attrib['filename']
        methods = _class.find('methods')
        for method in _class[0]: #FIXME
        # for method in methods:
          method_name = method.attrib['name']
          method_signature = method.attrib['signature']
          line_rate = float(method.attrib['line-rate'])
          if line_rate == 0:
            # skip if there is no covered lines in this method
            continue
          lines = method.find('lines')
          for line in method[0]: #FIXME
          # for line in lines:
            hit_count = int(line.attrib['hits'])
            if hit_count == 0:
              # skip if this line is not covered
              continue
            lineno = int(line.attrib['number'])
            hits[(class_file_name, method_name, method_signature, lineno)] = hit_count
  return hits

class CoverageMatrix:
  def __init__(self, X, y, tests, components):
    assert X.shape[0] == len(tests)
    assert X.shape[1] == len(components)
    assert y.shape[0] == len(tests)

    self.X = X
    self.y = y
    self.tests = tests
    self.components = components

  def __str__(self):
    return f"{self.X.shape[0]}x{self.X.shape[1]} Coverage Matrix"

  def to_sparse_df(self):
    from scipy.sparse import csr_matrix

    cov = pd.DataFrame.sparse.from_spmatrix(csr_matrix(self.X),
      index=self.tests, columns=self.components)
    cov['result'] = self.y

    return cov

  @property
  def failing_tests(self):
    return np.array(self.tests)[self.y == 0].tolist()

  def sbfl(self, formula='ochiai'):
    e_p = self.X[self.y == 1].sum(axis=0)
    e_f = self.X[self.y == 0].sum(axis=0)
    n_p = (~self.X[self.y == 1]).sum(axis=0)
    n_f = (~self.X[self.y == 0]).sum(axis=0)
    if formula == 'ochiai':
      return e_f/np.sqrt((e_f + n_f) * (e_f + e_p))
    else:
      raise Exception(f"Formula {formula} not avaiable")

  def get_tests_cover(self, component):
    return np.array(self.tests)[self.X[:, self.components.index(component)]].tolist()

  def get_components_covered_by(self, test):
    return np.array(self.components)[self.X[self.tests.index(test)]].tolist()

  def is_covered_by_tests(self, component, only_failing=False):
    if only_failing:
      mat = self.X[self.y == 0]
    else:
      mat = self.X

    return np.any(mat[:, self.components.index(component)])

  @classmethod
  def read_pickle(cls, path_to_coverage):
    df = pd.read_pickle(path_to_coverage)
    y = df['result'].values
    df.drop(columns=['result'], inplace=True)
    X = df.values
    tests = df.index.values.tolist()
    components = df.columns.values.tolist()
    return cls(X, y, tests, components)
