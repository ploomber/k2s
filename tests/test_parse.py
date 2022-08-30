import os
from pathlib import Path

import pytest
import nbformat

from k2s import parse

# TODO: test extract_imports with a notebook read from nbformat and one with
# json

# TODO: test extract_imports returns no duplicates (it currently does)


def test_extract_imports():
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(source="import pandas as pd"),
        nbformat.v4.new_code_cell(source="import sklearn"),
    ]

    assert parse.extract_imports_from_notebook(nb) == [
        'pandas', 'scikit-learn'
    ]


@pytest.mark.parametrize('source, expected', [
    [
        """
```sh
pip install duckdb duckdb-engine pyarrow
```
""",
        {
            'duckdb',
            'duckdb-engine',
            'pyarrow',
        },
    ],
    [
        """
```sh
pip install duckdb duckdb-engine pyarrow --upgrade
```
""",
        {
            'duckdb',
            'duckdb-engine',
            'pyarrow',
        },
    ],
    [
        """
```sh
pip install duckdb duckdb-engine pyarrow -U
```
""",
        {
            'duckdb',
            'duckdb-engine',
            'pyarrow',
        },
    ],
    [
        """
```sh
pip install duckdb duckdb-engine pyarrow
```

```
pip install pyarrow
```
""",
        {
            'duckdb',
            'duckdb-engine',
            'pyarrow',
        },
    ],
    [
        """

Try locally:

```python
pip install k2s -U && k2s get ploomber/jupysql/main/examples/nb.ipynb
```

```
pip install pyarrow
```
""",
        {'pyarrow'},
    ],
],
                         ids=[
                             'simple',
                             'double-dash-option',
                             'single-dash-option',
                             'duplicates',
                             'ignores-itself',
                         ])
def test_extract_from_plain_text(tmp_empty, source, expected):
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(source=source),
    ]

    nb_str = nbformat.writes(nb, version=nbformat.NO_CONVERT)

    assert set(parse.extract_from_plain_text(nb_str)) == expected


def test_extract_imports_also_plain_text():
    md_source = """
```python
pip install duckdb duckdb-engine pyarrow
```
"""
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(source="import pandas as pd"),
        nbformat.v4.new_code_cell(source="import sklearn"),
        nbformat.v4.new_markdown_cell(source=md_source)
    ]

    assert set(parse.extract_imports_from_notebook(nb)) == {
        'pandas',
        'scikit-learn',
        'duckdb',
        'duckdb-engine',
        'pyarrow',
    }


@pytest.mark.parametrize('source, expected', [
    [
        """
df = pd.read_csv("some-file.txt")

read('notebook.ipynb')

nbformat.read('another.ipynb')

path = Path("path/to/file.ext")
""", {
            'some-file.txt',
            'notebook.ipynb',
            'another.ipynb',
            'path/to/file.ext',
        }
    ],
    [
        """
read(fp='notebook.ipynb')

nbformat.read('another.ipynb', another="value")
""", {
            'notebook.ipynb',
            'another.ipynb',
        }
    ],
    [
        """
invalid python code
""",
        set(),
    ],
    [
        """
df = pd.read_parquet("some-file.parquet")

df_2 = pd.read_csv("some-file.csv")
""",
        {
            'some-file.parquet',
            'some-file.csv',
        },
    ],
    [
        """
df = pd.read_sql("SELECT * FROM table", conn)
""",
        set(),
    ],
    [
        """
df = pd.read_csv(path)
""",
        set(),
    ],
],
                         ids=[
                             'various',
                             'kwargs',
                             'invalid',
                             'pandas',
                             'read_sql',
                             'variable',
                         ])
def test_local_files(source, expected):
    assert parse.local_files(source) == expected


def test_download_files(tmp_empty):
    source = """
Path("with-files-something.txt")

Path("non-existing-file.txt")
"""

    url = ("https://raw.githubusercontent.com/ploomber/k2s/main"
           "/examples/with-files.ipynb")

    parse.download_files(source, url=url)

    assert os.listdir() == ["with-files-something.txt"]
    assert Path("with-files-something.txt").read_text() == 'hello!\n'
