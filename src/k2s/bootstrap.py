"""
pip install k2s --upgrade && k2s get ploomber/jupysql/doc/nb.ipynb
"""
import os
import json
import sys
from pathlib import Path, PurePosixPath
import subprocess
import venv
import urllib.request

from k2s.parse import extract_imports


def _get_python_folder_and_bin_name():
    folder = 'Scripts' if os.name == 'nt' else 'bin'
    bin_name = 'python.exe' if os.name == 'nt' else 'python'
    return folder, bin_name


def from_url(url):
    """

    >>> from k2s.bootstrap import from_url; from_url("URL")
    """
    url = f'https://raw.githubusercontent.com/{url}'

    file = PurePosixPath(url).name
    urllib.request.urlretrieve(url, file)
    return from_file(file)


def from_file(file):
    env_name = Path(file).stem + '-env'

    nb = json.loads(Path(file).read_text(encoding='utf-8'))

    deps = extract_imports(nb)

    print("Creating virtual environment...")
    print(f"Installing: {', '.join(deps)}")
    print("This may take a moment. "
          "Join our community while you wait: https://ploomber.io/community")

    # maybe site-packages, yes? will that copy the existing ones? perhaps
    # they already ahve most of the dependencies and we can save time.
    # if so, then we need to ensure jupyterlab starts with the kernel in
    # the virtual environment
    venv.create(env_name, with_pip=True, system_site_packages=False)

    dir_, bin_name = _get_python_folder_and_bin_name()
    path_to_python = str(Path(env_name, dir_, bin_name))

    subprocess.run(
        [path_to_python, '-m', 'pip', 'install', 'pip', '--upgrade'],
        check=True,
        capture_output=True)

    subprocess.run(
        [path_to_python, '-m', 'pip', 'install', 'jupyterlab', '--quiet'] +
        deps,
        check=True,
        capture_output=False)

    print("Lauching Jupyter...")

    if Path(f'{env_name}/bin/jupyter-lab').exists():
        jupyterlab = f'{env_name}/bin/jupyter-lab'
    else:
        jupyterlab = str(Path(sys.prefix, 'bin', 'jupyter-lab'))

    jupyterlab = f'{env_name}/bin/jupyter-lab'

    print('To exit: CTRL + C')

    try:
        subprocess.run([jupyterlab, file], check=True, capture_output=True)
    except KeyboardInterrupt:
        print('Exiting...')
        print(f'\nTo laucnh again:\n\n'
              f'{env_name}/bin/jupyter-lab {file}')
