import json
import sys
import shutil
from pathlib import Path
import urllib.request
import subprocess

from k2s.subprocess import _run_command

# https://docs.python.org/3/library/sys.html#sys.platform
URLS = {
    'linux':
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    'darwin':
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh",
}


def _get_conda_url():
    url = URLS.get(sys.platform)

    if url is None:
        raise RuntimeError("Only Linux and Mac are supported")

    return url


class CondaManager:
    """Manage conda installations

    Parameters
    ----------
    install_conda : bool, default=False
        Force installing at ~/.k2s/conda, even if there's an existing
        installation
    """

    def __init__(self, install_conda=True) -> None:
        self.install_conda = install_conda

        if not shutil.which("conda") and not install_conda:
            raise RuntimeError("conda is not installed, to install it "
                               "pass install_conda=True")

        has_local_conda = (self.get_home() / 'conda').is_dir()

        if (not shutil.which('conda')
                or install_conda) and not has_local_conda:
            self.install_local()

        # ensure mamba is installed in the base prefix
        self.install_mamba()

    def install_local(self):
        """Installs miniconda in ~/.k2s/conda
        """
        print("Installing conda (only needed once)...")
        home = self.get_home()
        urllib.request.urlretrieve(_get_conda_url(), "miniconda.sh")
        _run_command(["bash", "miniconda.sh", "-b", "-p", str(home / 'conda')])
        print("Finished installing conda.")

    def install_mamba(self):
        prefix = self.get_base_prefix()

        if not Path(prefix, "bin", "mamba").exists():
            print("Installing mamba...")
            _run_command([
                self.get_base_conda_bin(),
                "install",
                "mamba",
                "-c",
                "conda-forge",
                "-y",
                "--prefix",
                self.get_base_prefix(),
            ])
            print("Done installing mamba.")

    def create_env(self, name, requirements, requirements_pip):
        # TODO: if the env already exists, say "updating" instead of
        # "installing"
        print("Installing dependencies...")

        spec = {
            "name":
            name,
            "channels": ["conda-forge"],
            "dependencies":
            list(requirements) +
            ["pip", "ipykernel", "python",
             dict(pip=requirements_pip)],
        }

        Path("env.yml").write_text(json.dumps(spec))

        if name is None:
            prefix = str(Path(self.get_active_prefix()))
        else:
            prefix = str(Path(self.get_base_prefix(), "envs", name))

        cmd = [
            self.get_base_mamba_bin(),
            "env",
            "update",
            "--file",
            "env.yml",
            "--prefix",
            prefix,
            # NOTE: --prune is broken since conda 4.4
            # https://github.com/conda/conda/issues/7279
            "--prune",
        ]

        _run_command(cmd)

        print("Done installing dependencies.")

        return prefix

    def get_home(self):
        home = Path('~', '.k2s').expanduser()
        home.mkdir(exist_ok=True)
        return home

    def get_base_prefix(self):
        """Get base conda base prefix to use for all commands
        """
        if self.install_conda:
            return str(Path('~', '.k2s', 'conda').expanduser())
        else:
            return str(Path(shutil.which("conda")).parent.parent)

    def get_base_conda_bin(self):
        return str(Path(self.get_base_prefix(), "bin", "conda"))

    def get_base_mamba_bin(self):
        return str(Path(self.get_base_prefix(), "bin", "mamba"))

    def get_active_prefix(self):
        out = subprocess.run([self.get_base_conda_bin(), 'info', '--json'],
                             check=True,
                             capture_output=True)
        # TODO: this will return none if in the base env (this happens in
        # kaggle) - maybe is the conda version?
        return json.loads(out.stdout.decode())['active_prefix']

    def prune():
        """Delete all environments and kernels
        """
        pass
