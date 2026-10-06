# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 12:03:27 2026
Diagram Oluşturma
@author: Elif
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#Grid Ekleme
grid = pypsa.Network(name ='GRID')

#Bus Ekleme
grid.add(
    class_name= 'Bus',
    name='LV_1',
    v_nom = 0.4,
    x=2, y=0)

grid.add(
    class_name= 'Bus',
    name='LV_2',
    v_nom = 0.4,
    x=1, y=0)

grid.add(
    class_name= 'Bus',
    name='MV_1',
    v_nom = 20,
    x=0, y=0)

#Line ekleme
grid.add(
    class_name= 'Line',
    name='Line #2',
    bus0 = 'LV_1',
    bus1 = 'LV_2',
    x=0.2,
    r=0.02,
    )

# Tranformatör ekleme
grid.add(
    class_name= 'Transformer',
    name='MV-LV trafo',
    type='0.63 MVA 20/0.4 kV',
    bus0 = 'MV_1',
    bus1= 'LV_2')

#Generatör ekleme
grid.add(
    class_name= 'Generator',
    name='External Grid',
    bus='MV_1',
    p_set=0.1,
    control = 'Slack')

#Yuk
grid.add(
    class_name= 'Load',
    name='load_1',
    bus = 'LV_1',
    p_set=0.1,
    q_set = 0.05)

#Yük akışı
def loadflow():
    grid.lpf()
    grid.pf(use_seed =True)
    return pd.DataFrame(
        {
            "Voltage Angles" : grid.buses_t.v_ang.loc['now']*180/np.pi,
            "Voltage Magnitude" : grid.buses_t.v_mag_pu.loc["now"],
            })

results = loadflow()
print(results)

#Tek hat şeması
def single_line_diagram():
    fig, ax = plt.subplots(figsize=(11, 4))
    bx = {'MV_1': 0, 'LV_2': 4, 'LV_1': 8}

    # Baralar (kalın dikey çizgi) + isim, nominal gerilim, pu gerilim
    for b, x in bx.items():
        ax.plot([x, x], [-1, 1], lw=6, color='k')
        ax.text(x, 1.25, f"{b}\n{grid.buses.at[b, 'v_nom']} kV",
                ha='center', va='bottom')
        ax.text(x, -1.3, f"{results.at[b, 'Voltage Magnitude']:.3f} pu\n"
                         f"{results.at[b, 'Voltage Angles']:.2f}°",
                ha='center', va='top', color='tab:blue')

    # Dış şebeke (slack) -> MV_1
    ax.plot([-1.5, 0], [0, 0], 'k')
    ax.add_patch(plt.Circle((-2, 0), 0.5, fill=False))
    ax.text(-2, 0, '~', ha='center', va='center', fontsize=18)
    ax.text(-2, -0.9, 'External Grid', ha='center', va='top')

    # Trafo: MV_1 -> LV_2 (iki iç içe daire)
    ax.plot([0, 1.3], [0, 0], 'k')
    ax.plot([2.7, 4], [0, 0], 'k')
    ax.add_patch(plt.Circle((1.8, 0), 0.5, fill=False))
    ax.add_patch(plt.Circle((2.2, 0), 0.5, fill=False))
    ax.text(2, 0.8, 'MV-LV trafo\n0.63 MVA', ha='center', va='bottom')

    # Hat: LV_2 -> LV_1 (dikdörtgen sembol)
    ax.plot([4, 5.5], [0, 0], 'k')
    ax.plot([6.5, 8], [0, 0], 'k')
    ax.add_patch(plt.Rectangle((5.5, -0.2), 1, 0.4, fill=False))
    ax.text(6, 0.4, 'Line #2', ha='center', va='bottom')

    # Yük: LV_1
    ax.annotate('', xy=(10.5, 0), xytext=(8, 0),
                arrowprops=dict(arrowstyle='-|>', color='k', lw=1.5))
    ax.text(9.3, 0.2, f"{grid.loads.at['load_1', 'p_set']} MW\n"
                      f"{grid.loads.at['load_1', 'q_set']} MVAr",
            ha='center', va='bottom')

    ax.set_xlim(-3, 11)
    ax.set_ylim(-2.5, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Tek Hat Şeması (GRID)")
    plt.show()

single_line_diagram()