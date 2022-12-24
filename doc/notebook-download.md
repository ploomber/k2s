# Downloading Jupyter notebooks

If you find a Jupyter notebook on GitHub that you want to try locally, you can use `k2s` to download it, install all dependencies and start JupyterLab in an isolated environment.

Run the following in a terminal:

```sh
k2s get {GITHUB_URL}
```

+++

Example:

```{code-cell} ipython3
%%sh
k2s get https://github.com/ploomber/k2s/blob/main/examples/simple.ipynb --no-jupyter
```

You can also download from other domains:

```sh
k2s get https://domain.com/path/to/notebook.ipynb
```
