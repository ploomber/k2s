# Bootstrapping Jupyter kernels


Download sample notebook:

```{code-cell}
from urllib.request import urlretrieve

urlretrieve("https://raw.githubusercontent.com/ploomber/k2s/main/examples/simple.ipynb",
            "sample-demo.ipynb")
```

## Install in the current kernel

```{code-cell}
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name=None)
```

## Create new kernel

```{code-cell}
from k2s import bootstrap_env
bootstrap_env("sample-demo.ipynb", name="my-new-kernel")
```
