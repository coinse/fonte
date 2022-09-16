import os

JAVA_ANALYZER = "/root/workspace/tools/java_analyzer/target/java-analyzer-1.0-SNAPSHOT-shaded.jar"

class NodeRange:
  def __init__(self, name, begin_line, end_line, name_begin_line, node_type=None):
    self.name = name
    self.begin_line = begin_line
    self.end_line = end_line
    self.name_begin_line = name_begin_line
    self.node_type = node_type

  def __str__(self):
    return f"{self.begin_line}:{self.end_line}"

class NodeRanges:
  def __init__(self, path_to_source, separator='|'):
    self.ranges = {}
    source_root = os.path.dirname(path_to_source)
    file_name = os.path.basename(path_to_source)

    max_lineno = -1
    with os.popen(f"java -cp {JAVA_ANALYZER} analyzer.MethodRangeAnalyzer {source_root} {file_name}") as f:
      for l in f:
        if l.startswith("method" + separator) or l.startswith("constructor" + separator) or l.startswith("field" + separator):
          node_type = l.split(separator)[0]
          signature, begin_line, end_line, name_begin_line = tuple(l.strip().split(separator)[1:])
          begin_line, end_line, name_begin_line = int(begin_line), int(end_line), int(name_begin_line)
          signature = signature + "@" + str(begin_line)
          self.ranges[signature] = NodeRange(signature, begin_line, end_line, name_begin_line, node_type)
          if end_line > max_lineno:
            max_lineno = end_line

    self.nodes = list(self.ranges)

    self.lookup_helper = [None] * (max_lineno + 1)
    for node_index, signature in enumerate(self.nodes):
      node_range = self.ranges[signature]
      for lineno in range(node_range.begin_line, node_range.end_line + 1):
        self.lookup_helper[lineno] = node_index

  def get_range(self, lineno):
    if lineno < len(self.lookup_helper):
      node_index = self.lookup_helper[lineno]
      if node_index is not None:
        signature = self.nodes[node_index]
        return self.ranges[signature]
    return None
