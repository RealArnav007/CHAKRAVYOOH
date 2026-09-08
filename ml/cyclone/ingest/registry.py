"""Central factory and registry for all Chakravyuh data source loaders."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from ml.cyclone.ingest.era5 import open_era5, sample_env
from ml.cyclone.ingest.ibtracs import get_storm, load_tracks
from ml.cyclone.ingest.satellite import load_image_index, read_image


LOADER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ibtracs": {
        "description": "NOAA IBTrACS best-track historical trajectory dataset",
        "load": load_tracks,
        "get_storm": get_storm,
    },
    "satellite": {
        "description": "Multi-source geostationary satellite IR imagery index",
        "load": load_image_index,
        "read_image": read_image,
    },
    "drivendata": {
        "description": "DrivenData Tropical Cyclone Wind Speed Benchmark",
        "load": lambda **kw: load_image_index(source="drivendata", **kw),
        "read_image": read_image,
    },
    "digital_typhoon": {
        "description": "Digital Typhoon Geostationary Satellite Archive (NII Japan)",
        "load": lambda **kw: load_image_index(source="digital_typhoon", **kw),
        "read_image": read_image,
    },
    "era5": {
        "description": "ERA5 atmospheric and ocean surface reanalysis",
        "open": open_era5,
        "sample": sample_env,
    },
}


def list_sources() -> List[str]:
    """Returns a list of all registered dataset source identifiers."""
    return list(LOADER_REGISTRY.keys())


def get_loader(source: str) -> Dict[str, Any]:
    """Retrieves the loader interface dictionary for a registered source.

    Args:
        source: Name of source ('ibtracs', 'satellite', 'drivendata', 'digital_typhoon', 'era5')

    Returns:
        Dictionary containing loader functions ('load', 'read_image', 'open', 'sample')

    Raises:
        KeyError: If source is not in LOADER_REGISTRY.
    """
    source_key = source.lower().strip()
    if source_key not in LOADER_REGISTRY:
        raise KeyError(
            f"Source '{source}' is not registered. Available sources: {list_sources()}"
        )
    return LOADER_REGISTRY[source_key]


def load_dataset(source: str, **kwargs) -> Any:
    """Convenience helper to directly load dataset by source name."""
    loader_dict = get_loader(source)
    if "load" in loader_dict:
        return loader_dict["load"](**kwargs)
    raise AttributeError(f"Source '{source}' does not support direct 'load()' call.")


__all__ = ["list_sources", "get_loader", "load_dataset", "LOADER_REGISTRY"]
