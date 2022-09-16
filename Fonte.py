import argparse
from lib.experiment_utils import *

voting_functions = {
    # key: (alpha, tau)
    (1, 'max'): (lambda r: r.score/r.max_rank),
    (0, 'max'): (lambda r: 1/r.max_rank),
    (1, 'dense'): (lambda r: r.score/r.dense_rank),
    (0, 'dense'): (lambda r: 1/r.dense_rank),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute commit scores")
    parser.add_argument('coredir', help="data/Defects4J/core/<pid>-<vid>b")
    parser.add_argument('--tool', type=str, default="git",
        help="history retrieval tool, git or shovel (default: git)")
    parser.add_argument('--formula', type=str, default="Ochiai",
        help="SBFL formula (default: Ochiai)")
    parser.add_argument('--alpha', type=int, default=0,
        help="alpha (default: 0)")
    parser.add_argument('--tau', type=str, default="max",
        help="tau (default: max)")
    parser.add_argument('--lamb', type=float, default=0.1,
        help="lambda (default: 0.1)")
    parser.add_argument('--skip-stage-2', action="store_true",
        help="skip stage 2 (default: False)")
    parser.add_argument('--output', '-o',
        help="path to output file (example: output.csv)")
    args = parser.parse_args()

    assert args.alpha in [0, 1]
    assert args.tau in ["max", "dense"]
    assert 0 <= args.lamb < 1

    print(f"Number of total commits: {get_the_number_of_total_commits(args.coredir)}")
    if args.skip_stage_2:
        style_change_commits = []
    else:
        style_change_commits = get_style_change_commits(
            args.coredir, args.tool, with_Rewrite=True)

    vote_df = vote_for_commits(args.coredir, args.tool, args.formula,
        args.lamb, voting_functions[(args.alpha, args.tau)],
        use_method_level_score=False,
        excluded=style_change_commits, adjust_depth=True)

    vote_df["rank"] = (-vote_df["vote"]).rank(method="max")
    vote_df["is_style_change"] = vote_df.index.isin(style_change_commits)

    print(vote_df)
    if args.output:
        vote_df.to_csv(args.output)
        print(f"Saved to {args.output}")
