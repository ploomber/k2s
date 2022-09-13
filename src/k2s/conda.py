import os
import json
import sys
import shutil
from pathlib import Path
import urllib.request
import subprocess
from os import environ

from ploomber_core.telemetry.telemetry import Telemetry
from ploomber_core.config import Config

from k2s.subprocess import _run_command
from k2s.index import ChannelData
from k2s.exceptions import KernelRestartRequired

try:
    from importlib.metadata import version
except ModuleNotFoundError:
    from importlib_metadata import version

BASE_MINI = "https://repo.anaconda.com/miniconda"

# https://docs.python.org/3/library/sys.html#sys.platform
URLS = {
    'linux': f"{BASE_MINI}/Miniconda3-latest-Linux-x86_64.sh",
    'darwin': f"{BASE_MINI}/Miniconda3-latest-MacOSX-x86_64.sh",
}

MINI_3_7 = (f"{BASE_MINI}/Miniconda3-py37_4.12.0-Linux-x86_64.sh")

IS_KAGGLE = "KAGGLE_DOCKER_IMAGE" in environ
IS_COLAB = "COLAB_GPU" in environ

telemetry = Telemetry(
    api_key="phc_P9SpSeypyPwxrMdFn2edOOEooQioF2axppyEeDwtMSP",
    package_name="k2s",
    version=version("k2s"),
)


class CondaManager:
    """Manage conda installations

    Parameters
    ----------
    install_conda : bool, default=False
        Force installing at ~/.k2s/conda, even if there's an existing
        installation
    """

    def __init__(self, install_conda=True) -> None:
        self.pre_setup()

        self.install_conda = install_conda

        if not shutil.which("conda") and not install_conda:
            raise RuntimeError("conda is not installed, to install it "
                               "pass install_conda=True")

        has_local_conda = (self.get_config_directory() / 'conda').is_dir()

        if (not shutil.which('conda')
                or install_conda) and not has_local_conda:
            home = self.get_config_directory()
            self.install_conda_in_prefix(str(home / 'conda'))

        # ensure mamba is installed in the base prefix
        prefix = self.get_base_prefix()
        self.install_mamba_in_prefix(prefix)
        self.post_conda_install()

    def pre_setup(self):
        pass

    def post_conda_install(self):
        pass

    def _get_conda_url(self):
        url = URLS.get(sys.platform)

        if url is None:
            raise RuntimeError("Only Linux and Mac are supported")

        return url

    def install_conda_in_prefix(self, prefix):
        """Installs miniconda in the given prefix
        """
        print(f"Installing conda ({prefix!r})...")
        urllib.request.urlretrieve(self._get_conda_url(), "miniconda.sh")
        _run_command(["bash", "miniconda.sh", "-b", "-f", "-p", prefix])
        print("Finished installing conda.")

    def install_mamba_in_prefix(self, prefix):
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
                prefix,
            ])
            print("Done installing mamba.")
        else:
            print("mamba already installed...")

    def create_env(self, name, requirements, requirements_pip):
        """
        Notes
        -----
        Theres a chance conda/mamba determine to re-install Python, example:

        mamba create --name test python=3.8.13 -c defaults --yes
        conda activate test
        mamba install ploomber -c conda-forge --dry-run

        This will crash the environment, so we must pin Python


        Examples
        --------
        >>> from k2s.conda import CondaManager
        >>> cm = CondaManager()
        >>> cm.create_env("some-env", requirements=["python=3.8.13"],
        ... requirements_pip=None)
        >>> cm.create_env("some-env", requirements=["ploomber"],
        ... requirements_pip=None)
        """
        # TODO: if the env already exists, say "updating" instead of
        # "installing"
        print(
            "Installing dependencies, this might take a few minutes. "
            "Join our community while you wait: https://ploomber.io/community")

        spec = {
            "name":
            name,
            "channels": ["conda-forge", "default"],
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

        # TODO: revert this change after executing the update?
        # if the environment exists, we must pin Python
        # should I pin ipykernel as well?
        if Path(prefix).exists():
            bin = str(Path(prefix, 'bin', 'python'))
            cmd = ("from sys import version_info as v"
                   "; print(f'{v.major}.{v.minor}.{v.micro}')")
            out = subprocess.run([bin, "-c", cmd],
                                 check=True,
                                 capture_output=True)
            version = out.stdout.decode().strip()
            Path(prefix, "conda-meta").mkdir(exist_ok=True)
            pinned_path = Path(prefix, "conda-meta", "pinned")
            if pinned_path.exists():
                pinned = pinned_path.read_text()
            else:
                pinned = ''

            pinned_path.write_text(f'{pinned}\npython=={version}')

        cmd = [
            self.get_base_mamba_bin(),
            "env",
            "update",
            "--file",
            "env.yml",
            "--prefix",
            prefix,
            # NOTE: --prune is broken since conda 4.4
            # https://github.com/conda/conda/issues/7279,
            # it doesn't do anything and we noticed it sometimes
            # breaks stuff
        ]

        _run_command(cmd)

        print("Done installing dependencies.")

        return prefix

    def get_config_directory(self):
        """Returns the directory to store k2s configuration
        """
        home = Path('~', '.k2s').expanduser()
        home.mkdir(exist_ok=True)
        return home

    def get_base_prefix(self):
        """Get base conda base prefix to use for all commands
        """
        if self.install_conda:
            return str(self.get_config_directory() / 'conda')
        else:
            # NOTE: is this the best way to retrieve this?
            # maybe sys.prefix?
            return str(Path(shutil.which("conda")).parent.parent)

    def get_base_conda_bin(self):
        return str(Path(self.get_base_prefix(), "bin", "conda"))

    def get_base_mamba_bin(self):
        return str(Path(self.get_base_prefix(), "bin", "mamba"))

    def get_active_prefix(self):

        out = subprocess.run([self.get_base_conda_bin(), 'info', '--json'],
                             check=True,
                             capture_output=True)

        active_prefix = json.loads(out.stdout.decode())['active_prefix']

        if not active_prefix:
            raise RuntimeError("Unable to determine current environment. "
                               "For help: https://ploomber.io/community")

        return active_prefix

    def prune():
        """Delete all environments and kernels
        """
        # also delete local conda installation
        pass


class ColabConfig(Config):
    install_requirements_argument: list = None

    def path(cls):
        # remove this once this is closed:
        # https://github.com/ploomber/core/issues/16
        path_to_cfg = Path('~/.k2s/colab/config.yaml').expanduser()
        path_to_cfg.parent.mkdir(exist_ok=True, parents=True)
        return path_to_cfg


class ColabCondaManager(CondaManager):

    def __init__(self, install_conda=True) -> None:
        self.pre_setup()

        if shutil.which("conda"):
            print("conda already installed...")
        else:
            self.install_conda_in_prefix(self.get_active_prefix())
            self.install_mamba_in_prefix(self.get_active_prefix())
            self.post_conda_install()

    def pre_setup(self):
        if not IS_COLAB:
            raise RuntimeError(
                f"{type(self).__name__} should only be used in Colab")

        # this is not added by default on Colab
        sys.path.insert(
            0, f"{self.get_active_prefix()}/lib/python3.7/site-packages")

    def post_conda_install(self):
        os.rename(sys.executable, f"{sys.executable}.colab")
        LD_LIBRARY_PATH = (f"{self.get_active_prefix()}/lib"
                           f":{os.environ.get('LD_LIBRARY_PATH', '')}")

        Path(sys.executable).write_text(f"""\
#!/bin/bash
export LD_LIBRARY_PATH={LD_LIBRARY_PATH}
{sys.executable}.colab -x $@
""")

        subprocess.run(["chmod", "+x", sys.executable], check=True)

        from IPython import get_ipython
        get_ipython().kernel.do_shutdown(restart=True)
        raise KernelRestartRequired

    def get_base_prefix(self):
        return "/usr/local"

    def get_active_prefix(self):
        return self.get_base_prefix()

    def _get_conda_url(self):
        return MINI_3_7


class KaggleCondaManager(CondaManager):

    def pre_setup(self):
        if not IS_KAGGLE:
            raise RuntimeError(
                f"{type(self).__name__} should only be used in Kaggle")

    def get_base_prefix(self):
        return "/opt/conda"

    def get_active_prefix(self):
        return self.get_base_prefix()


@telemetry.log_call('k2s-install')
def install(requirements):
    """Install packages
    """
    cfg = None

    if IS_COLAB:
        cfg = ColabConfig()

        if requirements == cfg.install_requirements_argument:
            print('Packages already installed...')
            # instantiate the manager since it'll configure the path for
            # Colab to work
            ColabCondaManager()
            return

        class_ = ColabCondaManager
    elif IS_KAGGLE:
        class_ = KaggleCondaManager
    else:
        class_ = CondaManager

    cm = class_()
    cd = ChannelData()
    conda, pip = cd.pkg_exists(requirements)
    cm.create_env(name=None, requirements=conda, requirements_pip=pip)

    if IS_COLAB:
        cfg.install_requirements_argument = list(requirements)
