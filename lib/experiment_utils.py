import os
import numpy as np
import pandas as pd
from sbfl.base import SBFL

def load_BIC_GT(dataset_dir):
    def load_BIC_data(filename):
        df = pd.read_csv(os.path.join(dataset_dir, filename), header=0)
        df["vid"] = df["vid"].astype(str)
        df["commit"] = df["commit"].apply(lambda s: str(s)[:7])
        return df

    Wen_GT = load_BIC_data(
        "wen19-defects4j-bug-inducing-commits.csv")
    # print("Wen (Original)", len(Wen_GT))
    excluded_from_Wen = load_BIC_data(
        "excluded-from-Wen.csv"
    )[["pid", "vid"]].to_records(index=False).tolist()
    to_exclude = Wen_GT.apply(lambda row:
        (row.pid, row.vid) in excluded_from_Wen, axis=1)
    Wen_GT = Wen_GT[~to_exclude]
    # print("Wen (Filtered)", len(Wen_GT))

    manual_GT = load_BIC_data(
        "manual-defects4j-bug-inducing-commits.csv").drop_duplicates()
    # print("Manual", len(manual_GT))

    # Check for the overlapped data points
    overlap_counts = 0
    for _, row in Wen_GT.iterrows():
        cor_row = manual_GT[
            (manual_GT.pid == row.pid) & (manual_GT.vid == row.vid)]
        if cor_row.shape[0] > 0:
            found_by_Wen = row.commit
            found_manually =  cor_row.commit.values[0]
            assert found_by_Wen == found_manually
            overlap_counts += 1

    GT = pd.concat([Wen_GT, manual_GT])
    GT = GT.drop_duplicates()
    assert GT[["pid", "vid"]].drop_duplicates().shape[0] == GT.shape[0]
    print(f"The BIC data is available for {len(GT)} faults. ({len(Wen_GT)} Wen + {len(manual_GT)} Manual - {overlap_counts} Overlapped)")

    GT.groupby(["pid"]).count()["vid"]
    GT.sort_values(by=["pid", "vid"], inplace=True)

    GT = GT.set_index(["pid", "vid"])
    Wen_GT = Wen_GT.set_index(["pid", "vid"])
    manual_GT = manual_GT.set_index(["pid", "vid"])

    GT["provenance"] = ""
    GT.loc[Wen_GT.index, "provenance"] += "Wen+"
    GT.loc[manual_GT.index, "provenance"] += "Manual"
    GT["provenance"] = GT["provenance"].apply(
        lambda s: s[:-1] if s[-1:] == "+" else s)
    GT = GT.reset_index()
    
    savepath = os.path.join(dataset_dir, "combined.csv")
    GT.to_csv(savepath, index=False)
    print("The combined GT data is saved to", savepath)
    return GT

def get_sbfl_scores_from_coverage(path_to_coverage, formula="Ochiai",
    covered_by_failure_only=True, in_class_only=False, use_cache=True,
    return_coverage_matrix=False):
    assert not (use_cache and return_coverage_matrix)
    savedir = os.path.join(os.path.dirname(path_to_coverage), "sbfl")
    postfix = "suspicious" if covered_by_failure_only else "all"
    postfix += "_inClassOnly" if in_class_only else ""
    savepath = os.path.join(savedir, f"{formula}_{postfix}.pkl")
    if use_cache and os.path.exists(savepath):
        sbfl_df = pd.read_pickle(savepath)
    else:
        if in_class_only:
            # only use the test cases that are in the class containing
            # at least one failing test case
            new_path_to_coverage = path_to_coverage.replace(
                ".pkl", ".in_class_only.pkl")

            if os.path.exists(new_path_to_coverage):
                cov_df = pd.read_pickle(new_path_to_coverage)
            else:
                cov_df = pd.read_pickle(path_to_coverage)

                failing_tests = cov_df.index[~cov_df["result"]]
                failing_test_classes = set(
                    [t.split("::")[0] for t in failing_tests])
                in_class = np.array([
                    t.split("::")[0] in failing_test_classes for t in cov_df.index])
                cov_df = cov_df.loc[in_class]
                cov_df.to_pickle(new_path_to_coverage)
        else:
            cov_df = pd.read_pickle(path_to_coverage)
        is_passing = cov_df["result"].values.astype(bool) # test results
        cov_df.drop("result", axis=1, inplace=True)

        if covered_by_failure_only:
            cov_df = cov_df.loc[:, cov_df.loc[~is_passing].any(axis=0)]
        sbfl = SBFL(formula=formula)
        sbfl.fit(cov_df.values, is_passing)
        sbfl_df = sbfl.to_frame(elements=cov_df.columns,
                names=["class_file", "method_name", "method_signature", "line"])
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        sbfl_df.to_pickle(savepath)
    if return_coverage_matrix:
        return sbfl_df, cov_df
    else:
        return sbfl_df

def get_all_commits(fault_dir):
    with open(os.path.join(fault_dir, "commits.log"), "r") as f:
        return list(map(lambda hash: hash[:7], f.read().strip().split('\n')))

def get_the_number_of_total_commits(fault_dir):
    return len(get_all_commits(fault_dir))

def load_commit_history(fault_dir, tool):
    com_df = pd.read_pickle(os.path.join(fault_dir, tool, "commits.pkl"))
    if "class_file" not in com_df.columns:
        with open(os.path.join(fault_dir, "src_dir"), "r") as f:
            src_dir = f.read().strip()
            if src_dir[-1] != "/":
                src_dir += "/"
        com_df["class_file"] = com_df["src_path"].apply(
            lambda s: s[len(src_dir):]
        )
    com_df["commit_hash"] = com_df["commit_hash"].apply(lambda s: str(s)[:7])
    return com_df

def get_style_change_commits(fault_dir, tool, with_Rewrite=True):
    postfix = "" if with_Rewrite else "_noOpenRewrite"
    val_df = pd.read_csv(
        os.path.join(fault_dir, tool, f"validation{postfix}.csv"), 
        header=None,
        names=["commit", "src_path", "AST_diff"])

    val_df["unchanged"] = val_df["AST_diff"] == "U"
    agg_df = val_df.groupby("commit").all()[["unchanged"]]
    return agg_df.index[agg_df["unchanged"]].tolist()

def vote_for_commits(fault_dir, tool, formula, decay, voting_func,
    use_method_level_score=False, excluded=[], adjust_depth=True,
    in_class_only=False):
    commit_df = load_commit_history(fault_dir, tool)

    commit_df["excluded"] = commit_df["commit_hash"].isin(excluded)
    commit_df["new_depth"] = commit_df["depth"]

    if len(excluded) > 0 and adjust_depth:
        # update commit depth
        commit_df.loc[commit_df.excluded, "new_depth"] = None
        commit_df["method_identifier"] = commit_df.class_file + ":" + \
            commit_df.method_name + commit_df.method_signature + \
            ":L" + commit_df.begin_line.astype(str) + "," + commit_df.end_line.astype(str)
        for _, row in commit_df[commit_df.excluded].iterrows():
            # print(row)
            affected = (commit_df.method_identifier == row.method_identifier)\
                & (commit_df.depth > row.depth)
            commit_df.loc[affected, "new_depth"] = commit_df.loc[affected, "new_depth"] - 1

    sbfl_df = get_sbfl_scores_from_coverage(
        os.path.join(fault_dir, "coverage.pkl"),
        formula=formula,
        covered_by_failure_only=True,
        in_class_only=in_class_only)

    if use_method_level_score:
        identifier = ["class_file", "method_name", "method_signature","begin_line", "end_line"]
        l_sbfl_df = sbfl_df.reset_index()
        l_sbfl_df["dense_rank"] = (-l_sbfl_df["score"]).rank(method="dense")
        l_sbfl_df["max_rank"] = (-l_sbfl_df["score"]).rank(method="max")

        l_sbfl_df["score"] = l_sbfl_df.apply(voting_func, axis=1)

        method_sbfl_rows = []
        for _, method in commit_df[identifier].drop_duplicates().iterrows():
            method_score = l_sbfl_df[
                (l_sbfl_df.class_file == method.class_file)
                # & (l_sbfl_df.method_name == method.method_name)
                # & (l_sbfl_df.method_signature == method.method_signature)   
                & (l_sbfl_df.line >= method.begin_line)
                & (l_sbfl_df.line <= method.end_line)
            ].score.sum()
            method_sbfl_rows.append([
                method.class_file, method.method_name, method.method_signature,
                method.begin_line, method.end_line, method_score
            ])
        sbfl_df = pd.DataFrame(method_sbfl_rows,columns=identifier+["score"])
        sbfl_df = sbfl_df.set_index(identifier)

    sbfl_df["dense_rank"] = (-sbfl_df["score"]).rank(method="dense")
    sbfl_df["max_rank"] = (-sbfl_df["score"]).rank(method="max")
    vote_rows = []
    for _, row in sbfl_df.reset_index().iterrows():
        vote = voting_func(row)
        if use_method_level_score:
            com_df = commit_df[
                (commit_df.class_file == row.class_file) \
                & (commit_df.method_name == row.method_name) \
                & (commit_df.method_signature == row.method_signature)
            ]
        else:
            com_df = commit_df[
                (commit_df.class_file == row.class_file) \
                & (commit_df.begin_line <= row.line) \
                & (commit_df.end_line >= row.line)
            ]
        for commit, depth in zip(com_df.commit_hash, com_df.new_depth):
            if commit in excluded:
                decayed_vote = 0
            else:
                decayed_vote = vote * ((1-decay) ** depth)
            vote_rows.append([commit, decayed_vote])
    vote_df = pd.DataFrame(data=vote_rows, columns=["commit", "vote"])
    agg_vote_df = vote_df.groupby("commit").sum("vote")
    agg_vote_df.sort_values(by="vote", ascending=False, inplace=True)
    return agg_vote_df

def max_aggr_for_commits(fault_dir, tool, formula,
    use_method_level_score=False, excluded=[]):
    commit_df = load_commit_history(fault_dir, tool)

    sbfl_df = get_sbfl_scores_from_coverage(
        os.path.join(fault_dir, "coverage.pkl"),
        formula=formula,
        covered_by_failure_only=True)

    if use_method_level_score:
        identifier = ["class_file", "method_name", "method_signature","begin_line", "end_line"]
        l_sbfl_df = sbfl_df.reset_index()
        method_sbfl_rows = []
        for _, method in commit_df[identifier].drop_duplicates().iterrows():
            method_score = l_sbfl_df[
                (l_sbfl_df.class_file == method.class_file)
                & (l_sbfl_df.line >= method.begin_line)
                & (l_sbfl_df.line <= method.end_line)
            ].score.max()
            method_sbfl_rows.append([
                method.class_file, method.method_name, method.method_signature,
                method.begin_line, method.end_line, method_score
            ])
        sbfl_df = pd.DataFrame(method_sbfl_rows,columns=identifier+["score"])
        sbfl_df = sbfl_df.set_index(identifier)

    vote_rows = []
    for _, row in sbfl_df.reset_index().iterrows():
        vote = row.score
        if use_method_level_score:
            com_df = commit_df[
                (commit_df.class_file == row.class_file) \
                & (commit_df.method_name == row.method_name) \
                & (commit_df.method_signature == row.method_signature)
                & (commit_df.begin_line == row.begin_line) \
                & (commit_df.end_line == row.end_line)
            ]
        else:
            com_df = commit_df[
                (commit_df.class_file == row.class_file) \
                & (commit_df.begin_line <= row.line) \
                & (commit_df.end_line >= row.line)
            ]

        for commit in com_df.commit_hash.unique():
            vote_rows.append([commit, vote if commit not in excluded else 0])
    vote_df = pd.DataFrame(data=vote_rows, columns=["commit", "vote"])
    agg_vote_df = vote_df.groupby("commit").max("vote")
    agg_vote_df.loc[agg_vote_df.vote.isna(), "vote"] = .0
    agg_vote_df.sort_values(by="vote", ascending=False, inplace=True)
    return agg_vote_df

def standard_bisection(commits: list, BIC, verbose=False, return_pivots=False):
    assert BIC in commits
    # pre-condition: commit[i] is newer than commit[i+1]
    # return: the number of required iterations until the BIC is found

    BIC_index = commits.index(BIC)
    bad_index = 0
    good_index = len(commits)
    num_iterations = 0
    if return_pivots:
        pivots = []
    while good_index > bad_index + 1:
        num_iterations += 1
        pivot_index = int((bad_index + good_index)/2)
        if verbose:
            print(f"Test {pivot_index}")
        if return_pivots:
            pivots.append(pivot_index)
        if pivot_index > BIC_index:
            good_index = pivot_index
        elif pivot_index <= BIC_index:
            bad_index = pivot_index
    assert bad_index == BIC_index
    if return_pivots:
        return num_iterations, pivots
    else:
        return num_iterations

def weighted_bisection(commits: list, scores: list, BIC, verbose=False,
    return_pivots=False):
    assert BIC in commits
    assert len(commits) == len(scores)
    # pre-condition: commit[i] is newer than commit[i+1]
    # pre-condition: score[i] is the score of commit[i]
    # return: the number of required iterations until the BIC is found
    commits = [c for c, s in zip(commits, scores) if s > 0]
    scores = [s for s in scores if s > 0]
    BIC_index = commits.index(BIC)
    bad_index = 0
    good_index = len(commits)
    num_iterations = 0
    if return_pivots:
        pivots = []
    while good_index > bad_index + 1:
        num_iterations += 1
        """
        original implementation
        """
        min_diff, pivot_index = None, None
        for i in range(bad_index + 1, good_index):
            abs_diff = abs(
                sum(scores[bad_index:i]) - sum(scores[i:good_index]))
            if min_diff is None or min_diff > abs_diff:
                min_diff = abs_diff
                pivot_index = i
            else:
                # already pass the min, now increasing
                break
        if verbose:
            print(f"Test {pivot_index}")
        if return_pivots:
            pivots.append(pivot_index)
        if pivot_index > BIC_index:
            good_index = pivot_index
        elif pivot_index <= BIC_index:
            bad_index = pivot_index
    assert bad_index == BIC_index
    if return_pivots:
        return num_iterations, pivots
    else:
        return num_iterations
