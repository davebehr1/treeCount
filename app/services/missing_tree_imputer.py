import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from scipy.spatial import cKDTree
from pyproj import Transformer
from matplotlib.patches import Polygon as MplPolygon
from typing import List, Tuple


class MissingTreeImputer:
    def __init__(self):
        """
        These coordinate transformers are necessary to work with the KD-tree data structure used in the 
        __generate_candidates method, and to transform missing coordinates back to longitude and latitude.

        EPSG:4326 is a coordinate system in longitude and latitude.
        EPSG:3857 is the Web Mercator projection with a coordinate system in meters.
        """
        self.to_meters = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        self.to_latlon = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    def impute_missing_tree_coords(self,orchard_polygon: Polygon, locations: list, orchard_id: int) -> List[Tuple[float, float]]:
        longitudes = [loc[0] for loc in locations]
        latitudes = [loc[1] for loc in locations]
        areas = [loc[2] for loc in locations]

        polygon_coords = list(orchard_polygon.exterior.coords)
        polygon_coords_m = [self.to_meters.transform(lon, lat) for lon, lat in polygon_coords]


        radii = [np.sqrt(area / np.pi) for area in areas]
        tree_radius = np.max(radii)
        min_tree_radius = np.min(radii)
        bounding_polygon = Polygon(polygon_coords_m)


        safe_polygon = bounding_polygon.buffer(-min_tree_radius*2)

        tree_coords_m = [self.to_meters.transform(lon, lat) for lon, lat in zip(longitudes, latitudes)]
        kd_tree = cKDTree(tree_coords_m)

        new_trees = self.__generate_candidates(tree_radius, safe_polygon, kd_tree, tree_coords_m)

        new_tree_locations = [self.to_latlon.transform(x, y) for (x, y) in new_trees]

        self.__save_orchard_plot(orchard_polygon,safe_polygon, longitudes, latitudes, new_tree_locations,areas, orchard_id)

        return new_tree_locations


    def __generate_candidates(self,tree_radius: float, 
                                    safe_polygon: Polygon, 
                                    kd_tree: cKDTree, 
                                    tree_coords_m: List[Tuple[float, float]]) -> list:
        """
        This method generates new candidate trees by iterating over all tree coordinates and efficiently calculating their nearest neighbors 
        using a KD-tree data structure, which serves as a spatial index. It then examines the midpoints between neighboring trees 
        to determine whether each midpoint lies within the polygon boundary and whether it is an empty space. 
        This is done by querying the KD-tree for nearby trees. 
        If a valid empty space is found, a new tree is inserted and added to a new KD-tree to keep track of new trees, 
        ensuring that newly placed trees do not overlap.
        """
        new_trees = []

        new_trees_kd_tree = None

        for i, (x1, y1) in enumerate(tree_coords_m):

            neighbors = kd_tree.query_ball_point([x1, y1], r=15 * tree_radius) 
            
            for j in neighbors:
                if i >= j:
                    continue
                
                
                x2, y2 = tree_coords_m[j]
                midpoint_x = (x1 + x2) / 2
                midpoint_y = (y1 + y2) / 2
                pt = Point(midpoint_x, midpoint_y)

                
                if not safe_polygon.contains(pt.buffer(tree_radius)):
                    continue

                nearby_tree_idxs = kd_tree.query_ball_point([midpoint_x, midpoint_y], r=2 * tree_radius)
                if nearby_tree_idxs:
                    continue

                if new_trees_kd_tree is not None:
                    nearby_points = new_trees_kd_tree.query_ball_point([midpoint_x, midpoint_y], r=2 * tree_radius)
                    if len(nearby_points) > 0:
                        continue

                new_trees.append((midpoint_x, midpoint_y))
                
                new_trees_kd_tree = cKDTree(new_trees)

        return new_trees


    def __save_orchard_plot(self,orchard_polygon: Polygon,safe_polygon: Polygon, longitudes: List[float], latitudes: List[float], 
                        new_trees_latlon: List[Tuple[float, float]],areas: List[float],
                        orchard_id: int):

        _, ax = plt.subplots(figsize=(10, 9))


        polygon_coords = list(orchard_polygon.exterior.coords)
        polygon_patch = MplPolygon(polygon_coords, closed=True, edgecolor='blue', facecolor='none', linewidth=2, label='Orchard Boundary')
        ax.add_patch(polygon_patch)

        safe_coords_latlon = [self.to_latlon.transform(x, y) for x, y in safe_polygon.exterior.coords]
        safe_polygon_patch = MplPolygon(safe_coords_latlon, closed=True, edgecolor='red', facecolor='none',linestyle='--', linewidth=2, label='Safe Orchard Boundary')
        ax.add_patch(safe_polygon_patch)

        scale_factor = 10
        marker_sizes = [area * scale_factor for area in areas]
        ax.scatter(longitudes, latitudes, s=marker_sizes, c='green', alpha=0.6, edgecolors='k', label='Existing Trees')

        if new_trees_latlon:
            new_lons, new_lats = zip(*new_trees_latlon)
            ax.scatter(new_lons, new_lats, c='red', s=100, alpha=0.6, edgecolors='k', label='New Trees')

        ax.set_title(f"Possible locations for planting new trees")
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.grid(False)
        ax.legend()

        save_path = f'plots/plot_{orchard_id}.png'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, format='png', bbox_inches='tight', dpi=300)
        plt.close()

