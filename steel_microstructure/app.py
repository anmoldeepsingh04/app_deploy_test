import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "steel_microstructure"))

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from simulator import create_unified_simulator, COLORS


# =============================================================================
# HELPER: Carbon regime label
# Takes a carbon percentage and returns the named region on the Fe-C diagram.
# =============================================================================
def get_carbon_regime(carbon_percent):
    if carbon_percent <= 0.02:
        return "Pure Iron / Nearly Pure Iron"
    elif carbon_percent < 0.76:
        return "Hypoeutectoid Steel"
    elif abs(carbon_percent - 0.76) < 0.01:
        return "Eutectoid Steel"
    elif carbon_percent <= 2.06:
        return "Hypereutectoid Steel"
    elif carbon_percent < 4.3:
        return "Hypoeutectic Cast Iron"
    elif abs(carbon_percent - 4.3) < 0.01:
        return "Eutectic Cast Iron"
    else:
        return "Hypereutectic Cast Iron"


# =============================================================================
# PHASE DIAGRAM CALIBRATION
#
# These 6 constants map data coordinates (carbon %, temperature °C) to pixel
# coordinates in the image oriIron_carbon_phase_diagram.jpg.
#
# How they were found:
#   - COL_LEFT / COL_RIGHT: column of the y-axis and right end of x-axis
#   - ROW_TOP / ROW_BOTTOM: row of the topmost and bottommost content on y-axis
#   - T_TOP / T_BOTTOM: the temperatures those rows correspond to
#
# If you ever switch to a different image, update these 6 numbers by opening
# the new image in any image editor and hovering over the equivalent points.
# =============================================================================

# COL_LEFT   = int(700  * SCALE)
# COL_RIGHT  = int(7755 * SCALE)
# ROW_TOP    = int(185  * SCALE)
# ROW_BOTTOM = int(5063 * SCALE)


COL_LEFT   = 175    # pixel x of the y-axis line  → carbon = 0%
COL_RIGHT  = 1938   # pixel x of the right end of x-axis → carbon = 6.67%
ROW_TOP    = 46    # pixel y of the top of the y-axis → temperature = T_TOP
ROW_BOTTOM = 1265   # pixel y of the x-axis line → temperature = T_BOTTOM
T_TOP      = 1600   # °C at the top of the diagram
T_BOTTOM   = 20     # °C at the bottom of the diagram
C_MAX      = 6.67   # maximum carbon % on the diagram


def data_to_pixel(carbon, temperature):
    """
    Convert a (carbon%, temperature) data point into (pixel_x, pixel_y)
    coordinates on the phase diagram image.

    The x mapping is a straight linear interpolation from carbon 0→6.67%
    to pixel COL_LEFT→COL_RIGHT.

    The y mapping is also linear but INVERTED — high temperature is near
    the TOP of the image (small pixel y) and low temperature is near the
    BOTTOM (large pixel y). That is why we write (T_TOP - temperature)
    instead of just temperature.
    """
    px = COL_LEFT + (carbon / C_MAX) * (COL_RIGHT - COL_LEFT)
    py = ROW_TOP + ((T_TOP - temperature) / (T_TOP - T_BOTTOM)) * (ROW_BOTTOM - ROW_TOP)
    return px, py


# =============================================================================
# PAGE SETUP
# =============================================================================
st.set_page_config(page_title="Iron-Carbon Microstructure Simulator", layout="wide")

st.title("🔩 Iron-Carbon Phase Diagram Microstructure Simulator")
st.write(
    "Pick a carbon percentage and a temperature to see what the metal's "
    "microstructure looks like at that point on the iron-carbon phase diagram."
)


# =============================================================================
# SIDEBAR — INPUTS
# =============================================================================
st.sidebar.header("Inputs")

carbon_percent = st.sidebar.slider(
    "Carbon content (%)", min_value=0.0, max_value=6.67, value=0.4, step=0.01
)
temperature = st.sidebar.slider(
    "Temperature (°C)", min_value=20, max_value=1600, value=700, step=5
)
show_legend = st.sidebar.checkbox("Show color legend", value=True)


# =============================================================================
# RUN SIMULATION
# Streamlit re-runs this whole script top-to-bottom every time a slider moves.
# =============================================================================
with st.spinner("Generating microstructure..."):
    simulator = create_unified_simulator(carbon_percent)
    image, state = simulator.generate_microstructure(temperature)


# =============================================================================
# SIDEBAR — PHASE INFO
# =============================================================================
st.sidebar.header("Phase Info")
st.sidebar.write(f"**Phase:** {state['description']}")
st.sidebar.write(f"**Carbon:** {carbon_percent:.2f} wt%")
st.sidebar.write(f"**Temperature:** {temperature} °C")
st.sidebar.write(f"**Simulator:** {simulator.describe()}")

# --- Carbon regime (new Feature 1) ---
st.sidebar.header("Carbon Regime")
regime = get_carbon_regime(carbon_percent)
st.sidebar.info(f"**{regime}**")


# =============================================================================
# SIDEBAR — LEGEND (moved here from col2 to free up col2 for the phase diagram)
# =============================================================================
if show_legend:
    st.sidebar.header("Legend")
    for name, rgb in COLORS.items():
        hex_color = '#%02x%02x%02x' % rgb
        st.sidebar.markdown(
            f"<div style='display:flex;align-items:center;margin-bottom:4px;'>"
            f"<div style='width:18px;height:18px;background:{hex_color};"
            f"margin-right:8px;border:1px solid #333;'></div>{name}</div>",
            unsafe_allow_html=True,
        )


# =============================================================================
# MAIN AREA — TWO COLUMNS
# col1: microstructure image (unchanged from before)
# col2: phase diagram with moving crosshair (new Feature 2)
# =============================================================================
col1, col2 = st.columns([1.8, 2])

# --- Column 1: Microstructure ---
with col1:
    st.subheader("Microstructure")
    fig1, ax1 = plt.subplots(figsize=(6, 4.5))
    ax1.imshow(image)
    ax1.axis("off")
    ax1.set_title(
        f"{carbon_percent:.2f}% C at {temperature}°C\n{state['description']}",
        fontsize=10
    )
    st.pyplot(fig1)
    plt.close(fig1)   # always close figures in Streamlit to free memory


# --- Column 2: Phase diagram with crosshair ---
with col2:
    st.subheader("Fe-C Phase Diagram")

    # Build the absolute path to the image so it works regardless of which
    # directory Streamlit is launched from.
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    diagram_path = os.path.join(assets_dir, "Iron_carbon_phase_diagram.jpg")

    # Load the image as a numpy array so matplotlib can display it.
    # Image file is already pre-resized to ~2000px wide — load it directly.
    diagram_img = np.array(Image.open(diagram_path))

    # Compute where on the image the current (carbon, temperature) point is.
    px, py = data_to_pixel(carbon_percent, temperature)

    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    ax2.imshow(diagram_img)
    ax2.axis("off")

    # --- Draw the crosshair (new Feature 2) ---
    # Vertical dashed line — runs the full height of the image at the
    # carbon% position, indicating the carbon column.
    ax2.axvline(
        x=px,
        color='red', linewidth=1.5, linestyle='--', alpha=0.85,
        label=f"{carbon_percent:.2f}% C"
    )

    # Horizontal dashed line — runs the full width of the image at the
    # temperature position, indicating the temperature row.
    ax2.axhline(
        y=py,
        color='red', linewidth=1.5, linestyle='--', alpha=0.85,
        label=f"{temperature}°C"
    )

    # Red dot at the exact intersection of the two lines.
    ax2.plot(
        px, py,
        marker='o', color='red', markersize=8,
        markeredgecolor='darkred', markeredgewidth=1.5
    )

    ax2.set_title(
        f"Current point: {carbon_percent:.2f}% C, {temperature}°C  |  {regime}",
        fontsize=10
    )

    st.pyplot(fig2)
    plt.close(fig2)


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption(
    "This app only exposes inputs and outputs — the underlying simulation "
    "code is not visible to visitors of the website."
)