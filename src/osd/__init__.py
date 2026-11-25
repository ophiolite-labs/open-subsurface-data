"""Open Subsurface Data tools: validate records, verify origins, build the catalogue.

From Python (E49): `import osd; norne = osd.get("opm/norne")` fetches a dataset's files, checked
(`osd.api.get`; the `osd.get` module is callable). Importing `osd` reads nothing from the network.
"""

__version__ = "0.1.0"

from . import get
from .api import ChecksumMismatch, Dataset, DatasetError, File

__all__ = ["ChecksumMismatch", "Dataset", "DatasetError", "File", "__version__", "get"]
