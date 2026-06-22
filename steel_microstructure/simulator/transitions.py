# ==================== FAST TRANSITION INFO FUNCTIONS (ENHANCED FOR CARBON PROFILE) ====================
# Phase boundary functions (same as in simulators)
def liquidus(C):
    return 0.325201*C**3 - 5.168028*C**2 - 75.120496*C + 1538.747373

def solidus(C):
    return 66.388*C**3 - 139.918*C**2 - 167.114*C + 1515.012

def A3(C):
    # valid for C <= 0.76
    return 910 - 203*math.sqrt(C) - 15.2*C + 0.44*C**2

def Acm(C):
    # valid for 0.76 <= C <= 2.06
    return 330.77*C + 471.62

def gamma_alpha_to_alpha(C):
    # α/(α+γ) boundary, valid for C < 0.02
    return 27684937.1*C**3 - 545343.1*C**2 - 9597.6*C + 911.5

def alpha_to_alpha_cementite(C):
    # α/(α+Fe₃C) boundary, valid for C < 0.02
    return 95613037.48*C**3 - 4905199.82*C**2 + 95670.87*C + 11.05

def liquid_to_cementite(C):
    # Liquid/(Liquid+Fe₃C) for hypereutectic cast irons, C > 4.3
    return -19.714*C**3 + 313.032*C**2 - 1554.375*C + 3610.368

def solve_boundary(func, bracket, temp, name):
    try:
        sol = root_scalar(lambda c: func(c) - temp, bracket=bracket, method='bisect')
        if sol.converged and bracket[0] <= sol.root <= bracket[1]:
            return (sol.root, name)
    except:
        pass
    return None

def get_carbon_transitions(temp):
    """
    Compute all relevant phase boundary carbon percentages at a given temperature.
    Returns a list of (carbon, description) sorted by carbon.
    """
    trans = []
    
    # α/(α+γ) boundary (very low carbon)
    if 10 < temp < 912:
        result = solve_boundary(gamma_alpha_to_alpha, (0, 0.02), temp, "α → α+γ")
        if result:
            trans.append(result)
    
    # α/(α+Fe₃C) boundary (very low carbon, below eutectoid)
    if temp < 723 and temp > 11:
        result = solve_boundary(alpha_to_alpha_cementite, (0, 0.02), temp, "α → α+Fe₃C")
        if result:
            trans.append(result)
    
    # γ/(γ+α) boundary (A3)
    if 723 <= temp <= 912:
        result = solve_boundary(A3, (0, 0.76), temp, "γ → γ+α")
        if result:
            trans.append(result)
    
    # γ/(γ+Fe₃C) boundary (Acm)
    if 723 <= temp <= 1147:
        result = solve_boundary(Acm, (0.76, 2.06), temp, "γ → γ+Fe₃C")
        if result:
            trans.append(result)
    
    # Liquidus (for all compositions)
    if temp <= 1538:
        result = solve_boundary(liquidus, (0, 6.67), temp, "Liquidus")
        if result:
            trans.append(result)
    
    # Solidus (for steels)
    if temp <= 1515:
        result = solve_boundary(solidus, (0, 2.06), temp, "Solidus")
        if result:
            trans.append(result)
    
    # Liquid/(Liquid+Fe₃C) for hypereutectic cast irons
    if temp >= 1147 and temp <= 1600:
        result = solve_boundary(liquid_to_cementite, (4.3, 6.67), temp, "L → L+Fe₃C")
        if result:
            trans.append(result)
    
    # Invariant points (only include if temperature is very close)
    if abs(temp - 723) < 10:
        trans.append((0.76, "γ → α+Fe₃C (Eutectoid)"))
    if abs(temp - 1147) < 10:
        trans.append((4.3, "L → γ+Fe₃C (Eutectic)"))
    
    # Remove duplicates by carbon value (keep first occurrence)
    unique = {}
    for c, desc in trans:
        if c not in unique:
            unique[c] = desc
    sorted_trans = sorted([(c, desc) for c, desc in unique.items()], key=lambda x: x[0])
    return sorted_trans


# ==================== FAST TRANSITION TEMPERATURE FUNCTIONS ====================

def get_transition_temperatures_cast(C):
    temps = []
    if C < 4.3:
        liquid_to_austenite = 0.325201*C**3 - 5.168028*C**2 - 75.120496*C + 1538.747373
        temps.append(("Liquid → Liquid+γ", liquid_to_austenite))
    elif C > 4.3:
        liquid_to_cementite = -19.714*C**3 + 313.032*C**2 - 1554.375*C + 3610.368
        temps.append(("Liquid → Liquid+Fe₃C", liquid_to_cementite))
    temps.append(("Eutectic", 1147))
    temps.append(("Eutectoid", 723))
    return temps

def get_transition_temperatures_steel(C):
    temps = []
    liquidus = 0.325201*C**3 - 5.168028*C**2 - 75.120496*C + 1538.747373
    solidus = 66.388*C**3 - 139.918*C**2 - 167.114*C + 1515.012
    temps.append(("Liquidus", liquidus))
    temps.append(("Solidus", solidus))
    if C < 0.76:
        A3 = 910 - 203*math.sqrt(C) - 15.2*C + 0.44*C**2
        temps.append(("A3 (γ→γ+α)", A3))
    else:
        Acm = 330.77*C + 471.62
        temps.append(("Acm (γ→γ+Fe₃C)", Acm))
    temps.append(("Eutectoid", 723))
    return temps


def get_transition_temperatures_low_carbon(C):
    temps = []
    liquid_to_L_delta = -81.13 * C + 1536
    temps.append(("Liquid → Liquid+δ", liquid_to_L_delta))
    if C <= 0.09:
        L_delta_to_same = -477.77 * C + 1536
        delta_to_gamma_delta = 1122.22 * C + 1392
        gamma_delta_to_gamma = -623.331756*(C**2) + 717.550337*C + 1390.6
        temps.append(("Liquid+δ remains same", L_delta_to_same))
        temps.append(("Liquid+δ → γ+δ", delta_to_gamma_delta))
        temps.append(("γ+δ → γ", gamma_delta_to_gamma))
    elif C <= 0.17:
        L_delta_to_gamma_delta = 1493
        gamma_delta_to_gamma = -623.331756*(C**2) + 717.550337*C + 1390.6
        temps.append(("Liquid+δ → γ+δ", L_delta_to_gamma_delta))
        temps.append(("γ+δ → γ", gamma_delta_to_gamma))
    elif C <= 0.53:
        L_delta_to_L_gamma = 1493
        L_gamma_to_gamma = 66.388*(C**3) - 139.918*(C**2) - 167.114*C + 1515.012
        temps.append(("Liquid+δ → Liquid+γ", L_delta_to_L_gamma))
        temps.append(("Liquid+γ → γ", L_gamma_to_gamma))
    gamma_to_gamma_alpha = 910 - 203*math.sqrt(C) - 15.2*C + 0.44*(C**2)
    temps.append(("γ → γ+α", gamma_to_gamma_alpha))
    if C < 0.02:
        gamma_alpha_to_alpha = (27684937.1*(C**3) - 545343.1*(C**2) - 9597.6*C + 911.5)
        alpha_to_alpha_cementite = (95613037.48*(C**3) - 4905199.82*(C**2) + 95670.87*C + 11.05)
        temps.append(("γ+α → α", gamma_alpha_to_alpha))
        temps.append(("α → α+Fe₃C", alpha_to_alpha_cementite))
    else:
        temps.append(("Eutectoid start", 723))
    return temps