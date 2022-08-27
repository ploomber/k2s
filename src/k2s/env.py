import shutil
from pathlib import Path
import json
import subprocess


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


def _get_info():
    from conda.cli.python_api import run_command, Commands

    # maybe replace this with sys.prefix?
    out, err, code = run_command(Commands.INFO, "--json")
    return json.loads(out)


def _current_prefix():
    return _get_info()["active_prefix"]


def _install(name, requirements, inline=False, verbose=False):
    """Create a new conda environment
    """
    from mamba import api

    requirements = list(requirements) + ["ipykernel"]

    fn = api.install if inline else api.create

    if verbose:
        fn(
            name,
            requirements,
            ('conda-forge', ),
        )

    else:
        # NOTE: capturing output when using the Python API isn't working
        cmds = ['install'] if inline else ['create', '-n', name]
        cmd = ['mamba'] + cmds + requirements + ['-c', 'conda-forge', '-y']
        subprocess.run(cmd, capture_output=True, check=True)


def install(name, requirements, inline=False, verbose=False):
    """Create a new kernel
    """
    prefix = _current_prefix()

    # delete existing environment, otherwise mamba will complain with a
    # cryptic error
    prefix_new = Path(prefix, 'envs', name)

    if prefix_new.is_dir():
        shutil.rmtree(prefix_new)

    # create conda environment
    _install(name, requirements, inline=inline, verbose=verbose)

    # newly created environment
    path_to_python = Path(prefix, 'envs', name, 'bin', 'python')

    # folder where we'll register the kernel (in the prefix)
    path_to_kernels = Path(prefix, 'share', 'jupyter', 'kernels')

    spec = _make_spec(path_to_python, name)

    path_to_kernel = Path(path_to_kernels, name)
    path_to_kernel.mkdir(exist_ok=True)

    (path_to_kernel / 'kernel.json').write_text(json.dumps(spec))
