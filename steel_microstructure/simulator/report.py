from simulator.transitions import(
    get_transition_temperatures_low_carbon,
    get_transition_temperatures_steel,
    get_transition_temperatures_cast,
)

def show_transition_info_fast(carbon):
    if carbon <= 0.53:
        trans = get_transition_temperatures_low_carbon(carbon)
    elif carbon < 2.06:
        trans = get_transition_temperatures_steel(carbon)
    else:
        trans = get_transition_temperatures_cast(carbon)
    print(f"Transition temperatures for {carbon}% C:")
    for desc, temp in trans:
        print(f"  {desc}: {temp:.1f}°C")
