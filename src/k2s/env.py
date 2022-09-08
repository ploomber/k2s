from pathlib import Path
import json

from k2s.conda import CondaManager


def _make_spec(path_to_python, display_name):
    """Create Jupyter kernel spec

    Parameters
    ----------
    path_to_python : str
        Path to bin/python in the target environment (the env must have
        ipykernel installed)

    display_name : str
        Name displayed to the user
    """
    return {
        "argv": [
            str(path_to_python), "-m", "ipykernel_launcher", "-f",
            "{connection_file}"
        ],
        "display_name":
        f"Python 3 ({display_name})",
        "language":
        "python",
        "metadata": {
            "debugger": True
        }
    }


def install(name=None,
            requirements=None,
            requirements_pip=None,
            verbose=False):
    """Create a new kernel
    """
    cm = CondaManager(install_conda=True)

    prefix_new_env = cm.create_env(
        name=name,
        requirements=requirements,
        requirements_pip=requirements_pip,
    )

    # register kernel if we created a new environment
    if name is not None:
        # newly created environment
        path_to_python = Path(prefix_new_env, 'bin', 'python')

        # folder where we'll register the kernel (in the prefix)
        # NOTE: I don't think this will work every time, we need to test with
        # sagemaker, google cloud notebooks, etc. - probably better to
        # install in the local kernels directory
        prefix = cm.get_active_prefix()
        path_to_kernels = Path(prefix, 'share', 'jupyter', 'kernels')

        spec = _make_spec(path_to_python, name)

        path_to_kernel = Path(path_to_kernels, name)
        path_to_kernel.mkdir(exist_ok=True)

        (path_to_kernel / 'kernel.json').write_text(json.dumps(spec))
