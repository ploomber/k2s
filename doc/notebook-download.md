---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Downloading Jupyter notebooks

If you find a Jupyter notebook on GitHub that you want to try locally, you can use `k2s` to download it, install all dependencies and start JupyterLab in an isolated environment.

Run the following in a terminal:

```sh
k2s get {GITHUB_URL}
```

+++

Example:

```{code-cell} ipython3
# %%sh
# k2s get https://github.com/ploomber/k2s/blob/doc/examples/sklearn-demo.ipynb
```

```{code-cell} ipython3

```
