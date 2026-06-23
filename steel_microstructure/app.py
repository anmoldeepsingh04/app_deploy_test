import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "steel_microstructure"))

import streamlit as st
import matplotlib.pyplot as plt

from simulator import create_unified_simulator, COLORS

st.set_page_config(page_title="Iron-Carbon Microstructure Simulator", layout="wide")

st.title("🔩 Iron-Carbon Phase Diagram Microstructure Simulator")
st.write(
    "Pick a carbon percentage and a temperature to see what the metal's "
    "microstructure looks like at that point on the iron-carbon phase diagram."
)

# ----------------------------------------------------------------------
# SIDEBAR = the user's INPUTS. Nothing here can run arbitrary code -
# the user can only move sliders / pick dropdown values.
# ----------------------------------------------------------------------
st.sidebar.header("Inputs")

carbon_percent = st.sidebar.slider(
    "Carbon content (%)", min_value=0.0, max_value=6.67, value=0.4, step=0.01
)
temperature = st.sidebar.slider(
    "Temperature (°C)", min_value=20, max_value=1600, value=700, step=5
)

show_legend = st.sidebar.checkbox("Show color legend", value=True)

# ----------------------------------------------------------------------
# OUTPUT = build the simulator + image fresh every time an input changes.
# Streamlit re-runs this whole script top to bottom on every interaction.
# ----------------------------------------------------------------------
with st.spinner("Generating microstructure..."):
    simulator = create_unified_simulator(carbon_percent)
    image, state = simulator.generate_microstructure(temperature)

col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.imshow(image)
    ax.axis("off")
    ax.set_title(f"{carbon_percent:.2f}% C at {temperature}°C\n{state['description']}")
    st.pyplot(fig)

with col2:
    st.subheader("Phase info")
    st.write(f"**Phase:** {state['description']}")
    st.write(f"**Carbon:** {carbon_percent:.2f}%")
    st.write(f"**Temperature:** {temperature}°C")
    st.write(f"**Simulator used:** {simulator.describe()}")

    if show_legend:
        st.subheader("Legend")
        for name, rgb in COLORS.items():
            hex_color = '#%02x%02x%02x' % rgb
            st.markdown(
                f"<div style='display:flex;align-items:center;margin-bottom:4px;'>"
                f"<div style='width:18px;height:18px;background:{hex_color};"
                f"margin-right:8px;border:1px solid #333;'></div>{name}</div>",
                unsafe_allow_html=True,
            )

st.divider()
st.caption(
    "This app only exposes inputs and outputs - the underlying simulation "
    "code is not visible to visitors of the website."
)
