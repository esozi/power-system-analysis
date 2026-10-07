# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 13:46:26 2026

@author: Elif
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

network = pypsa.Network()

nbus = 7
for i in range(nbus):
    network.add('Bus',
                'Bus No {}'.format(i),
                v_nom=100,
                x=i * 2, y=0)          # şema için koordinat

# iletim hattı
for i in range(nbus - 1):
    network.add('Line',
                'Line No {}'.format(i),
                bus0='Bus No {}'.format(i),
                bus1='Bus No {}'.format(i + 1),
                r=0.3,
                x=3)

# generator ekleme
network.add('Generator',
            'Slack Gen',
            bus='Bus No 0',
            p_set=0,
            control='Slack')  # enterkonnekte sebeke
network.add('Generator',
            'Gen No 1',
            bus='Bus No 2',
            p_set=100,
            control='PV')

# yük ekleme
network.add('Load',
            'Load No 1',
            bus='Bus No 5',
            p_set=85,
            q_set=40)

network.pf()

print(network)
print(network.buses_t.v_mag_pu)
print(network.lines_t.p0)
print(network.generators_t.p)
print(network.generators_t.q)

# ---------------- Sonuçlar ----------------
v_mag = network.buses_t.v_mag_pu.loc['now']
line_p = network.lines_t.p0.loc['now']
gen_p = network.generators_t.p.loc['now']
gen_q = network.generators_t.q.loc['now']
pos = {b: (network.buses.at[b, 'x'], network.buses.at[b, 'y'])
       for b in network.buses.index}

# ---------------- 1) Şebeke şeması ----------------
fig, ax = plt.subplots(figsize=(14, 4.5))

# Hatlar + güç akışı okları
for l in network.lines.index:
    b0, b1 = network.lines.at[l, 'bus0'], network.lines.at[l, 'bus1']
    (x0, y0), (x1, y1) = pos[b0], pos[b1]
    ax.plot([x0, x1], [y0, y1], 'k', lw=2.5, zorder=1)

    p = line_p[l]
    if p < 0:                               # akış bus1 -> bus0
        x0, y0, x1, y1 = x1, y1, x0, y0
    mx = (x0 + x1) / 2
    d = 0.3 if x1 > x0 else -0.3
    ax.annotate('', xy=(mx + d, 0), xytext=(mx - d, 0),
                arrowprops=dict(arrowstyle='-|>', color='tab:red', lw=2),
                zorder=3)
    ax.text(mx, 0.25, f"{abs(p):.1f} MW", ha='center', color='tab:red',
            fontsize=9)

# Baralar + gerilimler
for b, (x, y) in pos.items():
    ax.scatter(x, y, s=350, c='k', zorder=4)
    ax.text(x, y - 0.45, f"{b.replace('Bus No ', 'Bus ')}\n{v_mag[b]:.4f} pu",
            ha='center', va='top', color='tab:blue', fontsize=9)

# Generatörler (barada yukarı)
for g in network.generators.index:
    b = network.generators.at[g, 'bus']
    x, y = pos[b]
    ax.plot([x, x], [y, y + 0.9], 'k', lw=2)
    ax.add_patch(plt.Circle((x, y + 1.25), 0.35, fill=False, lw=2))
    ax.text(x, y + 1.25, '~', ha='center', va='center', fontsize=16)
    ax.text(x, y + 1.8, f"{g}\n{gen_p[g]:.1f} MW / {gen_q[g]:.1f} MVAr",
            ha='center', va='bottom', fontsize=9)

# Yük (barada aşağı ok)
for ld in network.loads.index:
    b = network.loads.at[ld, 'bus']
    x, y = pos[b]
    ax.annotate('', xy=(x, y - 1.7), xytext=(x, y - 1.0),
                arrowprops=dict(arrowstyle='-|>', color='k', lw=2))
    ax.text(x, y - 1.85, f"{ld}\n{network.loads.at[ld, 'p_set']} MW / "
                         f"{network.loads.at[ld, 'q_set']} MVAr",
            ha='center', va='top', fontsize=9)

ax.set_aspect('equal')
ax.set_xlim(-1.5, 13.5)
ax.set_ylim(-3.3, 3.3)
ax.axis('off')
ax.set_title("7 Baralı İletim Şebekesi")
plt.show()

# ---------------- 2) Grafikler ----------------
fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))

x = np.arange(len(gen_p))
w = 0.35
axs[0].bar(x - w/2, gen_p.values, w, label='P (MW)')
axs[0].bar(x + w/2, gen_q.values, w, label='Q (MVAr)')
axs[0].set_xticks(x)
axs[0].set_xticklabels(gen_p.index)
axs[0].axhline(0, color='k', lw=0.8)
axs[0].set_title('Generatör çıkışları')
axs[0].legend()

axs[1].plot(range(len(v_mag)), v_mag.values, marker='o')
axs[1].set_xticks(range(len(v_mag)))
axs[1].set_xticklabels([b.replace('Bus No ', 'B') for b in v_mag.index])
axs[1].axhline(0.95, color='r', ls='--', lw=1)
axs[1].axhline(1.05, color='r', ls='--', lw=1)
axs[1].set_title('Bara gerilimleri (pu)')

axs[2].bar(range(len(line_p)), line_p.values)
axs[2].set_xticks(range(len(line_p)))
axs[2].set_xticklabels([l.replace('Line No ', 'L') for l in line_p.index])
axs[2].axhline(0, color='k', lw=0.8)
axs[2].set_title('Hat aktif güç akışı (MW)')

plt.tight_layout()
plt.show()