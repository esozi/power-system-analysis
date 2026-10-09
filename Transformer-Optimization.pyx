# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 16:16:45 2026

@author: Elif
"""

import pypsa
import pandas as pd
import numpy as np

network = pypsa.Network(name="Electrical Grid")

# Buses
network.add("Bus", "MV bus", v_nom=20, v_mag_pu_set=1.01)
network.add("Bus", "LV1 bus", v_nom=0.4)
network.add("Bus", "LV2 bus", v_nom=0.4)

# Transformer
network.add(
    "Transformer",
    "MV-LV Trafo",
    type="0.4 MVA 20/0.4 kV",
    bus0="MV bus",
    bus1="LV1 bus",
)

# Cable
network.add(
    "Line",
    "LV Cable",
    type="NAYY 4x50 SE",
    bus0="LV1 bus",
    bus1="LV2 bus",
    length=0.1,  # km
)

# External grid (slack)
network.add(
    "Generator",
    "External Grid",
    bus="MV bus",
    control="Slack",
    marginal_cost=10,
)

# Load
network.add(
    "Load",
    "LV Load",
    bus="LV2 bus",
    p_set=0.1,   # MW
    q_set=0.05,  # MVar
)


def rpff():
    network.lpf()
    network.pf(use_seed=True)
    return pd.DataFrame(
        {
            "Voltage Angle": network.buses_t.v_ang.loc["now"] * 180.0 / np.pi,
            "Voltage Magnitude": network.buses_t.v_mag_pu.loc["now"],
        }
    )


# First scenario
network.transformers.loc["MV-LV Trafo", "tap_position"] = 2
print(rpff())