import urllib.request
from pathlib import Path
import json


class ChannelData:
    """Get conda-forge channel data
    """

    def __init__(self):
        self._data = self.load_channel_data()

    def load_channel_data(self):
        home = Path('~', '.k2s').expanduser()
        if not home.exists():
            home.mkdir()

        target = home / "conda-forge.json"

        urllib.request.urlretrieve(
            "https://conda.anaconda.org/conda-forge/channeldata.json", target)

        data = json.loads(target.read_text())

        return data

    def pkg_exists(self, names):
        exist, not_exist = [], []

        for name in names:
            if self._data['packages'].get(name):
                exist.append(name)
            else:
                not_exist.append(name)

        return exist, not_exist
