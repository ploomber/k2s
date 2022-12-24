import pytest

from jupyter_client import KernelManager
from k2s import env


@pytest.mark.skip
def test_install():
    env.install("some-env", ["scikit-learn", "pandas"])

    # ensure the new kernel works
    km = KernelManager(kernel_name="some-env")
    km.start_kernel()
    kc = km.client()
    kc.start_channels()
    kc.wait_for_ready()

    kc.execute("import pandas as pd; import sklearn")
    out = kc.get_shell_msg(timeout=3)

    assert out["content"]["status"] == "ok"

    kc.shutdown()
