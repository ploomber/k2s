import pytest
from unittest.mock import Mock
import subprocess
import sys

from k2s.cli import CLI
from k2s import bootstrap


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

        if not args[0][0].endswith('jupyter-lab'):
            subprocess.run(*args, **kwargs)

    mock = Mock()
    mock.run = mock_run

    monkeypatch.setattr(bootstrap, 'subprocess', mock)

    with pytest.raises(SystemExit) as excinfo:
        CLI()

    assert cmds[-1][0][0].endswith('jupyter-lab')
    assert excinfo.value.code == 0


# TODO: test that imports are extracted from imports *and* plain text
