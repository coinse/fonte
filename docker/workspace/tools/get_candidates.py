import argparse
import pandas as pd

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('pkl', type=str)
  parser.add_argument('--output', '-o', type=str)
  parser.add_argument('--depth', '-d', type=int, default=None)
  args = parser.parse_args()

  df = pd.read_pickle(args.pkl)
  if args.depth is not None:
    df = df[df.rev_index < args.depth]
  candidates = df.commit_hash.unique().tolist()
  candidates = [sha[:7] for sha in candidates]

  if args.output:
    with open(args.output, 'w') as f:
      f.write("\n".join(candidates))
  else:
    for c in candidates:
      print(c)