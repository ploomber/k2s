# `conda` on Google Colab

```{important}
Ensure you're running `k2s>=0.1.8`.

A Colab example is [available here.](https://colab.research.google.com/drive/1pPhAQpAhJcsiIDmsP1g8mSjZvU1d7VAg)
```

`k2s` can install `conda` on Google Colab, allowing you to install dependencies easily.

## Instructions

Add the following to your Colab notebook.

Install k2s:

```python
%pip install k2s --quiet
```

Run `install`:

```python
from k2s import install
install(["some-pacakge", "another-package"])
```

```{important}
The first time you run `install`, the kernel will restart, that's expected.
Upon restarting, **run the cell with the `install` call again.**
```

## Example: install `geopandas` and `cartopy`


```python
%pip install k2s --quiet
from k2s import install
install(["geopandas", "cartopy", "matplotlib"])
```

Test:

```python
import matplotlib.pyplot as plt
import geopandas
from cartopy import crs as ccrs

path = geopandas.datasets.get_path('naturalearth_lowres')
df = geopandas.read_file(path)
_ = df.plot()
```

## Example: install `pymc`


```python
%pip install k2s --quiet
from k2s import install
install(["pymc"])
```

Test:

```python
import pymc
```