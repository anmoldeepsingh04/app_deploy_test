import random
import math
import numpy as np
from scipy import ndimage
from sklearn.cluster import KMeans

from .base import BaseSimulator
from .constants import COLORS

# ==================== GENERALIZED STEEL (2.06-6.67%C) ====================
class GeneralizedSteel(BaseSimulator):
    def __init__(self, carbon_percent=2.06, width=500, height=400, n_grains=50, seed=42):
        super().__init__()
        self.carbon_percent = carbon_percent
        self.width = width
        self.height = height
        self.seed = seed

        if carbon_percent < 4.3:
            self.steel_type = 'hypoeutectoid'
            C = carbon_percent
            self.liquid_to_austenite_temp = 0.325201*C**3 - 5.168028*C**2 - 75.120496*C + 1538.747373
            self.liquidus_temp = self.liquid_to_austenite_temp + 50
            self.austenite_start_temp = self.liquid_to_austenite_temp - 50
            self.large_grains_type = 'austenite'
        elif carbon_percent == 4.3:
            self.steel_type = 'eutectoid'
            self.liquidus_temp = 1147
            self.large_grains_type = None
        else:
            self.steel_type = 'hypereutectoid'
            C = carbon_percent
            self.liquid_to_cementite_temp = -19.714*C**3 + 313.032*C**2 - 1554.375*C + 3610.368
            self.liquidus_temp = self.liquid_to_cementite_temp + 50
            self.cementite_start_temp = self.liquid_to_cementite_temp - 50
            self.large_grains_type = 'cementite'

        self.eutectic_temp = 1147
        self.eutectoid_temp = 723

        self.original_grain_map = self._create_high_density_grain_structure(width, height, n_grains, seed)
        self.unique_grains = np.unique(self.original_grain_map)
        self.n_grains = len(self.unique_grains)

        if self.steel_type != 'eutectoid':
            self.large_grain_ids = self._select_interior_grains_for_enlargement(6)
        else:
            self.large_grain_ids = np.array([])

        self.liquid_color = COLORS['liquid']
        self.austenite_color = COLORS['austenite']
        self.proeutectoid_ferrite_color = COLORS['proeutectoid_ferrite']
        self.proeutectoid_cementite_color = COLORS['cementite_bulk']
        self.ferrite_in_pearlite_color = COLORS['pearlite_ferrite']
        self.cementite_in_pearlite_color = COLORS['pearlite_cementite']
        self.grain_boundary_color = COLORS['grain_boundary']
        self.background_color = COLORS['background']

        self.cementite_color = self.proeutectoid_cementite_color
        self.cementite_boundary_color = self.grain_boundary_color

        self.current_grain_maps = {}
        self.shrunk_grain_map_1147 = self._create_mixed_shrunk_grains()
        self.grain_boundaries = self._get_grain_boundaries(self.shrunk_grain_map_1147)
        self._precompute_pearlite_transformation_order()
        self._select_fixed_cementite_positions()

    def _select_fixed_cementite_positions(self):
        random.seed(self.seed)
        self.cementite_positions = []
        background = (self.shrunk_grain_map_1147 == -1)
        bg_y, bg_x = np.where(background)
        bg_coords = list(zip(bg_x, bg_y))
        if len(bg_coords) < 5:
            bg_coords = [(x, y) for x in range(50, self.width-50, 50)
                         for y in range(50, self.height-50, 50)]
        n_cementite = 5
        attempts = 0
        max_attempts = 100
        while len(self.cementite_positions) < n_cementite and attempts < max_attempts:
            attempts += 1
            if bg_coords:
                x, y = random.choice(bg_coords)
                valid = True
                for existing in self.cementite_positions:
                    dist = np.sqrt((x - existing['x'])**2 + (y - existing['y'])**2)
                    if dist < 60:
                        valid = False
                        break
                if valid:
                    size = random.randint(7, 8)
                    self.cementite_positions.append({'x': x, 'y': y, 'size': size})
        if len(self.cementite_positions) < n_cementite:
            zones = [
                (self.width//6, self.width//3, self.height//6, self.height//3),
                (2*self.width//3, 5*self.width//6, self.height//6, self.height//3),
                (2*self.width//3, 5*self.width//6, 2*self.height//3, 5*self.height//6),
                (self.width//3, 2*self.width//3, self.height//3, 2*self.height//3)
            ]
            for xmin, xmax, ymin, ymax in zones:
                if len(self.cementite_positions) >= n_cementite:
                    break
                x = (xmin + xmax) // 2
                y = (ymin + ymax) // 2
                size = random.randint(7, 8)
                self.cementite_positions.append({'x': x, 'y': y, 'size': size})

    def _draw_cementite_grains(self, micro, allowed_mask):
        h, w = allowed_mask.shape
        for cem in self.cementite_positions:
            x, y, sz = cem['x'], cem['y'], cem['size']
            if not (0 <= x < w and 0 <= y < h):
                continue
            for dx in range(-sz, sz+1):
                for dy in range(-sz, sz+1):
                    xi, yi = x+dx, y+dy
                    if 0 <= xi < w and 0 <= yi < h and dx*dx + dy*dy <= sz*sz:
                        if allowed_mask[yi, xi]:
                            micro[yi, xi] = self.cementite_color
            for dx in range(-sz-1, sz+2):
                for dy in range(-sz-1, sz+2):
                    xi, yi = x+dx, y+dy
                    if 0 <= xi < w and 0 <= yi < h:
                        d2 = dx*dx + dy*dy
                        if (sz+0.5)**2 < d2 <= (sz+1.5)**2:
                            if allowed_mask[yi, xi] and np.array_equal(micro[yi, xi], self.cementite_color):
                                micro[yi, xi] = self.cementite_boundary_color

    def _create_high_density_grain_structure(self, width, height, n_grains, seed):
        np.random.seed(seed)
        Y, X = np.mgrid[:height, :width]
        coordinates = np.column_stack((X.ravel(), Y.ravel()))
        n_samples = min(15000, width * height)
        sample_indices = np.random.choice(coordinates.shape[0], n_samples, replace=False)
        samples = coordinates[sample_indices]
        kmeans = KMeans(n_clusters=n_grains, random_state=seed, n_init=1)
        kmeans.fit(samples)
        labels = kmeans.predict(coordinates)
        return labels.reshape(height, width)

    def _select_interior_grains_for_enlargement(self, n_large=6):
        boundary_mask = np.zeros((self.height,self.width), dtype=bool)
        thick = 40
        boundary_mask[:thick,:] = True
        boundary_mask[-thick:,:] = True
        boundary_mask[:,:thick] = True
        boundary_mask[:,-thick:] = True
        interior = []
        for gid in self.unique_grains:
            mask = (self.original_grain_map == gid)
            if not np.any(mask & boundary_mask):
                if np.sum(mask) > 100:
                    interior.append(gid)
        if len(interior) < n_large:
            interior = list(self.unique_grains)
        selected = []
        remaining = interior.copy()
        while len(selected) < n_large and remaining:
            centers = []
            for g in selected:
                ym, xm = np.where(self.original_grain_map == g)
                if len(ym)>0:
                    centers.append((np.mean(ym), np.mean(xm)))
            dists = []
            for g in remaining:
                ym, xm = np.where(self.original_grain_map == g)
                if len(ym)==0: continue
                center = (np.mean(ym), np.mean(xm))
                if not centers:
                    mindist = float('inf')
                else:
                    mindist = min(np.sqrt((center[0]-c[0])**2 + (center[1]-c[1])**2) for c in centers)
                size = np.sum(self.original_grain_map == g)
                dists.append((g, mindist, size))
            if not dists: break
            dists.sort(key=lambda x: (x[1], -x[2]), reverse=True)
            selected.append(dists[0][0])
            remaining.remove(dists[0][0])
        return np.array(selected[:n_large])

    def _create_mixed_shrunk_grains(self):
        if self.steel_type == 'eutectoid':
            mixed = self.original_grain_map.copy()
            occupied = np.zeros((self.height,self.width), dtype=bool)
            struct = np.ones((3,3))
            for gid in self.unique_grains:
                mask = (self.original_grain_map == gid)
                rng = np.random.RandomState(gid)
                iters = rng.randint(8,12)
                eroded = ndimage.binary_erosion(mask, struct, iterations=iters)
                eroded = ndimage.binary_fill_holes(eroded) & ~occupied
                if np.any(eroded):
                    mixed[eroded] = gid
                    occupied |= eroded
                    mixed[mask & ~eroded] = -1
                else:
                    mixed[mask] = -1
            mixed[~occupied] = -1
            return mixed
        else:
            mixed = self.original_grain_map.copy()
            occupied = np.zeros((self.height,self.width), dtype=bool)
            struct = np.ones((3,3))
            large_struct = np.ones((7,7))
            for gid in self.large_grain_ids:
                mask = (self.original_grain_map == gid)
                rng = np.random.RandomState(gid)
                eroded = mask.copy()
                eroded = ndimage.binary_fill_holes(eroded)
                dilated = ndimage.binary_dilation(eroded, struct, iterations=6)
                dilated = ndimage.binary_dilation(dilated, large_struct, iterations=3)
                dilated = ndimage.binary_dilation(dilated, np.ones((5,5)), iterations=2)
                dilated = ndimage.binary_fill_holes(dilated) & ~occupied
                if np.any(dilated):
                    mixed[dilated] = gid
                    occupied |= dilated
                    mixed[mask & ~dilated] = -1
            for gid in self.unique_grains:
                if gid in self.large_grain_ids: continue
                mask = (self.original_grain_map == gid)
                rng = np.random.RandomState(gid)
                iters = rng.randint(8,12)
                eroded = ndimage.binary_erosion(mask, struct, iterations=iters)
                eroded = ndimage.binary_fill_holes(eroded) & ~occupied
                if np.any(eroded):
                    mixed[eroded] = gid
                    occupied |= eroded
                    mixed[mask & ~eroded] = -1
                else:
                    mixed[mask] = -1
            mixed[~occupied] = -1
            return mixed

    def _get_grain_boundaries(self, grain_map):
        boundary = np.zeros_like(grain_map, dtype=bool)
        for shift in [1,-1]:
            boundary |= (grain_map != np.roll(grain_map, shift, axis=0))
            boundary |= (grain_map != np.roll(grain_map, shift, axis=1))
        return boundary

    def _precompute_pearlite_transformation_order(self):
        if self.steel_type == 'hypereutectoid':
            consider = [g for g in self.unique_grains if g not in self.large_grain_ids]
        else:
            consider = self.unique_grains
        sizes = []
        for g in consider:
            sz = np.sum(self.shrunk_grain_map_1147 == g)
            if sz > 0:
                sizes.append((g, sz))
        sizes.sort(key=lambda x: x[1], reverse=True)
        self.pearlite_transformation_order = [g for g,s in sizes]
        self.n_transformable_grains = len(self.pearlite_transformation_order)

    def _add_pearlite_to_grain(self, micro, grain_id):
        mask = (self.shrunk_grain_map_1147 == grain_id)
        if np.sum(mask) < 8: return
        ys, xs = np.where(mask)
        if len(xs)==0: return
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        region = mask[ymin:ymax+1, xmin:xmax+1]
        Yg, Xg = np.where(region)
        if len(Xg)==0: return
        spacing = 2.0
        angle = 45
        theta = np.deg2rad(angle)
        cy, cx = np.mean(Yg), np.mean(xs)
        Yc = Yg - cy
        Xc = Xg - cx
        U = Xc*np.cos(theta) + Yc*np.sin(theta)
        phase = (np.floor(U/spacing)).astype(int) % 2
        cem = (phase == 0)
        fer = (phase == 1)
        cyy = Yg[cem] + ymin
        cxx = Xg[cem] + xmin
        fyy = Yg[fer] + ymin
        fxx = Xg[fer] + xmin
        valid_cem = (cxx < micro.shape[1]) & (cyy < micro.shape[0])
        valid_fer = (fxx < micro.shape[1]) & (fyy < micro.shape[0])
        micro[cyy[valid_cem], cxx[valid_cem]] = self.cementite_in_pearlite_color
        micro[fyy[valid_fer], fxx[valid_fer]] = self.ferrite_in_pearlite_color

    def get_transformation_state(self, temperature):
        if self.steel_type == 'hypoeutectoid':
            if temperature > self.liquidus_temp:
                return {'phase':'liquid','description':'Liquid (L)','liquid_fraction':1.0,
                        'austenite_fraction':0.0,'pearlite_fraction':0.0,
                        'grains_visible':False,'large_grains_type':'austenite'}
            elif temperature > self.austenite_start_temp:
                frac = (self.liquidus_temp - temperature)/(self.liquidus_temp - self.austenite_start_temp)
                frac = max(0, min(frac, 0.3))
                return {'phase':'austenite_forming','description':'L + γ (austenite)',
                        'liquid_fraction':1.0-frac,'austenite_fraction':frac,
                        'pearlite_fraction':0.0,
                        'grains_visible':True,'only_large_grains':True,'large_grains_type':'austenite'}
            elif temperature > self.eutectic_temp:
                if temperature >= 1300: af = 0.7
                elif temperature >= 1200: af = 0.85
                else: af = 0.95
                return {'phase':'austenite_liquid','description':'L + γ (austenite)',
                        'liquid_fraction':1.0-af,'austenite_fraction':af,
                        'pearlite_fraction':0.0,
                        'grains_visible':True,'only_large_grains':True,'all_grains':False,
                        'large_grains_type':'austenite'}
        elif self.steel_type == 'hypereutectoid':
            if temperature > self.liquidus_temp:
                return {'phase':'liquid','description':'Liquid (L)','liquid_fraction':1.0,
                        'cementite_fraction':0.0,'pearlite_fraction':0.0,
                        'grains_visible':False,'large_grains_type':'cementite'}
            elif temperature > self.cementite_start_temp:
                frac = (self.liquidus_temp - temperature)/(self.liquidus_temp - self.cementite_start_temp)
                frac = max(0, min(frac, 0.3))
                return {'phase':'cementite_forming','description':'L + Fe₃C',
                        'liquid_fraction':1.0-frac,'cementite_fraction':frac,
                        'pearlite_fraction':0.0,
                        'grains_visible':True,'only_large_grains':True,'large_grains_type':'cementite'}
            elif temperature > self.eutectic_temp:
                if temperature >= 1300: cf = 0.7
                elif temperature >= 1200: cf = 0.85
                else: cf = 0.95
                return {'phase':'cementite_liquid','description':'L + Fe₃C',
                        'liquid_fraction':1.0-cf,'cementite_fraction':cf,
                        'pearlite_fraction':0.0,
                        'grains_visible':True,'only_large_grains':True,'all_grains':False,
                        'large_grains_type':'cementite'}
        elif self.steel_type == 'eutectoid':
            if temperature > self.eutectic_temp:
                return {'phase':'liquid','description':'Liquid (L)','liquid_fraction':1.0,
                        'austenite_fraction':0.0,'pearlite_fraction':0.0,
                        'grains_visible':False,'large_grains_type':None}
        if temperature == self.eutectic_temp:
            if self.steel_type == 'eutectoid':
                desc = 'Ledeburite'
            elif self.steel_type == 'hypoeutectoid':
                desc = 'Austenite (γ) + Ledeburite I + Fe₃C II'
            else:
                desc = 'Ledeburite I + Fe₃C I'
            return {'phase':'all_grains_appear','description':desc,'liquid_fraction':0.0,
                    'austenite_fraction':1.0 if self.steel_type!='hypereutectoid' else 0.0,
                    'cementite_fraction':1.0 if self.steel_type=='hypereutectoid' else 0.0,
                    'pearlite_fraction':0.0,'grains_visible':True,
                    'only_large_grains':False,'all_grains':True,'white_background':True,
                    'large_grains_type':self.large_grains_type}
        elif temperature >= self.eutectoid_temp:
            if self.steel_type == 'hypereutectoid':
                desc = 'Ledeburite I + Fe₃C I'
            elif self.steel_type == 'hypoeutectoid':
                desc = 'Austenite (γ) + Ledeburite I + Fe₃C II'
            else:
                desc = 'Ledeburite'
            return {'phase':'ledeburite','description':desc,'liquid_fraction':0.0,
                    'austenite_fraction':1.0 if self.steel_type!='hypereutectoid' else 0.0,
                    'cementite_fraction':1.0 if self.steel_type=='hypereutectoid' else 0.0,
                    'pearlite_fraction':0.0,'grains_visible':True,
                    'all_grains':True,'white_background':True,'large_grains_type':self.large_grains_type}
        else:
            under = self.eutectoid_temp - temperature
            if temperature == self.eutectoid_temp: pfrac = 0.0
            elif under < 50: pfrac = min(0.95, under/50)
            else: pfrac = min(0.98, 0.95 + (under-50)/200)
            if self.steel_type == 'hypereutectoid':
                desc = 'Ledeburite II + Fe₃C I'
            elif self.steel_type == 'hypoeutectoid':
                desc = 'Pearlite + Ledeburite II + Fe₃C II'
            else:
                desc = 'Pearlite'
            return {'phase':'pearlite_forming','description':desc,'liquid_fraction':0.0,
                    'austenite_fraction':1.0-pfrac if self.steel_type!='hypereutectoid' else 0.0,
                    'cementite_fraction':1.0-pfrac if self.steel_type=='hypereutectoid' else 0.0,
                    'pearlite_fraction':pfrac,
                    'grains_visible':True,'all_grains':True,'white_background':True,
                    'large_grains_type':self.large_grains_type,
                    'n_pearlite_grains':int(pfrac * self.n_transformable_grains)}

    def generate_microstructure(self, temperature):
        state = self.get_transformation_state(temperature)
        micro = np.zeros((self.height,self.width,3), dtype=np.uint8)
        if state['phase'] in ['liquid','austenite_forming','austenite_liquid',
                              'cementite_forming','cementite_liquid']:
            micro[:,:,:] = self.liquid_color
        else:
            micro[:,:,:] = self.background_color

        current = None

        if state['phase'] == 'liquid':
            current = np.full((self.height,self.width), -1)
        elif state['phase'] == 'austenite_forming':
            current = np.full((self.height,self.width), -1)
            n_show = max(1, int(len(self.large_grain_ids) * state['austenite_fraction'] / 0.3))
            for gid in self.large_grain_ids[:n_show]:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    micro[mask] = self.austenite_color
                    current[mask] = gid
        elif state['phase'] == 'austenite_liquid':
            current = np.full((self.height,self.width), -1)
            for gid in self.large_grain_ids:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    micro[mask] = self.austenite_color
                    current[mask] = gid
        elif state['phase'] == 'cementite_forming':
            current = np.full((self.height,self.width), -1)
            n_show = max(1, int(len(self.large_grain_ids) * state['cementite_fraction'] / 0.3))
            for gid in self.large_grain_ids[:n_show]:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    micro[mask] = self.proeutectoid_cementite_color
                    current[mask] = gid
        elif state['phase'] == 'cementite_liquid':
            current = np.full((self.height,self.width), -1)
            for gid in self.large_grain_ids:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    micro[mask] = self.proeutectoid_cementite_color
                    current[mask] = gid
        elif state['phase'] == 'all_grains_appear':
            current = self.shrunk_grain_map_1147.copy()
            for gid in self.unique_grains:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    if self.steel_type == 'hypereutectoid':
                        if gid in self.large_grain_ids:
                            micro[mask] = self.proeutectoid_cementite_color
                        else:
                            micro[mask] = self.austenite_color
                    else:
                        micro[mask] = self.austenite_color
        elif state['phase'] == 'ledeburite':
            current = self.shrunk_grain_map_1147.copy()
            for gid in self.unique_grains:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    if self.steel_type == 'hypereutectoid':
                        if gid in self.large_grain_ids:
                            micro[mask] = self.proeutectoid_cementite_color
                        else:
                            micro[mask] = self.austenite_color
                    else:
                        micro[mask] = self.austenite_color
        else:  # pearlite_forming
            current = self.shrunk_grain_map_1147.copy()
            pearl_set = set()
            if 'n_pearlite_grains' in state:
                pearl_set = set(self.pearlite_transformation_order[:state['n_pearlite_grains']])
            for gid in self.unique_grains:
                mask = (self.shrunk_grain_map_1147 == gid)
                if np.any(mask):
                    if gid in pearl_set:
                        micro[mask] = self.ferrite_in_pearlite_color
                        self._add_pearlite_to_grain(micro, gid)
                    else:
                        if self.steel_type == 'hypereutectoid':
                            if gid in self.large_grain_ids:
                                micro[mask] = self.proeutectoid_cementite_color
                            else:
                                micro[mask] = self.austenite_color
                        else:
                            micro[mask] = self.austenite_color

        if state.get('grains_visible', False) and state.get('phase') not in ['liquid']:
            if current is not None and np.any(current >= 0):
                bounds = self._get_grain_boundaries(current)
                micro[bounds] = self.grain_boundary_color

        if temperature < 723 and current is not None:
            allowed = (current == -1)
            self._draw_cementite_grains(micro, allowed)

        return micro, state