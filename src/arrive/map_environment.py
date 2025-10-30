'''
Overview:

    User's raster or vector data to be visualized on OSM basemap.

Usage:

    from arrive.map_environment import show_on_basemap
    show_on_basemap("data/my_counties.shp")
    show_on_basemap("data/landcover.tif")

'''

from pathlib import Path
from typing import Optional, Tuple, Union, Dict

import matplotlib.pyplot as plt
import contextily as cx
import geopandas as gpd
import rasterio
from rasterio.plot import show as show_raster
from rasterio.warp import transform_bounds

def _load_vector(path: Path) -> gpd.GeoDataFrame:
    '''
    Load a vector file (shapefile, GeoJSON, etc.)
    '''
    gdf = gpd.read_file(path)

    # safe handling of missing CRS:
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)

    # contextily uses Web Mercator tiles == EPSG 3857
    gdf_3857 = gdf.to_crs(epsg=3857)
    return gdf_3857

def _load_raster(path: Path):
    '''
    Load a raster (GeoTIFF) file and return (data, transform, crs3857_bounds, crs3857_affine).
    '''
    src = rasterio.open(path)

    # If the raster != Web Mercator, reprojecting full array is going to be extremely slow.
    # so start by plotting in its native CRS, and only later reproject to 3857.

    return src

def _is_raster(path: Path) -> bool:
    return path.suffix.lower() in {'.tif', '.tiff', '.geotiff'}

def _is_vector(path: Path) -> bool:
    return path.suffix.lower() in {
        '.shp',
        '.geojson',
        '.json',
        '.gpkg',
        '.fgb',
    }

def show_on_basemap(
        data_path: Union[str, Path],
        layer_kwargs: Optional[Dict] = None, ## is this where I want to create the classes?
        figsize: Tuple[int, int] = (10, 10),
        add_attribution: bool = True,
):
    

    '''
    Plot data on top of an OSM-style basemap (contextily)...

    Params:

        data_path: path to vector or raster

        layer_kwargs: dict, optional

            Extra kwargs passed to the plot() call (for vector)
            or rasterio.show (for raster).

            Ex. {"edgecolor": "yellow", "facecolor": "none", "linewidth": 1}
        
        figsize: (int, int)
        
            Figure size in inches.

        add_attribution: bool

            Whether to include the OSM attribution text in the corner (default True).

    Returns:

        fig, ax: matplotlib Figure and Axes

    '''

    path = Path(data_path)

    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}.")
    
    layer_kwargs = layer_kwargs or {}

    if _is_vector(path):

        gdf = _load_vector(path)

        fig, ax = plt.subplots(figsize=figsize)

        # plot user data
        gdf.plot(ax=ax, **layer_kwargs)

        # add basemap under it
        cx.add_basemap(
            ax,
            crs=gdf.crs,
            source=cx.providers.OpenStreetMap.Mapnik,
            attribution=add_attribution,
        )

        # set tight extent
        ax.set_xlim(gdf.total_bounds[0], gdf.total_bounds[2])
        ax.set_ylim(gdf.total_bounds[1], gdf.total_bounds[3])

        ax.set_xlabel("Web Mercator X (meters)")
        ax.set_ylabel("Web Mercator Y (meters)")

        return fig, ax
    
    elif _is_raster(path):

        src = _load_raster(path)

        fig, ax = plt.subplots(figsize=figsize)

        # display raster in native CRS
        show_raster(src, ax=ax, **layer_kwargs)

        # to deal with possible (likely) EPSG mismatch,
        # first get raster bounds in native CRS
        # then transform those to 3857
        # then create "twin Axes" in 3857 for the basemap
        # and finally align the extents, which gives us an approximate location

        raster_crs = src.crs
        left, bottom, right, top = src.bounds

        # transform raster bounds to 3857 bounds,
        # which returns minx, miny, maxx, maxy)
        b3857 = transform_bounds(raster_crs, "EPSG: 3857", left, bottom, right, top)

        # make new axes for basemap (same position, invisible frame)
        ax_basemap = fig.add_axes(ax.get_position(), frameon = False)
        ax_basemap.set_xlim(b3857[0], b3857[2])
        ax_basemap.set_ylim(b3857[1], b3857[3])

        cx.add_basemap(
            ax_basemap,
            crs = 'EPSG: 3857',
            source=cx.providers.OpenStreetMap.Mapnik,
            attribution=add_attribution,
        )

        # We draw basemap first
        # then keep the raster visible on top
        ax.set_zorder(2)
        ax.patch.set_alpha(0)

        src.close()
        return fig, ax
    
    else:
        raise ValueError(
            f"Filetype '{path.suffix}' not recognized. "
            "Supported vectors: .shp .geojson .json .gpkg .fgb; "
            "Supported rasters: .tif .tiff .geotiff"
        )


        
