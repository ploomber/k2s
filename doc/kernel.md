# Bootstrapping Jupyter kernels

`k2s` allows you to install all required dependencies in a Jupyter notebook.

Download sample notebook has `import pandas as pd`:

```python
from urllib.request import urlretrieve

urlretrieve("https://raw.githubusercontent.com/ploomber/k2s/main/examples/simple.ipynb",
            "sample-demo.ipynb")
```

## Install in the current kernel

```python
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name=None)
```

## Create new kernel

```python
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name="my-new-kernel")
```
