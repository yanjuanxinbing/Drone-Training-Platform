# Vendored AirSim client — preserved from the original project.
# Importing the package gives you `airsim.MultirotorClient`, `airsim.ImageType`,
# etc., matching the upstream `airsim` PyPI package.
from . import client as _client
from . import types as _types
from . import utils as _utils

# Re-export common symbols so `import airsim` from drone_controller works.
MultirotorClient = _client.MultirotorClient
ImageType = _types.ImageType
DrivetrainType = _types.DrivetrainType
YawMode = _types.YawMode

__all__ = ["MultirotorClient", "ImageType", "DrivetrainType", "YawMode"]