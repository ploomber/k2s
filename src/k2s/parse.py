import re
import sys
from pathlib import Path

import parso
from isort import place_module

from k2s.env import install


def extract_from_plain_text(text):
    matches = re.findall(r'pip install ([\w \-]+)', text)
    deps = set([
        item for sublist in [match.split() for match in matches]
        for item in sublist if not item.startswith('-')
    ])
    return list(deps - {'k2s'})


# NOTE: we copied this from soorgeon
# https://github.com/ploomber/soorgeon/blob/cb16dc51f326cf21486bff86dfec03b4d1f5c2d7/src/soorgeon/definitions.py#L24
def packages_used(tree):
    """
    Return a list of the packages used, correcting for some packages whose
    module name does not match the PyPI package (e.g., sklearn -> scikit-learn)
    Returns None if fails to parse them
    """

    pkg_name = {
        'sklearn': 'scikit-learn',
        'sql': 'jupysql',
    }

    def flatten(elements):
        return [i for sub in elements for i in sub]

    def _extract_names(node):
        if hasattr(node, 'children'):
            return extract_names(node.children[0])
        else:
            return [node.value]

    def extract_names(import_):
        if import_.type == 'name':
            return [import_.value]
        elif import_.type in {'dotted_name', 'dotted_as_name'}:
            return [import_.children[0].value]

        second = import_.children[1]

        if second.type in {'dotted_name', 'dotted_as_name'}:
            return extract_names(second.children[0])
        elif second.type == 'dotted_as_names':
            # import a as something, b as another

            return flatten([
                _extract_names(node) for i, node in enumerate(second.children)
                if i % 2 == 0
            ])
        else:
            return [second.value]

    pkgs = flatten([extract_names(import_) for import_ in tree.iter_imports()])

    # replace using pkg_name mapping and ignore standard lib
    pkgs_final = [
        pkg_name.get(name, name) for name in pkgs
        if place_module(name) == 'THIRDPARTY'
    ]

    # remove duplicates and sort
    return sorted(set(pkgs_final))


def extract_imports(nb):

    try:
        code = '\n'.join([
            cell['source'] for cell in nb['cells']
            if cell['cell_type'] == "code"
        ])
    except TypeError:
        # if passed a notebook read using json instead of nbformat
        code = '\n'.join([
            '\n'.join(c['source']) for c in nb['cells']
            if c['cell_type'] == 'code'
        ])

    try:
        plain = '\n'.join([cell['source'] for cell in nb['cells']])
    except TypeError:
        # # if passed a notebook read using json instead of nbformat
        plain = '\n'.join(['\n'.join(c['source']) for c in nb['cells']])

    return packages_used(parso.parse(code)) + extract_from_plain_text(plain)


def bootstrap_env(path_to_notebook, inline=False, verbose=False):
    import nbformat

    if inline:
        name = Path(sys.prefix).name
    else:
        name = Path(path_to_notebook).stem

    print('Parsing notebook...')
    nb = nbformat.read(path_to_notebook, as_version=nbformat.NO_CONVERT)
    imports = extract_imports(nb)
    imports = set(imports) - {'k2s'}
    imports_str = ', '.join(imports)
    print(f'Found: {imports_str}. Installing...')

    install(name, imports, verbose=verbose, inline=inline)

    if not inline:
        print('Kernel is ready! Refresh your browser')

    nb.metadata.kernelspec = {
        'display_name': f'Python 3 ({name})',
        'language': 'python',
        'name': name,
    }

    # override kernel spec - note that refreshing won't switch to this
    # kernel and it'll stick with the original one until we kill the existing
    # kernel
    Path(path_to_notebook).write_text(nbformat.v4.writes(nb))
