import os
import json
import numpy as np
import pandas as pd
from spiral import ronin
from rank_bm25 import BM25Okapi
from collections import Counter
from scipy.spatial.distance import cosine
from lib.experiment_utils import *

CORE_DATA_DIR = "./data/Defects4J/core"
BIC_GT_DIR = "./data/Defects4J/BIC_dataset"
BASELINE_DATA_DIR = "./data/Defects4J/baseline"

def tokenize(text):
    return ronin.split(text)

def vectorize_complex(bm25, features):
    vectors = []
    for feature in features:
        tokenize_feature = tokenize(feature)
        doc_len = len(tokenize_feature)
        doc = Counter(tokenize_feature)
        vector = []
        for v in bm25.vocab:
            freq = doc.get(v, 0)
            vector.append(bm25.idf.get(v, 0) * (freq * (bm25.k1 + 1) /
                (freq + bm25.k1 * (1 - bm25.b + bm25.b * doc_len / bm25.avgdl))))
        vectors.append(vector)
    assert len(vectors) == len(features)
    assert len(vectors[0]) == len(bm25.vocab)
    vectors = np.array(vectors)
    return vectors.mean(axis=0)

def run_bug2commit(pid, vid):
    core_data_dir = os.path.join(CORE_DATA_DIR, f"{pid}-{vid}b")
    baseline_data_dir = os.path.join(BASELINE_DATA_DIR, f"{pid}-{vid}b")
    commit_dir = os.path.join(baseline_data_dir, "commits")
    
    savepath = os.path.join(baseline_data_dir, "ranking_Bug2Commit.csv")
    if os.path.exists(savepath):
        print(f"{pid}-{vid}b: {savepath} already exists")
        return

    print(f"{pid}-{vid}b: Collecting commit features..........................")
    # get doc (commit) features
    commit_features = {}
    for filename in os.listdir(commit_dir):
        with open(os.path.join(commit_dir, filename), "r") as f:
            data = json.load(f)
            commit_message = data["log"].strip() # 1st commit feature
            modified_files = "\n".join(list(set([  # 2nd commit feature
                l[6:]
                for l in data["commit"].strip().split("\n")
                if l.startswith("+++ ")
            ])))
            commit_features[filename] = [commit_message, modified_files]

    print(f"{pid}-{vid}b: Collecting query features...........................")
    # get query (bug report) features
    query_features = []
    with open(os.path.join(baseline_data_dir, "br_long.txt"), "r") as f:
        query_features.append(f.read().strip()) # 1st bug report feature
    with open(os.path.join(baseline_data_dir, "br_short.txt"), "r") as f:
        query_features.append(f.read().strip()) # 2nd bug report feature
    with open(os.path.join(core_data_dir, "failing_tests"), "r") as f:
        query_features.append(f.read().strip()) # 3rd bug report feature

    corpus = sum(commit_features.values(), [])
    tokenized_corpus = [tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25.vocab = list(set( # collect all words appearning in the corpus
        sum([list(doc.keys()) for doc in bm25.doc_freqs], [])))

    print(f"{pid}-{vid}b: Vectorizing the features............................")

    # vectorize the features (using the vector_complex)
    commit_vectors = {
        filename: vectorize_complex(bm25, commit_features[filename])
        for filename in commit_features
    }
    query_vector = vectorize_complex(bm25, query_features)

    print(f"{pid}-{vid}b: Calculating the scores of commits...................")

    score_rows = []
    for filename in commit_vectors:
        commit = filename[2:9]
        similarity = 1 - cosine(commit_vectors[filename], query_vector)
        score_rows.append([commit, filename, similarity])

    score_df = pd.DataFrame(data=score_rows,
        columns=["commit", "filename", "score"])
    score_df["rank"] = score_df["score"].rank(ascending=False, method="max")
    score_df["rank"] = score_df["rank"].astype(int)
    score_df.sort_values(by="rank", inplace=True)
    score_df = score_df[["commit", "filename", "rank", "score"]]
    if savepath:
        score_df.to_csv(savepath, index=False, header=None)
        print(f"{pid}-{vid}b: Saved to {savepath}")
    return score_df

if __name__ == "__main__":
    GT = load_BIC_GT(BIC_GT_DIR)
    for _, row in GT.iterrows():
        pid, vid = row.pid, row.vid
        score_df = run_bug2commit(pid, vid)