import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
import urllib.request
from urllib.parse import urlsplit, urlunsplit
from urllib.error import HTTPError

import parso
from isort import place_module

# https://ipython.readthedocs.io/en/stable/config/extensions/index.html
from k2s.env import install
from k2s.index import ChannelData

_BUILT_IN_EXTENSIONS = {'autoreload', 'storemagic'}

_PACKAGE_MAPPING = {
    'sklearn': 'scikit-learn',
    'sql': 'jupysql',
}


# FIXME: downloaded files might depend on other files, so we have to download
# them as well
def download_files(source, url):
    files = local_files(source)

    split = urlsplit(url)
    split = split._replace(path=str(PurePosixPath(split.path).parent))
    base = urlunsplit(split)

    deps = set()

    # TODO: download in parallel
    for file in files:
        try:
            # TODO: if .py or .ipynb, there might be more packages to install
            urllib.request.urlretrieve(f'{base}/{file}', file)
            print(f'Downloaded filed used in notebook: {file}')

            if Path(file).suffix == '.py':
                deps_ = extract_imports_from_path_to_script(file)
                deps = deps | set(deps_)
            elif Path(file).suffix == '.ipynb':
                deps_ = extract_imports_from_path_to_notebook(file)
                deps = deps | set(deps_)

        except HTTPError as e:
            print("It appears the notebook is using "
                  f"a file named {file!r}, but downloading it failed: {e}")

    return deps


def _get_previous_leaf(leaf, *, levels):

    for _ in range(levels):
        leaf = leaf.get_previous_leaf()

        if leaf is None:
            return None

    return leaf


def local_files(source):
    """
    Given some source code, infer what files are used as inputs. For example,
    calls to .read, .read_* functions, or calls to pathlib.Path
    """
    # nbformat.read("notebook.ipynb") or jupytext.read("notebook.ipynb")
    # Path("file.txt")
    # pd.read_{fmt}("path.ext")
    # look for calls to these functions
    targets = {'read', 'Path'}

    # TODO: ploomber-specific: pipeline.yaml (DAGSpec.find())
    # or ploomber build

    # TODO: ignore things like s3://

    def evaluator(leaf):
        is_string = leaf.type == 'string'

        if not is_string:
            return False

        prev = leaf.get_previous_leaf()

        if prev.type == 'operator' and prev.value == '=':
            prev = _get_previous_leaf(leaf, levels=4)
        else:
            prev = _get_previous_leaf(leaf, levels=2)

        if prev is None:
            return is_string

        return prev.value in targets or (prev.value.startswith('read_')
                                         and prev.value != 'read_sql')

    return string_literals(source, evaluator=evaluator)


def paths(source, *, raw=False):
    """
    Given some source code, parse string literals that look like paths
    """

    def evaluator(leaf):
        is_string = leaf.type == 'string'

        if not is_string:
            return False

        value = leaf.value

        constructor = (PureWindowsPath
                       if ':' in value or '\\' in value else PurePosixPath)

        path = constructor(value)

        return len(path.parts) >= 2 or path.suffix

    return string_literals(source, evaluator=evaluator, raw=raw)


def string_literals(source, *, evaluator=None, raw=False):
    """Find string literals in the source code

    Parameters
    ----------
    source : str
        Source code

    evaluator : callable
        A function that returns true if the leaf should be ocnsidered a
        candidate or not
    """
    if evaluator is None:

        def evaluator(leaf):
            return leaf.type == 'string'

    mod = parso.parse(source)

    leaf = mod.get_first_leaf()

    literals = []

    while leaf:
        if evaluator(leaf):
            if raw:
                value = leaf.value
            else:
                value = leaf.value[1:-1]

            literals.append(value)

        leaf = leaf.get_next_leaf()

    return set(literals)


def extract_from_plain_text(text):
    # NOTE: +, :, /, and . are also required since users may have something
    # like: pip install git+https://github.com/ploomber/ploomber
    # we ignore those requirements but we need to parse them
    matches = re.findall(r'pip install ([\w \-\+\:\/\.]+)', text)
    matches

    deps = set([
        item for sublist in [match.split() for match in matches]
        for item in sublist
        # ignore options passed to "pip install"
        if not item.startswith('-')
        # ignore git+URL and similar:
        # https://pip.pypa.io/en/stable/topics/vcs-support/
        if '+' not in item
    ])
    return list(deps - {'k2s'})


# NOTE: imports might also be from local files, so we should download them
# NOTE: we copied this from soorgeon
# https://github.com/ploomber/soorgeon/blob/cb16dc51f326cf21486bff86dfec03b4d1f5c2d7/src/soorgeon/definitions.py#L24
def packages_used(tree):
    """
    Return a list of the packages used, correcting for some packages whose
    module name does not match the PyPI package (e.g., sklearn -> scikit-learn)
    Returns None if fails to parse them
    """

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
        _PACKAGE_MAPPING.get(name, name) for name in pkgs
        if place_module(name) == 'THIRDPARTY'
    ]

    # parse magics
    leaf = tree.get_first_leaf()

    while leaf:
        if leaf.value == '%' and leaf.get_next_leaf().value == 'load_ext':
            ext_name = leaf.get_next_leaf().get_next_leaf().value
            if ext_name not in _BUILT_IN_EXTENSIONS:
                pkgs_final.append(_PACKAGE_MAPPING.get(ext_name, ext_name))

        leaf = leaf.get_next_leaf()

    # remove duplicates and sort
    return sorted(set(pkgs_final))


def extract_code(nb):
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

    return code


def to_text(nb):
    try:
        plain = '\n'.join([cell['source'] for cell in nb['cells']])
    except TypeError:
        # # if passed a notebook read using json instead of nbformat
        plain = '\n'.join(['\n'.join(c['source']) for c in nb['cells']])

    return plain


def extract_imports_from_path_to_notebook(path):
    nb = json.loads(Path(path).read_text(encoding='utf-8'))
    return extract_imports_from_notebook(nb)


def extract_imports_from_path_to_script(path):
    code = Path(path).read_text()
    return packages_used(parso.parse(code)) + extract_from_plain_text(code)


def extract_imports_from_notebook(nb):
    code = extract_code(nb)
    # TODO: maybe use the notebook's JSON string? cause here we're ignoring
    # code cells that might have comments such as "pip install something"
    plain = to_text(nb)

    return packages_used(parso.parse(code)) + extract_from_plain_text(plain)


def bootstrap_env(path_to_notebook, name=None, verbose=False):
    # TODO: maybe print "remember to click on save?" - if users edit the
    # notebook but do not save, we won't see their changes
    import nbformat

    if name is None:
        print("name not supplied, installing in the current environment...")

    print('Parsing notebook...')
    nb = nbformat.read(path_to_notebook, as_version=nbformat.NO_CONVERT)
    imports = set(extract_imports_from_notebook(nb)) | {'k2s'}

    cd = ChannelData()
    conda, pip = cd.pkg_exists(imports)

    print(f'Found: {", ".join(imports)}')

    install(name, conda, requirements_pip=pip, verbose=verbose)

    # if installed in a new env, we need to refresh jupyter for the new kernel
    # to appear
    # TODO: only say "switch" to if on a different kernel
    if name is not None:
        print('Kernel is ready! Refresh your browser and switch '
              f'the kernel to: {name}')

    nb.metadata.kernelspec = {
        'display_name': f'Python 3 ({name})',
        'language': 'python',
        'name': name,
    }

    # override kernel spec - note that refreshing won't switch to this
    # kernel and it'll stick with the original one until we kill the
    # existing kernel
    Path(path_to_notebook).write_text(nbformat.v4.writes(nb))
