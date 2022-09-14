"""
pip install k2s --upgrade && k2s get ploomber/jupysql/doc/nb.ipynb
"""
import shutil
import os
import json
from pathlib import Path, PurePosixPath
from subprocess import run as subprocess_run
import venv
from urllib.request import urlretrieve

from k2s.parse import (extract_imports_from_notebook, download_files,
                       extract_code)

from k2s.subprocess import _run_command


def path_to_bin(env_name, bin):
    dir = 'Scripts' if os.name == 'nt' else 'bin'
    bin_name = f'{bin}.exe' if os.name == 'nt' else bin
    return str(Path(env_name, dir, bin_name))


def from_url(url):
    """

    >>> from k2s.bootstrap import from_url; from_url("URL")
    """
    url = f'https://raw.githubusercontent.com/{url}'

    file = PurePosixPath(url).name
    urlretrieve(url, file)

    return from_file(file, url=url)


def from_file(file, url=None):
    env_name = Path(file).stem + '-env'

    nb = json.loads(Path(file).read_text(encoding='utf-8'))

    if 'metadata' not in nb:
        nb['metadata'] = {}

    if not nb['metadata'].get('kernelspec'):
        print('Notebook is missing kernel information, assuming Python...')
        nb['metadata']['kernelspec'] = {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        }

        Path(file).write_text(json.dumps(nb), encoding='utf-8')

    deps = extract_imports_from_notebook(nb)

    # FIXME: we're runnign extract_code inside extract_imports already, we
    # should refactor
    if url:
        deps_extra = download_files(extract_code(nb), url)
    else:
        deps_extra = set()

    deps = list(set(deps) | deps_extra)

    print("Creating virtual environment...")
    print(f"Installing: {', '.join(deps)}")
    print("This may take a moment. "
          "Join our community while you wait: https://ploomber.io/community")

    # if the user stopped the process in the middle and tried again, the env
    # might exist but will be corrupted, so we must clean it
    if Path(env_name).exists():
        shutil.rmtree(env_name)

    # maybe site-packages, yes? will that copy the existing ones? perhaps
    # they already ahve most of the dependencies and we can save time.
    # if so, then we need to ensure jupyterlab starts with the kernel in
    # the virtual environment
    venv.create(env_name, with_pip=True, system_site_packages=False)

    path_to_python = path_to_bin(env_name, 'python')

    subprocess_run(
        [path_to_python, '-m', 'pip', 'install', 'pip', '--upgrade'],
        check=True,
        capture_output=True)

    _run_command([path_to_python, '-m', 'pip', 'install', 'jupyterlab'] + deps)

    print("Lauching Jupyter... (this might take a few seconds)")

    # TODO: if jupyter lab is already installed, we can use it (and skip
    # installation), but we have to make sure that the kernel used is
    # the one in the venv, not in the parent env
    path_to_jupyterlab = path_to_bin(env_name, 'jupyter-lab')

    print('To exit: CTRL + C')

    try:
        subprocess_run([path_to_jupyterlab, file],
                       check=True,
                       capture_output=True)
    except KeyboardInterrupt:
        print('Exiting...')
        print(f'\nTo laucnh again:\n\n'
              f'{path_to_jupyterlab} {file}')
