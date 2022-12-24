import pytest

from k2s.index import ChannelData


@pytest.mark.parametrize(
    "pkgs, not_exist, exist",
    [
        [["some-unknown-package"], ["some-unknown-package"], []],
        [["ploomber==0.21"], [], ["ploomber=0.21"]],
        [["ploomber=0.21"], [], ["ploomber=0.21"]],
    ],
)
def test_pkg_exists(pkgs, not_exist, exist):
    cd = ChannelData()

    exist_res, not_exist_res = cd.pkg_exists(pkgs)
    assert exist_res == exist
    assert not_exist_res == not_exist
