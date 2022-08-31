from pathlib import Path
import pytest
from unittest.mock import Mock
import subprocess
import sys

from k2s.cli import CLI
from k2s import bootstrap


def is_installed(env_name, package):
    return len(list(
        Path(env_name).glob(f'lib/*/site-packages/{package}'))) == 1


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

    mock_subprocess = Mock()
    mock_subprocess.Popen().stdout.readline.return_value = b''
    mock_subprocess.Popen().poll.return_value = 0

    monkeypatch.setattr(bootstrap, 'subprocess', mock_subprocess)
    monkeypatch.setattr(bootstrap, 'venv', Mock())

    with pytest.raises(SystemExit) as excinfo:
        CLI()

    assert excinfo.value.code == 0
    assert Path(expected_file).is_file()

    install = mock_subprocess.Popen.call_args_list[-1][0][0]
    i = install.index('install')
    installed = install[i + 1:]
    assert set(installed) == expected_installed


# TODO: test that imports are extracted from imports *and* plain text
