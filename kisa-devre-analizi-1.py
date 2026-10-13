# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 23:37:36 2026

@author: Elif
"""

import pandapower as pp
import pandapower.shortcircuit as sc
import matplotlib.pyplot as plt


def ring_network():
    net = pp.create_empty_network()

    b1 = pp.create_bus(net, vn_kv=220)
    b2 = pp.create_bus(net, vn_kv=110)
    b3 = pp.create_bus(net, vn_kv=110)
    b4 = pp.create_bus(net, vn_kv=110)

    pp.create_ext_grid(net, b1,
                       s_sc_max_mva=100, s_sc_min_mva=80,
                       rx_max=0.35, rx_min=0.2)

    pp.create_transformer(net, b1, b2, std_type='100 MVA 220/110 kV')

    line_type = 'N2XS(FL)2Y 1x120 RM/35 64/110 kV'
    pp.create_line(net, b2, b3, length_km=15, std_type=line_type)
    l2 = pp.create_line(net, b3, b4, length_km=12, std_type=line_type)
    pp.create_line(net, b4, b2, length_km=10, std_type=line_type)

    # Halkayı b4 tarafında açık tutan anahtar
    pp.create_switch(net, b4, l2, et='l', closed=False)
    return net


net = ring_network()
sc.calc_sc(net, case='max', ip=True, ith=True, branch_results=True)

print(net.res_bus_sc)
print(net.res_line_sc)
print(net.res_trafo_sc)