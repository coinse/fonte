# **Fonte: Finding Bug Inducing Commit From Failure**

<p align="center">
  <img src="./fonte.png" />
</p>

## **Environmental Setup**
- Hardware
  - Developed under Mac with Intel chip
  - Compatible with AMD64 processors
- Software
  - Tested with bash (recommended), zsh, PowerShell
  - Python 3.9.1
    - If using `pyenv`, use these commands:
      ```bash
      pyenv install 3.9.1
      pyenv local 3.9.1
      ```
    - **Install dependencies**
        ```bash
        python -m pip install numpy==1.21.0 pandas==1.4.3 scipy==1.9.0 tqdm matplotlib==3.4.0 seaborn==0.11.1 rank-bm25==0.2.2 tabulate==0.8.9 jupyter setuptools
        python -m pip install lib/SBFL
        python -m pip install lib/spiral
        ```

  - Docker client (only for the replication or extension): [Download here](https://www.docker.com/products/docker-desktop)

## **Getting Started**

### Please note that
- The core ingredient data including coverage matrix and commit history is available at `./data/Defects4J/core/`.
- The BIC dataset is available at `./data/Defects4J/BIC_dataset/`.

### Running Fonte
```bash
python Fonte.py data/Defecst4J/core/<pid>-<vid>b -o <savepath>
```
- Example:
  ```bash
  python Fonte.py data/Defects4J/core/Cli-29b -o output.csv
  # Number of total commits: 616
  #          vote  rank  is_style_change
  # commit
  # c0d5c79   1.0   1.0            False
  # 147df44   0.0   2.0             True
  ```

- Available arguments:
  ```
  usage: Fonte.py [-h] [--tool TOOL] [--formula FORMULA] [--alpha ALPHA] [--tau TAU] [--lamb LAMB] [--skip-stage-2] [--output OUTPUT] coredir

  Compute commit scores

  positional arguments:
    coredir               data/Defects4J/core/<pid>-<vid>b

  optional arguments:
    -h, --help            show this help message and exit
    --tool TOOL           history retrieval tool, git or shovel (default: git)
    --formula FORMULA     SBFL formula (default: Ochiai)
    --alpha ALPHA         alpha (default: 0)
    --tau TAU             tau (default: max)
    --lamb LAMB           lambda (default: 0.1)
    --skip-stage-2        skip stage 2 (default: False)
    --output OUTPUT, -o OUTPUT
                          path to output file (example: output.csv)
  ```

## **Reproducing the experiment results**
1. Run the Jupyter notebook
    ```bash
    jupyter notebook
    ```
    If you're a VSCode user, just install the `Jupyter` extension.
2. Open `experiment.ipynb` and run the cells to reproduce our experiment results.
    - The output will be saved to `./experiment_results/`. Note that the directory already contains the pre-computed results. If you want to fully replicate our experiments, remove all files from the `./experiment_results/` and run the cells again.

## **Wait, how to extract the core data for other Defects4J faults for further extensions?** (optional)
We provide a pre-built Docker image, containing our data collection scripts along with Defects4J, that can be used to extract the core data for all bugs in Defects4J.
1. Pull the image from DockerHub. This may take a while because the image size is about 4GB.
    ```bash
    docker pull anonyfonte/fonte:latest
    ```
2. Start a Docker container
    ```bash
    docker run -dt --name fonte -v $(pwd)/docker/workspace:/root/workspace anonyfonte/fonte:latest
    ```
    - The directory `./docker/workspace` in the local machine will share data with `/root/workspace` in the container.
    - `$(pwd)`: The current directory. Change it to `${PWD}` or `%cd%` if you're using PowerShell or Windows Command Prompt, respectively.
3. Collect the coverage information and the commit history of `<pid>-<vid>b`
    ```bash
    docker exec fonte sh collect_core.sh <pid> <vid> <tool:git,shovel>
    # docker exec fonte sh collect_core.sh Cli 29 git
    ```
    - The output will be saved to `./docker/workspace/data/<pid>-<vid>b/`
    - Don't forget to append the tool option (`git` or `shovel`)!
4. Run Fonte on the newly collected data:
    ```bash
    python Fonte.py ./docker/workspace/data/<pid>-<vid>b/
    # python Fonte.py ./docker/workspace/data/Cli-29b/
    ```

    💡 To **speed up** the AST comparison, you can turn off the code formatting using OpenRewrite. Just append `false` when calling `collect_core.sh`:
    ```bash
    docker exec fonte sh collect_core.sh <pid> <vid> <tool:git,shovel> false
    # docker exec fonte sh collect_core.sh Cli 29 git false
    ```



## **File & Directory Structure**
- `README.md`
- `CodeShovel-error.md`: this contains the error reproduction steps for CodeShovel
- **`Fonte.py`: Fonte CLI**
- **`experiment.ipynb`: the main experiment script**
- `run_Bug2Commit.py`: the python script implementing Bug2Commit (not contained in the lightweight version)
- `data/`
  - `Defects4J/`
    - `BIC_dataset/`
      - `*.csv`
      - `README.md`: See this for more information about the BIC dataset
    - `core/`
      - `<pid>-<vid>b`
        - `git/`
          - `commits.pkl`: pandas Dataframe
          - `validation.csv`: style change commit validation results in the following format:
            ```csv
            commit,filepath,[C|U|N|E]
            ...
            ```
            - where
              - `C`: ASTs are different (**c**hanged)
              - `U`: ASTs are identical (**u**nchanged)
              - `N`: The file is **n**ewly introduced
              - `E`: External **e**rror by GumTree
            - A commit is a style-change commit only when the result for every related file is `U`.
          - `validation_noOpenRewrite.csv`: style change commit validation results without the CheckStyle fixes using OpenRewrite
        - `shovel/`
          - `raw/`: the raw output files from CodeShovel
          - `commits.pkl`: pandas Dataframe
          - `validation.csv`
          - `validation_noOpenRewrite.csv`: style change commit validation results without the CheckStyle fixes using OpenRewrite
        - `coverage.pkl`: pandas Dataframe (index: tests, columns: lines)
        - `commits.log`: all commits in the branch
        - `failing_tests`: the exception messages and stack traces of failing test cases (used when running Bug2Commit)
    - `baseline/`: this contains the ingredients & results for Bug2Commit and FBL-BERT.
       - `<pid>-<vid>b/`
         - `commits/`: the raw contents of commits that modified at least one `.java` file (collected using the `data_utils.py` in [FBL-BERT](https://anonymous.4open.science/r/fbl-bert-700C), not contained in the lightweight version)
         - `br_short.txt`: a title of the bug report
         - `br_long.txt`: a main body of the bug report
         - `ranking_INDEX_FBLBERT_RN_bertoverflow_QARC_q256_d230_dim128_cosine_q256_d230_dim128_commits_token.tsv`: raw retrieval results for `<pid>-<vid>b` (**FBL-BERT**)
         - `ranking_Bug2Commit.csv`: raw retrieval results for `<pid>-<vid>b` (**Bug2Commit**)
    - `buggy_methods.json`: The buggy method information is constructed for the actual buggy versions of programs in Defects4J (corresponding to `revision.id.buggy`). The actual buggy version may differ from the isolated buggy version provided by Defects4J that you obtain right after the checkout. Therefore, the buggy methods may not exactly match the methods fixed by the patch.
  - `industry/`: the results of applying Fonte to the batch testing data of an industry software ABC
    - `<data>_<test>.csv`: test names are anonymized due to DBR
- `docker/`: containing the docker resources that can be used to extract the core data
  - `resources/`: the resources needed to build the image from scratch
  - `Dockerfile`: the docker config file used to build the image `bic:new`
  - `workspace/`
    - `collect_core.sh`: the main script for code data extraction
    - `collect.py`
- `experiment_results/`
  - `rankings/`
    - `git_line_Ochiai_voting(_C_BIC|_C_susp)/`: the postfix `_C_susp` means skipping Stage 2
      - `<tau>-<alpha>-<lambda>.csv`
      - `score-<lambda>.csv`: baseline
      - `equal-<lambda>.csv`: baseline
    - `git_line_Ochiai_maxArrg(_C_BIC|_C_susp).csv`: max-aggregation baseline
    - `Random(_C_BIC|_C_susp).csv`: Random baseline
    - `FBL-BERT(_C_BIC|_C_susp).csv`: FBL-BERT results
    - `Bug2Commit(_C_BIC|_C_susp).csv`: Bug2Commit results
    - `Worst(_C_BIC|_C_susp).csv`: Lower bound of the results
- `lib/`
  - `SBFL/`
  - `spiral/`
  - `experiment_utils.py`: it contains the main functions
  - `README.md`
