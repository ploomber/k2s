"""
pip install k2s --upgrade && k2s get ploomber/jupysql/doc/nb.ipynb
"""
import os
import json
from pathlib import Path, PurePosixPath
import subprocess
import venv
import urllib.request

from k2s.parse import extract_imports


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

    path_to_python = path_to_bin(env_name, 'python')

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

    # TODO: if jupyter lab is already installed, we can use it (and skip
    # installation), but we have to make sure that the kernel used is
    # the one in the venv, not in the parent env
    path_to_jupyterlab = path_to_bin(env_name, 'jupyter-lab')

    print('To exit: CTRL + C')

    try:
        subprocess.run([path_to_jupyterlab, file],
                       check=True,
                       capture_output=True)
    except KeyboardInterrupt:
        print('Exiting...')
        print(f'\nTo laucnh again:\n\n'
              f'{path_to_jupyterlab} {file}')
