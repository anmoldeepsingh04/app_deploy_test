# Iron-Carbon Phase Diagram Microstructure Simulator

This is a Python script (meant to run in a **Jupyter Notebook**) that simulates and animates what the *microstructure* of iron-carbon alloys (steel and cast iron) looks like as it cools from molten metal (1600°C) all the way down to room temperature.

If you've ever taken a materials science / metallurgy class, you've seen the famous **iron-carbon phase diagram**. This code turns that diagram into a visual, interactive simulation — instead of just reading "at this temperature and carbon %, you get pearlite," you actually *see* a picture of what that looks like under a microscope.

No prior knowledge of metallurgy or this codebase is assumed below — everything is explained from scratch.

---

## 1. The big picture, in plain English

1. You pick a **carbon percentage** (e.g. 0.2% — typical mild steel) and a **temperature**.
2. The script calculates which "phase" (form) the iron is in at that temperature, using real metallurgical formulas.
3. It then draws a synthetic picture (like a microscope image) of what the metal's internal structure looks like — colored regions representing things like liquid metal, ferrite, austenite, cementite, or pearlite.
4. It can also **animate** this as the temperature drops (or as carbon % changes), and display the animation right inside a Jupyter notebook with interactive buttons and sliders.

Think of it like a weather simulator, but instead of predicting clouds and rain, it predicts what crystals/grains form inside a piece of metal as it cools.

---

## 2. Some quick metallurgy background

You don't need to memorize this, but it helps to know what the colors/words mean:

| Term | What it means |
|---|---|
| **Liquid (L)** | Molten metal, no solid structure yet |
| **δ-ferrite (delta)** | A high-temperature solid iron form (BCC crystal structure) |
| **Austenite (γ / gamma)** | A solid iron form stable at medium-high temperatures (FCC crystal structure) — can dissolve more carbon than ferrite |
| **α-ferrite (alpha)** | The low-temperature solid iron form, same crystal structure as δ but stable when cool |
| **Cementite (Fe₃C)** | Iron carbide — a hard, brittle compound that forms when there's "extra" carbon |
| **Pearlite** | A striped/banded mixture of ferrite + cementite that forms during a specific transformation at 723°C and below |
| **Grain** | A single crystal region in the metal — metals are made of many small grains packed together, like a tiled floor |
| **Grain boundary** | The edge where two grains meet (often drawn in black) |

The script's job is to figure out, at any (carbon %, temperature) pair, which of these phases exist and roughly how they're arranged.

---

## 3. File structure overview

The script is organized into clear sections (look for the `# ==========` comment banners):

```
1. Imports
2. Global COLORS dictionary
3. IronCarbonPhaseDiagramSimulator   -> handles 0% - 0.53% carbon (low-carbon steels)
4. SteelMicrostructureSimulator      -> handles 0.53% - 2.06% carbon (higher-carbon steels)
5. GeneralizedSteel                  -> handles 2.06% - 6.67% carbon (cast irons)
6. create_unified_simulator()        -> picks the right class automatically
7. plot_key_transitions()            -> static grid of images, one alloy cooling down
8. plot_carbon_profile()             -> static grid, comparing different carbon %
9. animate_temperature_profile()     -> animated cooling sequence
10. animate_carbon_profile()         -> animated carbon-percentage sweep
11. Phase boundary formulas (liquidus, solidus, A3, Acm, etc.)
12. create_dashboard()               -> interactive ipywidgets UI
13. "Fast" lookup functions          -> quick numeric answers, no images
14. Main entry point                 -> launches the dashboard
```

Each carbon range needs **its own class** because the real phase diagram has genuinely different physics/equations in each region — there's no single formula that covers 0% to 6.67% carbon.

---

## 4. The three simulator classes (the heart of the code)

All three classes (`IronCarbonPhaseDiagramSimulator`, `SteelMicrostructureSimulator`, `GeneralizedSteel`) follow the same recipe:

### Step A — Calculate transition temperatures
Real metallurgical research has produced polynomial equations that approximate the boundary lines of the phase diagram (e.g. "Liquidus" — the temperature above which everything is liquid, or "Eutectoid temperature" — fixed at 723°C). The `__init__` and `_calculate_*_temperatures()` methods plug in your chosen carbon % and compute these temperatures.

### Step B — Generate a "grain" map
Real metal isn't a single uniform crystal — it's made of many small, randomly shaped & sized **grains**, similar to the cells in a honeycomb or the patches on a cracked mud surface.

`_create_grain_structure()` fakes this:
1. It randomly samples points across the image.
2. It runs **k-means clustering** (`sklearn.cluster.KMeans`) on those points, which naturally partitions the image into blob-like regions — this becomes the grain map (like a Voronoi diagram).

This grain map is the "skeleton" reused throughout the simulation — different phases just recolor or reshape it.

### Step C — Decide the phase at a given temperature
`get_phase_region()` (or `get_transformation_state()` in the other classes) is essentially a big decision tree:
- "Is the temperature above the liquidus? → It's all Liquid."
- "Is it between the eutectoid temperature and a lower value? → Pearlite is forming, X% complete."
- ...and so on.

It returns a small dictionary describing what phase(s) are present and how to draw them (e.g. whether grain boundaries should be visible, how much grains should "shrink" to represent a new phase nucleating, etc.).

### Step D — Paint the picture
`generate_microstructure(temperature)` is where the actual image is built:
- It starts with a blank canvas colored with the background.
- Based on the phase from Step C, it colors the grains with the right COLORS (liquid, ferrite, austenite...).
- For phases where one structure is "eating into" another (e.g., ferrite forming inside austenite as it cools), it **shrinks the grains** using image erosion (`scipy.ndimage.binary_erosion`) to simulate growth from grain boundaries inward.
- For **pearlite**, it draws alternating thin stripes of ferrite and cementite at a 45° angle inside each grain (`_create_pearlite_in_all_grains`) — this mimics the real striped/lamellar look of pearlite under a microscope.
- For **cementite particles**, it stamps small filled circles with black outlines at fixed positions along grain-boundary "channels" (`_draw_cementite_grains`).
- Finally, it draws black grain-boundary lines on top.

The result, `micro`, is just a NumPy array of shape `(height, width, 3)` — an RGB image — that matplotlib can display directly.

---

## 5. The "picker" function

```python
create_unified_simulator(carbon_percent, **kwargs)
```
You almost never need to manually choose which of the 3 classes to use — this function does it for you based on the carbon percentage you give it (≤0.53%, 0.53–2.06%, or >2.06%).

---

## 6. Visualization functions

- **`plot_key_transitions(carbon_percent)`** — creates one alloy and draws a grid of static snapshots at each meaningful temperature as it cools from 1600°C to 20°C. Good for seeing the whole "life story" of one specific steel composition at a glance.

- **`plot_carbon_profile(temperature)`** — fixes the temperature and instead varies the carbon %, showing a row of different alloys side-by-side at that one moment. Good for comparing, e.g., what 0% carbon vs 4.3% carbon looks like at 1000°C.

- **`animate_temperature_profile(carbon_percent, temp_range)`** — generates a real animation: it computes the microstructure image at many temperatures (using your start/end/step), then strings them into a `matplotlib.animation.FuncAnimation`, converted to HTML5/JS so it plays inline in a notebook (`anim.to_jshtml()`).

- **`animate_carbon_profile(fixed_temperature, carbon_range)`** — same idea, but instead it sweeps across carbon percentages at one fixed temperature.

Both animation functions temporarily redirect the simulator's normal `print()` statements to a `DummyWriter` (lines ~1363) so the notebook output isn't flooded with text while frames are being generated.

---

## 7. The interactive dashboard

`create_dashboard()` builds a little app inside your Jupyter notebook using `ipywidgets`:

- A dropdown to choose **"Temperature profile"** (animate cooling at fixed carbon %) or **"Carbon profile"** (animate across carbon % at fixed temperature).
- Number input boxes that change their labels/defaults depending on which mode you pick.
- A **"Generate Animation"** button — clicking it calls `animate_temperature_profile()` or `animate_carbon_profile()` behind the scenes and displays the result.
- A **legend panel** on the right showing what each color means, built using `matplotlib.patches.Patch`.

At the very bottom:
```python
if __name__ == "__main__":
    dashboard = create_dashboard()
    display(dashboard)
```
This means: if you run the whole script directly inside a Jupyter notebook cell, it will automatically pop up the dashboard for you to interact with.

---

## 8. "Fast" helper functions (no images, just numbers)

Near the bottom of the file there's a second, lightweight set of functions that mirror the temperature-calculating logic from the classes, but **without** building a full simulator or generating an image:

- `get_transition_temperatures_low_carbon(C)`, `..._steel(C)`, `..._cast(C)` — return a list of `(description, temperature)` pairs for a given carbon %.
- `show_transition_info_fast(carbon)` — prints those transition temperatures.
- `get_carbon_transitions(temp)` — does the reverse: given a *temperature*, it numerically solves (using `scipy.optimize.root_scalar`) for which carbon percentages sit on a phase boundary at that temperature.

These exist for quick numeric answers when you don't need a picture — e.g. "what carbon % values matter at 800°C?"

---

## 9. How to actually run this

1. Open it in a Jupyter Notebook (or JupyterLab / Google Colab).
2. Make sure these packages are installed: `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `ipywidgets`.
3. Run the whole script in one cell (or run the whole `.py`/`.ipynb` file).
4. Either:
   - Call `dashboard = create_dashboard(); display(dashboard)` and use the buttons, **or**
   - Call functions manually, e.g.:
     ```python
     plot_key_transitions(0.2)              # static images, 0.2% carbon steel cooling down
     plot_carbon_profile(800)                # compare alloys at 800°C
     animate_temperature_profile(0.4, (1600, 20, 40))   # animated cooling, 0.4% C
     animate_carbon_profile(800, (0.0, 6.67, 0.1))      # animated carbon sweep at 800°C
     ```

> **Note:** This script relies on `ipywidgets` and IPython display features (`HTML`, `display`, `clear_output`), so it must be run inside a Jupyter-style environment — it won't produce interactive output in a plain terminal/script run.

---

## 10. Glossary of key variables/functions (cheat sheet)

| Name | What it is |
|---|---|
| `COLORS` | Dictionary mapping phase names to RGB colors |
| `carbon_percent` | The wt% carbon in the iron alloy you're simulating |
| `original_grain_map` | 2D array where each pixel holds an integer grain ID |
| `get_phase_region()` / `get_transformation_state()` | Decides which phase(s) exist at a temperature |
| `generate_microstructure()` | Builds the actual RGB image for a given temperature |
| `_shrink_grains_for_channels()` | Erodes grains inward to simulate a new phase nucleating at boundaries |
| `_create_pearlite_in_all_grains()` | Draws the striped ferrite/cementite pattern of pearlite |
| `_draw_cementite_grains()` | Stamps round cementite particles at fixed positions |
| `create_unified_simulator()` | Auto-selects the right simulator class for your carbon % |
| `create_dashboard()` | Builds the interactive Jupyter widget UI |

---

## TL;DR

This script is a **scientifically-grounded, visual "metal cooling" simulator**. You give it a carbon percentage, and it shows you — as a picture or animation — what's happening inside the metal at any temperature as it cools from molten (1600°C) to room temperature, using real phase-diagram equations and a synthetic grain structure for realism.
