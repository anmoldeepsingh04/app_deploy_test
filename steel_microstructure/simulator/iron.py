import random
import math
import numpy as np
from scipy import ndimage
from sklearn.cluster import KMeans


from simulator.base import BaseSimulator
from simulator.constants import COLORS

# ==================== IRON-CARBON PHASE DIAGRAM SIMULATOR (0-0.53%C) ====================
class IronCarbonPhaseDiagramSimulator(BaseSimulator):
    def __init__(self, carbon_percent=0.2, width=400, height=300, n_grains=50, seed=42):
        super().__init__(carbon_percent, width, height, n_grains, seed)
        # self.carbon_percent = carbon_percent
        # self.width = width
        # self.height = height
        # self.seed = seed
        random.seed(seed)

        self._calculate_all_transition_temperatures()
        self.original_grain_map = self._create_grain_structure(width, height, n_grains, seed)
        self.unique_grains = np.unique(self.original_grain_map)
        self.n_grains = len(self.unique_grains)

        # Use global colors
        self.liquid_color = COLORS['liquid']
        self.delta_ferrite_color = COLORS['delta_ferrite']
        self.austenite_color = COLORS['austenite']
        self.alpha_ferrite_color = COLORS['alpha_ferrite']
        self.proeutectoid_ferrite_color = COLORS['proeutectoid_ferrite']
        self.cementite_color = COLORS['cementite_bulk']
        self.cementite_boundary_color = COLORS['cementite_boundary']
        self.pearlite_ferrite_color = COLORS['pearlite_ferrite']
        self.pearlite_cementite_color = COLORS['pearlite_cementite']
        self.grain_boundary_color = COLORS['grain_boundary']
        self.background_color = COLORS['background']

        self._select_fixed_cementite_positions()

        print(f"COMPLETE IRON-CARBON PHASE DIAGRAM SIMULATION (0-0.53%C)")
        print(f"Carbon content: {self.carbon_percent}%")
        print(f"Number of grains: {self.n_grains}")
        print("="*70)
        self._print_all_transition_temperatures()

    def _select_fixed_cementite_positions(self):
        random.seed(self.seed)
        self.cementite_positions = []
        shrunk_map = self._shrink_grains_for_channels(self.original_grain_map, shrinkage_factor=8)
        ferrite_channel_mask = (shrunk_map == -1)
        ferrite_y, ferrite_x = np.where(ferrite_channel_mask)
        ferrite_coords = list(zip(ferrite_x, ferrite_y))
        if len(ferrite_coords) < 5:
            ferrite_coords = [(x, y) for x in range(50, self.width-50, 50)
                             for y in range(50, self.height-50, 50)]
        n_cementite_grains = 5
        attempts = 0
        max_attempts = 100
        while len(self.cementite_positions) < n_cementite_grains and attempts < max_attempts:
            attempts += 1
            if ferrite_coords:
                x, y = random.choice(ferrite_coords)
                valid = True
                for existing in self.cementite_positions:
                    dist = np.sqrt((x - existing['x'])**2 + (y - existing['y'])**2)
                    if dist < 60:
                        valid = False
                        break
                if valid:
                    size = random.randint(7, 8)
                    self.cementite_positions.append({'x': x, 'y': y, 'size': size})
        if len(self.cementite_positions) < n_cementite_grains:
            zones = [
                (self.width//6, self.width//3, self.height//6, self.height//3),
                (2*self.width//3, 5*self.width//6, self.height//6, self.height//3),
                (self.width//6, self.width//3, 2*self.height//3, 5*self.height//6),
                (2*self.width//3, 5*self.width//6, 2*self.height//3, 5*self.height//6),
                (self.width//3, 2*self.width//3, self.height//3, 2*self.height//3)
            ]
            for xmin, xmax, ymin, ymax in zones:
                if len(self.cementite_positions) >= n_cementite_grains:
                    break
                x = (xmin + xmax) // 2
                y = (ymin + ymax) // 2
                size = random.randint(7, 8)
                self.cementite_positions.append({'x': x, 'y': y, 'size': size})

    def _calculate_all_transition_temperatures(self):
        C = self.carbon_percent
        self.liquid_to_L_delta = -81.13 * C + 1536
        self.L_delta_to_same = None
        self.delta_to_gamma_delta = None
        self.gamma_delta_to_gamma = None
        self.L_delta_to_gamma_delta = None
        self.L_delta_to_L_gamma = None
        self.L_gamma_to_gamma = None
        if C <= 0.09:
            self.L_delta_to_same = -477.77 * C + 1536
            self.delta_to_gamma_delta = 1122.22 * C + 1392
            self.gamma_delta_to_gamma = -623.331756*(C**2) + 717.550337*C + 1390.6
        elif C <= 0.17:
            self.L_delta_to_gamma_delta = 1493
            self.gamma_delta_to_gamma = -623.331756*(C**2) + 717.550337*C + 1390.6
        elif C <= 0.53:
            self.L_delta_to_L_gamma = 1493
            self.L_gamma_to_gamma = 66.388*(C**3) - 139.918*(C**2) - 167.114*C + 1515.012
        self.gamma_to_gamma_alpha = 910 - 203*math.sqrt(C) - 15.2*C + 0.44*(C**2)
        if C < 0.02:
            self.gamma_alpha_to_alpha = (27684937.1*(C**3) - 545343.1*(C**2) -
                                        9597.6*C + 911.5)
            self.alpha_to_alpha_cementite = (95613037.48*(C**3) - 4905199.82*(C**2) +
                                            95670.87*C + 11.05)
        else:
            self.eutectoid_temp = 723
        self.pearlite_start = 723
        self.pearlite_complete = 600

    def _print_all_transition_temperatures(self):
        C = self.carbon_percent
        print("COMPLETE TRANSITION TEMPERATURES:")
        print("="*70)
        print("\nHIGH TEMPERATURE (1600°C to 1200°C):")
        print(f"  Liquid → Liquid + δ: {self.liquid_to_L_delta:.1f}°C")
        if C <= 0.09:
            print(f"  T = {self.L_delta_to_same:.1f}°C: Liquid+δ remains same")
            print(f"  Liquid+δ → γ+δ: {self.delta_to_gamma_delta:.1f}°C")
            print(f"  γ+δ → γ: {self.gamma_delta_to_gamma:.1f}°C")
        elif C <= 0.17:
            print(f"  Liquid+δ → γ+δ: {self.L_delta_to_gamma_delta:.1f}°C")
            print(f"  γ+δ → γ: {self.gamma_delta_to_gamma:.1f}°C")
        elif C <= 0.53:
            print(f"  Liquid+δ → Liquid+γ: {self.L_delta_to_L_gamma:.1f}°C")
            print(f"  Liquid+γ → γ: {self.L_gamma_to_gamma:.1f}°C")
        print("\nMEDIUM TEMPERATURE (~1200°C to ~727°C):")
        print(f"  γ → γ + α: {self.gamma_to_gamma_alpha:.1f}°C")
        print("\nLOW TEMPERATURE (below ~727°C):")
        if C < 0.02:
            print(f"  γ + α → α: {self.gamma_alpha_to_alpha:.1f}°C")
            print(f"  α → α + Fe₃C: {self.alpha_to_alpha_cementite:.1f}°C")
        else:
            print(f"  Eutectoid transformation starts at {self.eutectoid_temp}°C")
            print(f"  Pearlite formation: 723°C to 600°C")
        print("="*70)

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
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            shifted = np.roll(np.roll(grain_map, dx, axis=1), dy, axis=0)
            boundary |= (grain_map != shifted)
        return boundary

    def _shrink_grains_for_channels(self, grain_map, shrinkage_factor):
        if shrinkage_factor <= 0:
            return grain_map.copy()
        shrunk_map = grain_map.copy()
        structure = np.ones((3,3))
        for gid in np.unique(grain_map):
            if gid == -1: continue
            mask = (grain_map == gid)
            if np.sum(mask) < 10: continue
            eroded = ndimage.binary_erosion(mask, structure=structure, iterations=shrinkage_factor)
            eroded = ndimage.binary_fill_holes(eroded)
            shrunk_map[eroded] = gid
            shrunk_map[mask & ~eroded] = -1
        return shrunk_map

    def _create_pearlite_in_all_grains(self, microstructure, grain_map):
        temp = microstructure.copy()
        unique = np.unique(grain_map)
        unique = unique[unique != -1]
        for gid in unique:
            mask = (grain_map == gid)
            if np.sum(mask) < 10: continue
            ys, xs = np.where(mask)
            ymin, ymax = ys.min(), ys.max()
            xmin, xmax = xs.min(), xs.max()
            region = mask[ymin:ymax+1, xmin:xmax+1]
            yidx, xidx = np.where(region)
            if len(yidx)==0: continue
            yc = yidx - np.mean(yidx)
            xc = xidx - np.mean(xidx)
            angle = 45
            theta = np.deg2rad(angle)
            u = xc*np.cos(theta) + yc*np.sin(theta)
            lamella = 3
            phase = ((u/lamella).astype(int) % 2)
            cem_mask = (phase == 0)
            fer_mask = (phase == 1)
            cy = yidx[cem_mask] + ymin
            cx = xidx[cem_mask] + xmin
            fy = yidx[fer_mask] + ymin
            fx = xidx[fer_mask] + xmin
            temp[cy, cx] = self.pearlite_cementite_color
            temp[fy, fx] = self.pearlite_ferrite_color
        for gid in unique:
            microstructure[grain_map == gid] = temp[grain_map == gid]

    # ---------- unified cementite drawing method ----------
    def _draw_cementite_grains(self, micro, allowed_mask):
        h, w = allowed_mask.shape
        for cem in self.cementite_positions:
            x, y, sz = cem['x'], cem['y'], cem['size']
            if not (0 <= x < w and 0 <= y < h):
                continue
            # Bulk
            for dx in range(-sz, sz+1):
                for dy in range(-sz, sz+1):
                    xi, yi = x+dx, y+dy
                    if 0 <= xi < w and 0 <= yi < h and dx*dx + dy*dy <= sz*sz:
                        if allowed_mask[yi, xi]:
                            micro[yi, xi] = self.cementite_color
            # Outline
            for dx in range(-sz-1, sz+2):
                for dy in range(-sz-1, sz+2):
                    xi, yi = x+dx, y+dy
                    if 0 <= xi < w and 0 <= yi < h:
                        d2 = dx*dx + dy*dy
                        if (sz+0.5)**2 < d2 <= (sz+1.5)**2:
                            if allowed_mask[yi, xi] and np.array_equal(micro[yi, xi], self.cementite_color):
                                micro[yi, xi] = self.cementite_boundary_color

    def get_phase_region(self, temperature):
        C = self.carbon_percent
        if temperature > self.liquid_to_L_delta:
            return {'phase':'liquid', 'description':'Liquid (L)', 'grains_visible': False}
        elif C <= 0.09:
            if temperature > self.L_delta_to_same:
                return {'phase':'liquid_delta_ferrite', 'description':'L + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'delta_ferrite',
                        'shrinkage_factor': 5}
            elif temperature > self.delta_to_gamma_delta:
                return {'phase':'liquid_delta_ferrite', 'description':'L + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'delta_ferrite',
                        'shrinkage_factor': 5}
            elif temperature > self.gamma_delta_to_gamma:
                return {'phase':'gamma_delta_ferrite', 'description':'γ + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'both'}
        elif C <= 0.17:
            if temperature > self.L_delta_to_gamma_delta:
                return {'phase':'liquid_delta_ferrite', 'description':'L + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'delta_ferrite',
                        'shrinkage_factor': 5}
            elif temperature > self.gamma_delta_to_gamma:
                return {'phase':'gamma_delta_ferrite', 'description':'γ + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'both'}
        elif C <= 0.53:
            if temperature > self.L_delta_to_L_gamma:
                return {'phase':'liquid_delta_ferrite', 'description':'L + δ-ferrite',
                        'grains_visible': True, 'phase_type': 'delta_ferrite',
                        'shrinkage_factor': 5}
            elif temperature > self.L_gamma_to_gamma:
                return {'phase':'liquid_austenite', 'description':'L + γ (austenite)',
                        'grains_visible': True, 'phase_type': 'austenite'}
        if temperature > self.gamma_to_gamma_alpha + 5:
            return {'phase':'austenite_only', 'description':'Austenite (γ)',
                    'grains_visible': True, 'phase_type': 'austenite'}
        if C < 0.02:
            if temperature > self.gamma_alpha_to_alpha + 5:
                shrinkage = int((self.gamma_to_gamma_alpha - temperature) / 15)
                shrinkage = max(1, min(6, shrinkage))
                return {'phase':'austenite_ferrite', 'description':'α + γ',
                        'grains_visible': True, 'phase_type': 'both', 'shrinkage_factor': shrinkage}
            elif temperature > self.alpha_to_alpha_cementite + 5:
                return {'phase':'ferrite_only', 'description':'α-ferrite (α)',
                        'grains_visible': True, 'phase_type': 'alpha_ferrite'}
            else:
                return {'phase':'ferrite_cementite', 'description':'α + Fe₃C',
                        'grains_visible': True, 'phase_type': 'both', 'shrinkage_factor': 10}
        elif temperature > self.pearlite_start:
            shrinkage = int((self.gamma_to_gamma_alpha - temperature) / 15)
            shrinkage = max(1, min(6, shrinkage))
            return {'phase':'austenite_ferrite', 'description':'α + γ',
                    'grains_visible': True, 'phase_type': 'both', 'shrinkage_factor': shrinkage}
        else:
            if temperature >= self.pearlite_start:
                pearlite_fraction = 0.1
                return {'phase':'pearlite_forming', 'description': f'Pearlite forming ({pearlite_fraction*100:.0f}%)',
                        'grains_visible': True, 'phase_type': 'pearlite', 'shrinkage_factor': 6,
                        'pearlite_fraction': pearlite_fraction}
            elif temperature > self.pearlite_complete:
                pearlite_fraction = 1.0 - ((temperature - self.pearlite_complete) /
                                          (self.pearlite_start - self.pearlite_complete))
                pearlite_fraction = max(0.1, min(0.9, pearlite_fraction))
                return {'phase':'pearlite_forming', 'description': f'Pearlite forming ({pearlite_fraction*100:.0f}%)',
                        'grains_visible': True, 'phase_type': 'pearlite', 'shrinkage_factor': 6,
                        'pearlite_fraction': pearlite_fraction}
            else:
                return {'phase':'pearlite_complete', 'description': 'α-ferrite + Pearlite + Fe₃C III',
                        'grains_visible': True, 'phase_type': 'pearlite', 'shrinkage_factor': 6}

    def generate_microstructure(self, temperature):
        state = self.get_phase_region(temperature)
        micro = np.ones((self.height, self.width, 3), dtype=np.uint8) * self.background_color
        current = None

        if state['phase'] == 'liquid':
            micro[:,:,:] = self.liquid_color
            current = np.full((self.height, self.width), -1, dtype=int)
        elif state['phase'] == 'liquid_delta_ferrite':
            shrink = state.get('shrinkage_factor', 5)
            shrunk = self._shrink_grains_for_channels(self.original_grain_map, shrink)
            micro[:,:,:] = self.liquid_color
            for gid in self.unique_grains:
                gmask = (shrunk == gid)
                if np.any(gmask):
                    micro[gmask] = self.delta_ferrite_color
            current = shrunk
        elif state['phase'] == 'liquid_austenite':
            micro[:,:,:] = self.liquid_color
            current = self.original_grain_map.copy()
            for gid in self.unique_grains:
                micro[self.original_grain_map == gid] = self.austenite_color
        elif state['phase'] == 'gamma_delta_ferrite':
            current = self.original_grain_map.copy()
            for i, gid in enumerate(self.unique_grains):
                mask = (self.original_grain_map == gid)
                micro[mask] = self.austenite_color if i%2==0 else self.delta_ferrite_color
        elif state['phase'] == 'austenite_only':
            current = self.original_grain_map.copy()
            for gid in self.unique_grains:
                micro[self.original_grain_map == gid] = self.austenite_color
        elif state['phase'] == 'austenite_ferrite':
            shrink = state.get('shrinkage_factor',1)
            shrunk = self._shrink_grains_for_channels(self.original_grain_map, shrink)
            ferrite = (shrunk == -1)
            micro[ferrite] = self.proeutectoid_ferrite_color
            for gid in self.unique_grains:
                gmask = (shrunk == gid)
                if np.any(gmask):
                    micro[gmask] = self.austenite_color
            current = shrunk
        elif state['phase'] == 'ferrite_only':
            current = self.original_grain_map.copy()
            for gid in self.unique_grains:
                micro[self.original_grain_map == gid] = self.alpha_ferrite_color
        elif state['phase'] == 'ferrite_cementite':
            shrink = state.get('shrinkage_factor',10)
            shrunk = self._shrink_grains_for_channels(self.original_grain_map, shrink)
            ferrite = (shrunk == -1)
            micro[ferrite] = self.alpha_ferrite_color
            for gid in self.unique_grains:
                gmask = (shrunk == gid)
                if np.any(gmask):
                    micro[gmask] = self.cementite_color
            current = shrunk
        elif state['phase'] == 'pearlite_forming':
            shrink = state.get('shrinkage_factor',6)
            pearl_frac = state.get('pearlite_fraction',0.0)
            shrunk = self._shrink_grains_for_channels(self.original_grain_map, shrink)
            ferrite = (shrunk == -1)
            micro[ferrite] = self.proeutectoid_ferrite_color
            n_pearl = int(pearl_frac * len(self.unique_grains))
            pearl_ids = list(self.unique_grains)[:n_pearl]
            pearl_map = np.full_like(shrunk, -1)
            for gid in pearl_ids:
                gmask = (shrunk == gid)
                if np.any(gmask):
                    pearl_map[gmask] = gid
            if np.any(pearl_map != -1):
                self._create_pearlite_in_all_grains(micro, pearl_map)
            for gid in self.unique_grains:
                if gid in pearl_ids: continue
                gmask = (shrunk == gid)
                if np.any(gmask):
                    micro[gmask] = self.austenite_color
            current = shrunk
        elif state['phase'] == 'pearlite_complete':
            shrink = state.get('shrinkage_factor',6)
            shrunk = self._shrink_grains_for_channels(self.original_grain_map, shrink)
            ferrite = (shrunk == -1)
            micro[ferrite] = self.proeutectoid_ferrite_color
            self._create_pearlite_in_all_grains(micro, shrunk)
            current = shrunk
        else:
            current = self.original_grain_map.copy()
            for gid in self.unique_grains:
                micro[self.original_grain_map == gid] = self.austenite_color

        if state.get('grains_visible', False) and state['phase'] != 'liquid':
            if current is not None:
                bounds = self._get_grain_boundaries(current)
                micro[bounds] = self.grain_boundary_color

        if temperature < 723 and current is not None:
            allowed = (current == -1)
            self._draw_cementite_grains(micro, allowed)

        return micro, state
    

    # alias method for parent class
    def get_phase_state(self, temperature):
        return self.get_phase_region(temperature)