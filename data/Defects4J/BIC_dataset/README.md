# BIC Dataset
1. [./Wen19-defects4j-bug-inducing-commits.csv](./wen19-defects4j-bug-inducing-commits.csv)
  - Source: [**InduceBenchmark**](https://github.com/justinwm/InduceBenchmark/blob/master/Defects4J.csv) (Exploring and Exploiting the Correlations between Bug-Inducing and Bug-Fixing Commits, Wen et al. 2019)
  -  [./excluded-from-Wen.csv](./excluded-from-Wen.csv)
    - We excluded 24 data points from this BIC dataset. This file contains the reason for the exclusion for each data point.
2. [./manual-defects4j-bug-inducing-commits.csv](./manual-defects4j-bug-inducing-commits.csv)
  - Manually identified by authors referring to the bug reports, symptoms, developer patch, and commit history.
3. [./combined.csv](./combined.csv)
  - The combined dataset (Wen + ours) that is used in the paper.