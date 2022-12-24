# Bootstrapping Jupyter kernels


Download sample notebook:

```python
from urllib.request import urlretrieve

urlretrieve("https://raw.githubusercontent.com/ploomber/k2s/doc/examples/sklearn-demo.ipynb",
            "sample-demo.ipynb")
```

## Install in the current kernel

```python
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name=None)
```

## Switching kernel

```python
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name="my-new-kernel")
```

```python

```
