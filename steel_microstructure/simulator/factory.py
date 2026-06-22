# ==================== UNIFIED INTERFACE ====================
def create_unified_simulator(carbon_percent, **kwargs):
    if carbon_percent < 0 or carbon_percent > 6.67:
        raise ValueError(f"Carbon must be 0–6.67%, got {carbon_percent}%")
    defaults = {'width':400, 'height':300, 'seed':42, 'n_grains':50}
    defaults.update(kwargs)
    if carbon_percent <= 0.53:
        return IronCarbonPhaseDiagramSimulator(carbon_percent=carbon_percent, **defaults)
    elif carbon_percent < 2.06:
        return SteelMicrostructureSimulator(carbon_percent=carbon_percent, **defaults)
    else:
        defaults.setdefault('width', 500)
        defaults.setdefault('height', 400)
        return GeneralizedSteel(carbon_percent=carbon_percent, **defaults)
