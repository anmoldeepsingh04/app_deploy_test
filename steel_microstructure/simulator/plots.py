import numpy as np
import matplotlib.pyplot as plt

from simulator.factory import create_unified_simulator

# ==================== CARBON PROFILE AT FIXED TEMPERATURE ====================
def generate_carbon_list():
    return [0.0, 0.02, 0.09, 0.17, 0.53, 0.8, 2.06, 4.3, 6.67]

def plot_carbon_profile(temperature, carbon_list=None, **kwargs):
    if carbon_list is None:
        carbon_list = generate_carbon_list()
    n_cols = 5
    n_rows = int(np.ceil(len(carbon_list) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 3*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    for i, C in enumerate(carbon_list):
        if i >= len(axes):
            break
        sim = create_unified_simulator(C, **kwargs)
        micro, state = sim.generate_microstructure(temperature)
        axes[i].imshow(micro)
        axes[i].set_title(f'{C}% C\n{state["description"]}', fontsize=9)
        axes[i].axis('off')
    for i in range(len(carbon_list), len(axes)):
        axes[i].axis('off')
    plt.suptitle(f'Fe-C Microstructures at {temperature}°C for various carbon contents',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()


# ==================== PLOT KEY TRANSITIONS (TEMPERATURE PROFILE) ====================
def plot_key_transitions(carbon_percent, **kwargs):
    simulator = create_unified_simulator(carbon_percent, **kwargs)
    transitions = []

    transitions.append(("1600°C", 1600, "Liquid"))

    if carbon_percent <= 0.53:
        C = carbon_percent
        if C <= 0.09:
            transitions.append((f"{simulator.liquid_to_L_delta:.0f}°C -5°C",
                                simulator.liquid_to_L_delta-5, "Liquid+δ"))
            transitions.append((f"{simulator.delta_to_gamma_delta:.0f}°C -5°C",
                                simulator.delta_to_gamma_delta-5, "γ+δ"))
            transitions.append((f"{simulator.gamma_delta_to_gamma:.0f}°C -5°C",
                                simulator.gamma_delta_to_gamma-5, "γ"))
        elif C <= 0.17:
            transitions.append((f"{simulator.liquid_to_L_delta:.0f}°C -5°C",
                                simulator.liquid_to_L_delta-5, "Liquid+δ"))
            transitions.append(("1490°C", 1490, "γ+δ"))
            transitions.append((f"{simulator.gamma_delta_to_gamma:.0f}°C -5°C",
                                simulator.gamma_delta_to_gamma-5, "γ"))
        elif C <= 0.53:
            transitions.append((f"{simulator.liquid_to_L_delta:.0f}°C -5°C",
                                simulator.liquid_to_L_delta-5, "Liquid+δ"))
            transitions.append(("1490°C", 1490, "Liquid+γ"))
            transitions.append((f"{simulator.L_gamma_to_gamma:.0f}°C -5°C",
                                simulator.L_gamma_to_gamma-5, "γ"))
        transitions.append(("1200°C", 1200, "γ"))
        transitions.append((f"{simulator.gamma_to_gamma_alpha:.0f}°C -5°C",
                            simulator.gamma_to_gamma_alpha-5, "γ+α"))
        if C < 0.02:
            transitions.append((f"{simulator.gamma_alpha_to_alpha:.0f}°C -5°C",
                                simulator.gamma_alpha_to_alpha-5, "α"))
            transitions.append((f"{simulator.alpha_to_alpha_cementite:.0f}°C -5°C",
                                simulator.alpha_to_alpha_cementite-5, "α+Fe₃C"))
            transitions.append(("20°C", 20, "α+Fe₃C (room temp)"))
        else:
            transitions.append(("724°C", 724, "γ+α (just above eutectoid)"))
            transitions.append(("723°C", 723, "PEARLITE STARTS FORMING"))
            transitions.append(("700°C", 700, "Pearlite forming ~30%"))
            transitions.append(("650°C", 650, "Pearlite forming ~60%"))
            transitions.append(("600°C", 600, "Pearlite ~90% complete"))
            transitions.append(("20°C", 20, "Pearlite + 5 Fe₃C in channels"))

    elif carbon_percent < 2.06:
        transitions.append((f"{simulator.liquidus_temp:.0f}°C", simulator.liquidus_temp, "Liquidus"))
        transitions.append((f"{(simulator.liquidus_temp+simulator.solidus_temp)/2:.0f}°C",
                            (simulator.liquidus_temp+simulator.solidus_temp)/2, "Liquid+Austenite"))
        transitions.append((f"{simulator.solidus_temp:.0f}°C", simulator.solidus_temp, "Solidus"))
        transitions.append(("1200°C", 1200, "Austenite"))
        if hasattr(simulator, 'transition_temp') and simulator.transition_temp is not None:
            transitions.append((f"{simulator.transition_temp+100:.0f}°C",
                                simulator.transition_temp+100, "Austenite"))
            transitions.append((f"{simulator.transition_temp:.0f}°C",
                                simulator.transition_temp, f"A3/Acm start"))
        transitions.append((f"{simulator.eutectoid_temp+20:.0f}°C",
                            simulator.eutectoid_temp+20, "Austenite+Proeutectoid"))
        transitions.append((f"{simulator.eutectoid_temp:.0f}°C", simulator.eutectoid_temp, "Pearlite start"))
        transitions.append(("700°C", 700, "Pearlite forming"))
        transitions.append(("600°C", 600, "Pearlite forming"))
        transitions.append(("20°C", 20, "Room temp"))

    else:
        if hasattr(simulator, 'liquidus_temp') and simulator.liquidus_temp:
            transitions.append((f"{simulator.liquidus_temp:.0f}°C", int(simulator.liquidus_temp),
                                "Large grains forming"))
        transitions.append(("1148°C", 1148, "Just above eutectic"))
        transitions.append(("1147°C", 1147, "Eutectic transformation"))
        transitions.append(("1000°C", 1000, "Ledeburite"))
        transitions.append(("723°C", 723, "Pearlite start"))
        transitions.append(("500°C", 500, "Pearlite forming"))
        transitions.append(("25°C", 25, "Room temp"))

    if len(transitions) == 0:
        transitions.append(("20°C", 20, "Room temperature"))

    valid = [(name, t, desc) for name, t, desc in transitions if 20 <= t <= 1600]
    if len(valid) == 0:
        valid = [("20°C", 20, "Room temperature (fallback)")]

    n_cols = 4
    n_rows = int(np.ceil(len(valid) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()

    for i, (name, temp, desc) in enumerate(valid):
        if i >= len(axes): break
        micro, state = simulator.generate_microstructure(temp)
        axes[i].imshow(micro)
        desc_low = state['description'].lower()
        color = 'black'
        if 'liquid' in desc_low: color = 'blue'
        elif 'δ' in desc_low or 'delta' in desc_low: color = 'darkblue'
        elif 'γ' in desc_low or 'austenite' in desc_low: color = 'darkred'
        elif 'α' in desc_low or 'ferrite' in desc_low: color = 'darkcyan'
        elif 'cementite' in desc_low or 'fe₃c' in desc_low: color = 'darkgray'
        elif 'pearlite' in desc_low: color = 'saddlebrown'
        elif 'ledeburite' in desc_low: color = 'purple'
        axes[i].set_title(f'{name}\n{desc}', fontsize=9, color=color, fontweight='bold')
        axes[i].axis('off')

    for i in range(len(valid), len(axes)):
        axes[i].axis('off')

    if carbon_percent <= 0.53:
        ctype = "Low carbon steel"
    elif carbon_percent < 2.06:
        ctype = f"{simulator.steel_type.capitalize()} steel"
    else:
        ctype = f"{simulator.steel_type.capitalize()} cast iron"
    plt.suptitle(f'Fe-{carbon_percent}%C: Phase Transformations (1600°C → 20°C)\n{ctype}',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    return simulator