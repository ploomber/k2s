import subprocess
import shutil
from pathlib import Path
import sys

import pytest
from k2s.conda import CondaManager


@pytest.mark.skipif(sys.platform == "win32", reason="not supported")
def test_install_local():
    target = Path('~', '.k2s', 'conda').expanduser()

    if target.is_dir():
        shutil.rmtree(target)

    cm = CondaManager(install_conda=True)

    bin = str(target / 'bin' / 'conda')

    out = subprocess.run([bin, '--help'], check=True, capture_output=True)

    assert "usage: conda" in out.stdout.decode()
    assert cm.get_base_conda_bin() == bin
    assert cm.get_base_prefix() == str(target)


# TODO: test install mamba
