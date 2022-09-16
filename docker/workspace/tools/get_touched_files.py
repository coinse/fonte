import pandas as pd
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('commit_path', type=str)
  parser.add_argument('--commit', '-c', type=str)
  parser.add_argument('--output', '-o', type=str)
  args = parser.parse_args()
  df = pd.read_pickle(args.commit_path)
  if args.commit:
    touched = df['commit_hash'].apply(
      lambda sha: sha.startswith(args.commit)
    )
    df = df[touched]

  files = df.after_src_path.unique().tolist()
  
  if args.output:
    with open(args.output, 'w') as f:
      f.write('\n'.join(files))
  else:
    for f in files:
      print(f)