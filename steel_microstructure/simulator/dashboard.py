def create_dashboard():
    # Widgets
    profile_type = widgets.Dropdown(
        options=['Temperature profile', 'Carbon profile'],
        value='Temperature profile',
        description='Profile:',
        style={'description_width': 'initial'}
    )
    
    # Input fields with appropriate defaults
    fixed_label = widgets.Label('Fixed carbon (%):')
    fixed_input = widgets.FloatText(value=0.2, step=0.01, description='')
    start_label = widgets.Label('Start temperature (°C):')
    start_input = widgets.FloatText(value=1600, step=10)
    end_label = widgets.Label('End temperature (°C):')
    end_input = widgets.FloatText(value=20, step=10)
    step_label = widgets.Label('Step (°C):')
    step_input = widgets.FloatText(value=40, step=1)   # default step = 40°C
    
    inputs_box = widgets.VBox([
        widgets.HBox([fixed_label, fixed_input]),
        widgets.HBox([start_label, start_input]),
        widgets.HBox([end_label, end_input]),
        widgets.HBox([step_label, step_input])
    ])
    
    def update_labels(change):
        if change['new'] == 'Temperature profile':
            fixed_label.value = 'Fixed carbon (%):'
            fixed_input.value = 0.2
            start_label.value = 'Start temperature (°C):'
            start_input.value = 1600
            end_label.value = 'End temperature (°C):'
            end_input.value = 20
            step_label.value = 'Step (°C):'
            step_input.value = 40          # default step = 40°C
        else:
            fixed_label.value = 'Fixed temperature (°C):'
            fixed_input.value = 800
            start_label.value = 'Start carbon (%):'
            start_input.value = 0.0
            end_label.value = 'End carbon (%):'
            end_input.value = 6.67
            step_label.value = 'Step (%):'
            step_input.value = 0.1
    profile_type.observe(update_labels, names='value')
    
    generate_btn = widgets.Button(description='Generate Animation', button_style='success')
    
    animation_output = widgets.Output()
    legend_output = widgets.Output()
    
    left_col = widgets.VBox([profile_type, inputs_box, generate_btn, animation_output])
    right_col = widgets.VBox([legend_output], layout=widgets.Layout(width='300px'))
    dashboard = widgets.HBox([left_col, right_col])
    
    def show_legend():
        with legend_output:
            clear_output(wait=True)
            fig_leg, ax_leg = plt.subplots(figsize=(2.5, 4))
            ax_leg.axis('off')
            from matplotlib.patches import Patch
            patches = [
                Patch(color=np.array(COLORS['liquid'])/255, label='Liquid (L)'),
                Patch(color=np.array(COLORS['delta_ferrite'])/255, label='δ-ferrite (δ)'),
                Patch(color=np.array(COLORS['austenite'])/255, label='Austenite (γ)'),
                Patch(color=np.array(COLORS['alpha_ferrite'])/255, label='α-ferrite (α)'),
                Patch(color=np.array(COLORS['proeutectoid_ferrite'])/255, label='Proeutectoid Ferrite'),
                Patch(color=np.array(COLORS['cementite_bulk'])/255, label='Cementite (Fe₃C) bulk'),
                Patch(color=np.array(COLORS['pearlite_ferrite'])/255, label='Pearlite Ferrite'),
                Patch(color=np.array(COLORS['pearlite_cementite'])/255, label='Pearlite Cementite'),
                Patch(color=np.array(COLORS['grain_boundary'])/255, label='Grain Boundary'),
                Patch(color=np.array(COLORS['background'])/255, label='Ledeburite matrix')
            ]
            ax_leg.legend(handles=patches, loc='center', fontsize=8, frameon=False)
            plt.show()
    
    def on_generate(b):
        with animation_output:
            clear_output(wait=True)
            try:
                if profile_type.value == 'Temperature profile':
                    fixed_c = fixed_input.value
                    start = start_input.value
                    end = end_input.value
                    step_mag = step_input.value
                    if step_mag <= 0:
                        print("Step must be positive.")
                        return
                    temp_range = (start, end, step_mag)
                    print("Generating animation (this may take a few seconds due to grain generation)...")
                    anim_html = animate_temperature_profile(fixed_c, temp_range, interval=200)
                    if anim_html:
                        display(anim_html)
                else:
                    fixed_t = fixed_input.value
                    start_c = start_input.value
                    end_c = end_input.value
                    step = step_input.value
                    if step <= 0:
                        print("Step must be positive.")
                        return
                    carbon_range = (start_c, end_c, step)
                    print("Generating animation (this may take a few seconds due to grain generation)...")
                    anim_html = animate_carbon_profile(fixed_t, carbon_range, interval=200)
                    if anim_html:
                        display(anim_html)
            except Exception as e:
                print(f"Error: {e}")
    
    generate_btn.on_click(on_generate)
    
    show_legend()
    
    return dashboard