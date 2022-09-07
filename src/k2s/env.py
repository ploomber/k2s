import shutil
from pathlib import Path
import json
import subprocess

from k2s.subprocess import _run_command


def _make_spec(path_to_python, name):
    return {
        "argv": [
            str(path_to_python), "-m", "ipykernel_launcher", "-f",
            "{connection_file}"
        ],
        "display_name":
        f"Python 3 ({name})",
        "language":
        "python",
        "metadata": {
            "debugger": True
        }
    }


def _conda_active_prefix():
    out = subprocess.run(['conda', 'info', '--json'],
                         check=True,
                         capture_output=True)
    return json.loads(out.stdout.decode())['active_prefix']


def _conda_base_prefix():
    out = subprocess.run(['conda', 'info', '--json'],
                         check=True,
                         capture_output=True)
    return json.loads(out.stdout.decode())['conda_prefix']


def _install(name,
             requirements,
             requirements_pip,
             inline=False,
             verbose=False):
    """Create a new conda environment
    """

    # TODO: install packages in one step (generate environment.yml)
    requirements = list(requirements) + ["ipykernel"]

    cmds = ['install'] if inline else ['create', '-n', name]
    cmd = ['mamba'] + cmds + requirements + ['-c', 'conda-forge', '-y']
    _run_command(cmd)

    if inline:
        cmd = ['python', '-m', 'pip', 'install']
    else:
        cmd = [
            str(Path(_conda_base_prefix(), 'envs', name, 'bin', 'python')),
            '-m',
            'pip',
            'install',
        ]

    _run_command(cmd + list(requirements_pip))


def _ensure_mamba():
    if not shutil.which('mamba'):
        print('mamba not found, installing...')
        subprocess.run(
            ['conda', 'install', '-c', 'conda-forge', 'mamba', '-y'])


def _ensure_conda():
    if not shutil.which('conda'):
        # TODO: install at ~/.k2s/conda
        raise RuntimeError('conda not found')


def install(name,
            requirements,
            requirements_pip=None,
            inline=False,
            verbose=False):
    """Create a new kernel
    """
    _ensure_conda()
    _ensure_mamba()

    prefix_base = _conda_base_prefix()
    prefix = _conda_active_prefix()

    # delete existing environment, otherwise mamba will complain with a
    # cryptic error
    prefix_new = Path(prefix_base, 'envs', name)

    if prefix_new.is_dir():
        shutil.rmtree(prefix_new)

    # create conda environment
    _install(name,
             requirements,
             requirements_pip,
             inline=inline,
             verbose=verbose)

    # newly created environment
    path_to_python = Path(prefix_base, 'envs', name, 'bin', 'python')

    # folder where we'll register the kernel (in the prefix)
    path_to_kernels = Path(prefix, 'share', 'jupyter', 'kernels')

    spec = _make_spec(path_to_python, name)

    path_to_kernel = Path(path_to_kernels, name)
    path_to_kernel.mkdir(exist_ok=True)

    (path_to_kernel / 'kernel.json').write_text(json.dumps(spec))
