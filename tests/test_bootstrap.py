import json
from pathlib import Path
from unittest.mock import Mock
import subprocess
import sys

import pytest

from k2s.cli import CLI
from k2s import bootstrap


def is_installed(env_name, package):
    return len(list(
        Path(env_name).glob(f'lib/**/site-packages/{package}'))) == 1


def test_bootstrap(tmp_empty, monkeypatch):
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'kaas', 'get',
            'ploomber/soorgeon/main/examples/machine-learning/nb.ipynb'
        ],
    )

    cmds = []

    def mock_run(*args, **kwargs):
        cmds.append(args)

        if Path(args[0][0]).name not in {'jupyter-lab', 'jupyter-lab.exe'}:
            subprocess.run(*args, **kwargs)

    monkeypatch.setattr(bootstrap, 'subprocess_run', mock_run)

    with pytest.raises(SystemExit) as excinfo:
        CLI()

    assert Path(cmds[-1][0][0]).name.startswith('jupyter-lab')
    assert excinfo.value.code == 0

    # ensure packages are installed
    assert is_installed('nb-env', 'matplotlib')
    assert is_installed('nb-env', 'sklearn')
    assert is_installed('nb-env', 'seaborn')


@pytest.mark.parametrize('path, expected_file, expected_installed', [
    ['examples/with-files.ipynb', "with-files-something.txt", {'jupyterlab'}],
    ['examples/imports/nb.ipynb', "functions.py", {'jupyterlab', 'pandas'}],
],
                         ids=[
                             'simple',
                             'package-needed',
                         ])
def test_downloads_files(tmp_empty, monkeypatch, path, expected_file,
                         expected_installed):
    monkeypatch.setattr(
        sys,
        'argv',
        ['kaas', 'get', f'ploomber/k2s/main/{path}'],
    )

    mock = Mock()
    mock().stdout.readline.return_value = b''
    mock().poll.return_value = 0

    monkeypatch.setattr(bootstrap, 'subprocess_run', Mock())
    monkeypatch.setattr(bootstrap, 'Popen', mock)
    monkeypatch.setattr(bootstrap, 'venv', Mock())

    with pytest.raises(SystemExit) as excinfo:
        CLI()

    assert excinfo.value.code == 0
    assert Path(expected_file).is_file()

    install = mock.call_args_list[2][0][0]
    i = install.index('install')
    installed = install[i + 1:]
    assert set(installed) == expected_installed


@pytest.mark.parametrize('nb', [
    {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    },
    {
        "cells": [],
        "metadata": {
            "kernelspec": {}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    },
],
                         ids=[
                             'metadata-empty',
                             'kernelspec-empty',
                         ])
def test_adds_kernelspec(tmp_empty, nb, monkeypatch):
    mock = Mock()
    mock().stdout.readline.return_value = b''
    mock().poll.return_value = 0

    monkeypatch.setattr(bootstrap, 'subprocess_run', Mock())
    monkeypatch.setattr(bootstrap, 'Popen', mock)
    monkeypatch.setattr(bootstrap, 'venv', Mock())

    Path("nb.ipynb").write_text(json.dumps(nb), encoding='utf-8')

    bootstrap.from_file('nb.ipynb')

    nb_loaded = json.loads(Path("nb.ipynb").read_text())

    assert nb_loaded['metadata']['kernelspec'] == {
        'display_name': 'Python 3 (ipykernel)',
        'language': 'python',
        'name': 'python3'
    }


# TODO: test that imports are extracted from imports *and* plain text
