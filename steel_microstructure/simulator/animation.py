# ==================== ANIMATION FUNCTIONS (silenced with DummyWriter) ====================
class DummyWriter:
    def write(self, s): pass
    def flush(self): pass

def animate_temperature_profile(carbon_percent, temp_range, interval=200, **kwargs):
    start, end, step_mag = temp_range
    if start > end:
        step = -abs(step_mag)
    else:
        step = abs(step_mag)

    temps = np.arange(start, end + step/2, step)
    if len(temps) == 0:
        print("Error: No temperatures generated. Check start, end, and step.")
        return

    # Suppress simulator print during creation using dummy writer
    with redirect_stdout(DummyWriter()):
        sim = create_unified_simulator(carbon_percent, **kwargs)
    
    frames = []
    titles = []
    for T in temps:
        m, s = sim.generate_microstructure(T)
        frames.append(m)
        titles.append(f"{T:.0f}°C: {s['description']}")

    fig, ax = plt.subplots(figsize=(6,5))
    ax.axis('off')
    im = ax.imshow(frames[0])
    title = ax.set_title(titles[0], fontsize=10, fontweight='bold')

    def update(idx):
        im.set_array(frames[idx])
        title.set_text(titles[idx])
        return [im, title]

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=interval, blit=True)
    plt.close()
    return HTML(anim.to_jshtml())

def animate_carbon_profile(fixed_temperature, carbon_range, interval=200, **kwargs):
    start, end, step = carbon_range
    if step <= 0:
        print("Error: Step must be positive for carbon range.")
        return

    carbons = np.arange(start, end + step/2, step)
    carbons = [c for c in carbons if 0 <= c <= 6.67]
    if len(carbons) == 0:
        print("Error: No carbon values in range 0–6.67. Check start, end, step.")
        return

    frames = []
    titles = []
    for C in carbons:
        # Suppress simulator print for each creation
        with redirect_stdout(DummyWriter()):
            sim = create_unified_simulator(C, **kwargs)
        m, s = sim.generate_microstructure(fixed_temperature)
        frames.append(m)
        titles.append(f"{C:.2f}% C: {s['description']}")

    fig, ax = plt.subplots(figsize=(6,5))
    ax.axis('off')
    im = ax.imshow(frames[0])
    title = ax.set_title(titles[0], fontsize=10, fontweight='bold')

    def update(idx):
        im.set_array(frames[idx])
        title.set_text(titles[idx])
        return [im, title]

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=interval, blit=True)
    plt.close()
    return HTML(anim.to_jshtml())