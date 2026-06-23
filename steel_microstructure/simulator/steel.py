import random
import math
import numpy as np
from scipy import ndimage
from sklearn.cluster import KMeans


from simulator.base import BaseSimulator
from simulator.constants import COLORS

# ==================== STEEL MICROSTRUCTURE SIMULATOR (0.53-2.06%C) ====================
class SteelMicrostructureSimulator(BaseSimulator):
    def __init__(self, carbon_percent=0.76, width=400, height=300, n_grains=50, seed=42):
        super().__init__(carbon_percent, width, height, n_grains, seed)
        # self.carbon_percent = carbon_percent
        # self.width = width
        # self.height = height
        # self.seed = seed
        self._calculate_transformation_temperatures()
        self.original_grain_map = self._create_grain_structure(width, height, n_grains, seed)
        self.unique_grains = np.unique(self.original_grain_map)
        self.n_grains = len(self.unique_grains)

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

        if abs(self.carbon_percent - 0.76) < 0.01:
            self.steel_type = "eutectoid"
            self.transition_temp = self.eutectoid_temp
            self.proeutectoid_phase_name = None
            self.proeutectoid_phase_color = None
        elif self.carbon_percent < 0.76:
            self.steel_type = "hypoeutectoid"
            self.transition_temp = self.A3_temp
            self.proeutectoid_phase_name = "ferrite"
            self.proeutectoid_phase_color = self.proeutectoid_ferrite_color
        else:
            self.steel_type = "hypereutectoid"
            self.transition_temp = self.Acm_temp
            self.proeutectoid_phase_name = "cementite"
            self.proeutectoid_phase_color = self.proeutectoid_cementite_color

        self._select_fixed_cementite_positions()

        print(f"Carbon content: {self.carbon_percent}%")
        print(f"Steel Type: {self.steel_type.upper()}")
        self._print_transformation_temperatures()

    def _select_fixed_cementite_positions(self):
        random.seed(self.seed)
        self.cementite_positions = []
        shrunk = self._erode_grains(self.original_grain_map, erosion_amount=8)
        background = (shrunk == -1)
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

    def _calculate_transformation_temperatures(self):
        C = self.carbon_percent
        self.liquidus_temp = 0.325201*C**3 - 5.168028*C**2 - 75.120496*C + 1538.747373
        self.solidus_temp = 66.388*C**3 - 139.918*C**2 - 167.114*C + 1515.012
        self.eutectoid_temp = 723
        if C < 0.76:
            self.A3_temp = 910 - 203*np.sqrt(C) - 15.2*C + 0.44*C**2
            self.Acm_temp = None
        else:
            self.Acm_temp = 330.77*C + 471.62
            self.A3_temp = None

    def _print_transformation_temperatures(self):
        print("\n"+"="*50)
        print("TRANSFORMATION TEMPERATURES:")
        print("="*50)
        print(f"Liquidus: {self.liquidus_temp:.1f}°C")
        print(f"Solidus: {self.solidus_temp:.1f}°C")
        if self.steel_type == "eutectoid":
            print(f"Eutectoid: {self.eutectoid_temp}°C")
        elif self.steel_type == "hypoeutectoid":
            print(f"A3: {self.A3_temp:.1f}°C")
            print(f"Eutectoid: {self.eutectoid_temp}°C")
        else:
            print(f"Acm: {self.Acm_temp:.1f}°C")
            print(f"Eutectoid: {self.eutectoid_temp}°C")
        print("="*50)

    def _create_grain_structure(self, width, height, n_grains, seed):
        np.random.seed(seed)
        Y, X = np.mgrid[:height, :width]
        coordinates = np.column_stack((X.ravel(), Y.ravel()))
        n_samples = min(10000, width * height)
        sample_indices = np.random.choice(coordinates.shape[0], n_samples, replace=False)
        samples = coordinates[sample_indices]
        kmeans = KMeans(n_clusters=n_grains, random_state=seed, n_init=1)
        kmeans.fit(samples)
        labels = kmeans.predict(coordinates)
        return labels.reshape(height, width)

    def _get_grain_boundaries(self, grain_map):
        boundary = np.zeros_like(grain_map, dtype=bool)
        for shift in [1,-1]:
            boundary |= (grain_map != np.roll(grain_map, shift, axis=0))
            boundary |= (grain_map != np.roll(grain_map, shift, axis=1))
        return boundary

    def _erode_grains(self, grain_map, erosion_amount):
        if erosion_amount <= 0:
            return grain_map.copy()
        eroded = grain_map.copy()
        for gid in self.unique_grains:
            mask = (grain_map == gid)
            struct = np.ones((3,3))
            er = ndimage.binary_erosion(mask, struct, iterations=erosion_amount)
            eroded[er] = gid
            eroded[mask & ~er] = -1
        return eroded

    def _create_proeutectoid_channels_from_erosion(self, original, eroded):
        return (eroded == -1)

    def _add_pearlite_to_grain(self, microstructure, grain_id, current_grain_map):
        mask = (current_grain_map == grain_id)
        if np.sum(mask) < 10: return
        ys, xs = np.where(mask)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        region = mask[ymin:ymax+1, xmin:xmax+1]
        Yg, Xg = np.where(region)
        if len(Xg)==0: return
        rng = np.random.RandomState(grain_id)
        angle = rng.uniform(0,180)
        theta = np.deg2rad(angle)
        cy, cx = np.mean(Yg), np.mean(Xg)
        Yc = Yg - cy
        Xc = Xg - cx
        U = Xc*np.cos(theta) + Yc*np.sin(theta)
        spacing = rng.uniform(2,4)
        phase = (U/spacing).astype(int) % 2
        cem = (phase == 0)
        fer = (phase == 1)
        cem_y = Yg[cem] + ymin
        cem_x = Xg[cem] + xmin
        fer_y = Yg[fer] + ymin
        fer_x = Xg[fer] + xmin
        valid_cem = (cem_x < microstructure.shape[1]) & (cem_y < microstructure.shape[0])
        valid_fer = (fer_x < microstructure.shape[1]) & (fer_y < microstructure.shape[0])
        microstructure[cem_y[valid_cem], cem_x[valid_cem]] = self.cementite_in_pearlite_color
        microstructure[fer_y[valid_fer], fer_x[valid_fer]] = self.ferrite_in_pearlite_color

    def get_transformation_state(self, temperature):
        if temperature > self.liquidus_temp:
            return {'phase':'liquid','description':'Liquid (L)','erosion_amount':0}
        elif temperature > self.solidus_temp:
            frac = ((self.liquidus_temp - temperature) / (self.liquidus_temp - self.solidus_temp))
            frac = np.clip(frac,0,1)
            return {'phase':'liquid_austenite',
                    'description':'L + γ (austenite)',
                    'erosion_amount':0}
        elif self.steel_type=="eutectoid" and temperature>self.eutectoid_temp:
            return {'phase':'austenite','description':'Austenite (γ)','erosion_amount':0}
        elif self.steel_type!="eutectoid" and temperature>self.transition_temp:
            return {'phase':'austenite','description':'Austenite (γ)','erosion_amount':0}
        elif self.steel_type!="eutectoid" and temperature>self.eutectoid_temp:
            if self.steel_type=="hypoeutectoid":
                max_pro = (0.76 - self.carbon_percent) / (0.76 - 0.02)
            else:
                max_pro = (self.carbon_percent - 0.76) / (2.06 - 0.76)
            max_pro = np.clip(max_pro,0,0.95)
            frac_range = self.transition_temp - self.eutectoid_temp
            under = self.transition_temp - temperature
            pro_frac = min((under/frac_range)*max_pro, max_pro)
            max_erosion = 5
            erosion = int(pro_frac * max_erosion / max_pro) if max_pro>0 else 0
            erosion = max(1, erosion)
            phase_name = self.proeutectoid_phase_name
            if self.steel_type == "hypoeutectoid":
                region_name = "α + γ"
            else:
                region_name = "γ + Fe₃C (austenite + cementite)"
            return {'phase':'proeutectoid_forming',
                    'description':region_name,
                    'erosion_amount':erosion}
        else:
            if self.steel_type=="eutectoid":
                desc = 'Pearlite'
            elif self.steel_type == "hypoeutectoid":
                desc = 'α-ferrite + Pearlite + Fe₃C III'
            else:
                desc = 'Pearlite + Fe₃C II'
            return {'phase':'pearlite_forming','description':desc,'erosion_amount':5}

    def generate_microstructure(self, temperature):

        state = self.get_transformation_state(temperature)
        micro = np.ones((self.height,self.width,3),dtype=np.uint8)*self.background_color
        current = None

        if state['phase'] == 'liquid':
            micro[:,:,:] = self.liquid_color
            current = np.full((self.height,self.width),-1,dtype=int)
        elif state['phase'] == 'liquid_austenite':
            micro[:,:,:] = self.liquid_color
            frac = ((self.liquidus_temp - temperature)/(self.liquidus_temp - self.solidus_temp))
            frac = np.clip(frac,0,1)
            n_vis = int(frac * self.n_grains)
            visible = self.unique_grains[:n_vis]
            for gid in visible:
                micro[self.original_grain_map == gid] = self.austenite_color
            current = self.original_grain_map.copy()
            for gid in self.unique_grains:
                if gid not in visible:
                    current[current == gid] = -1
            bounds = self._get_grain_boundaries(current)
            micro[bounds] = self.grain_boundary_color
        else:
            if self.steel_type == "eutectoid":
                if state['phase'] == 'austenite':
                    for gid in self.unique_grains:
                        micro[self.original_grain_map == gid] = self.austenite_color
                    current = self.original_grain_map.copy()
                else:
                    for gid in self.unique_grains:
                        micro[self.original_grain_map == gid] = self.ferrite_in_pearlite_color
                        self._add_pearlite_to_grain(micro, gid, self.original_grain_map)
                    current = self.original_grain_map.copy()
            else:
                if state['phase'] == 'austenite':
                    for gid in self.unique_grains:
                        micro[self.original_grain_map == gid] = self.austenite_color
                    current = self.original_grain_map.copy()
                else:
                    erosion = state['erosion_amount']
                    eroded = self._erode_grains(self.original_grain_map, erosion)
                    pro_mask = self._create_proeutectoid_channels_from_erosion(self.original_grain_map, eroded)
                    micro[pro_mask] = self.proeutectoid_phase_color
                    remaining = ~pro_mask
                    if state['phase'] == 'proeutectoid_forming':
                        for gid in self.unique_grains:
                            gmask = (eroded == gid)
                            micro[gmask] = self.austenite_color
                    else:
                        for gid in self.unique_grains:
                            gmask = (eroded == gid) & remaining
                            micro[gmask] = self.ferrite_in_pearlite_color
                            self._add_pearlite_to_grain(micro, gid, eroded)
                    current = eroded

        if state['phase'] not in ['liquid']:
            if state['phase'] != 'liquid_austenite' and current is not None:
                bounds = self._get_grain_boundaries(current)
                micro[bounds] = self.grain_boundary_color

        if temperature < 723 and current is not None:
            allowed = (current == -1)
            self._draw_cementite_grains(micro, allowed)

        return micro, state

    def get_phase_state(self, temperature):
        return super().get_transformation_state(temperature)