# k2s

A tool to bootstrap Python environments and Jupyter kernels.

## Installation

```sh
pip install k2s
```

## Usage: Google Colab

`k2s` can install `conda` on Colab: [see this example.](https://colab.research.google.com/drive/1pPhAQpAhJcsiIDmsP1g8mSjZvU1d7VAg)
## Usage: Get GitHub notebook

To download a notebook, bootstrap a virtual environment, and start Jupyter:

```sh
k2s get {github-user}/{repo}/{branch}/path/to/notebook.ipynb
```

Example:

```sh
k2s get ploomber/sklearn-evaluation/master/docs/source/nbs/nbdb.ipynb
```

## Usage: Installing packages inside Jupyter

To parse a notebook, infer packages and install them, run this in the notebook:

```python
from k2s import bootstrap_env
bootstrap_env("notebook-name.ipynb", name=None)
```

If you want to create a new kernel:

```python
from k2s import bootstrap_env
bootstrap_env("notebook-name.ipynb", name="my-new-kernel")
```
