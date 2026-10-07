# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 17:02:08 2026

@author: Elif
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

network = pypsa.Network()

n_buses = 3

# Bara koordinatları (üçgen yerleşim)
coords = [(0, 0), (4, 0), (2, 3)]

# Bara oluşturma
for i in range(n_buses):
    network.add('Bus', 'Bus_P{}'.format(i), v_nom=20.0,
                x=coords[i][0], y=coords[i][1])

# Hat oluşturma (halka)
for i in range(n_buses):
    network.add(
        'Line',
        'Line_P{}'.format(i),
        bus0='Bus_P{}'.format(i),
        bus1='Bus_P{}'.format((i + 1) % n_buses),
        x=1.0,
        r=0.1)

# Generatör ekleme
network.add('Generator', 'Gen1', bus='Bus_P0', p_set=100,
            control='Slack')

# Yük ekleme
network.add('Load', 'Load_1', bus='Bus_P1', p_set=95)

# Yük akışı
network.pf()

print(network)
print(network.buses_t.v_mag_pu)
print(network.lines_t.p0)

# ---------------- Görselleştirme ----------------
v = network.buses_t.v_mag_pu.loc['now']
flows = network.lines_t.p0.loc['now']
pos = {b: (network.buses.at[b, 'x'], network.buses.at[b, 'y'])
       for b in network.buses.index}

fig, ax = plt.subplots(figsize=(8, 6))

# Hatlar + güç akışı okları
for l in network.lines.index:
    b0, b1 = network.lines.at[l, 'bus0'], network.lines.at[l, 'bus1']
    (x0, y0), (x1, y1) = pos[b0], pos[b1]
    ax.plot([x0, x1], [y0, y1], 'k', lw=2, zorder=1)

    p = flows[l]
    if p < 0:                       # akış yönü bus1 -> bus0
        x0, y0, x1, y1 = x1, y1, x0, y0
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = (x1 - x0) * 0.08, (y1 - y0) * 0.08
    ax.annotate('', xy=(mx + dx, my + dy), xytext=(mx - dx, my - dy),
                arrowprops=dict(arrowstyle='-|>', color='tab:red', lw=2),
                zorder=3)
    ax.text(mx, my + 0.25, f"{l}\n{abs(p):.1f} MW", ha='center',
            va='bottom', color='tab:red', fontsize=9)

# Baralar + gerilimler
for b, (x, y) in pos.items():
    ax.scatter(x, y, s=300, c='k', zorder=4)
    ax.text(x, y - 0.35, f"{b}\n{v[b]:.4f} pu", ha='center', va='top',
            color='tab:blue')

# Generatör (Bus_P0)
x, y = pos['Bus_P0']
ax.add_patch(plt.Circle((x - 1, y), 0.35, fill=False, lw=2))
ax.text(x - 1, y, '~', ha='center', va='center', fontsize=16)
ax.plot([x - 0.65, x], [y, y], 'k', lw=2)
ax.text(x - 1, y + 0.5, 'Gen1', ha='center')

# Yük (Bus_P1)
x, y = pos['Bus_P1']
ax.annotate('', xy=(x + 1.2, y), xytext=(x, y),
            arrowprops=dict(arrowstyle='-|>', color='k', lw=2))
ax.text(x + 1.2, y + 0.15, f"Load_1\n{network.loads.at['Load_1', 'p_set']} MW",
        ha='left', va='bottom')

ax.set_aspect('equal')
ax.set_xlim(-2, 6)
ax.set_ylim(-1.5, 4)
ax.axis('off')
ax.set_title("3 Baralı Halka Şebeke")
plt.show()