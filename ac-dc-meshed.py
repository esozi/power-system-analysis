import pypsa
import matplotlib.pyplot as plt

plt.rc("figure", figsize=(8, 8))
network = pypsa.examples.ac_dc_meshed()

# AC ve DC hatları renklendir
lines_current_type = network.c.lines.static.bus0.map(network.c.buses.static.carrier)

network.plot(
    line_color=lines_current_type.map(lambda ct: "r" if ct == "DC" else "b"),
    title="Mixed AC (blue) and DC (red) network - DC",
    geomap=True,
    jitter=0.3,
)
plt.tight_layout()

# Norwich dönüştürücüsünün kapasitesini sabitle
network.c.links.static.loc["Norwich Converter", "p_nom_extendable"] = False

# Topoloji
network.determine_network_topology()
sub_nets = network.c.sub_networks.static
sub_nets["n_branches"] = [len(sn.branches()) for sn in sub_nets.obj]
sub_nets["n_buses"] = [len(sn.components.buses.static) for sn in sub_nets.obj]

# Jeneratör kullanılabilirlik profilleri
network.c.generators.dynamic.p_max_pu.plot.area(subplots=True)
plt.tight_layout()

# Optimizasyon
status = network.optimize(solver_name="highs")
print(status)
print("Objective:", network.objective)

# Grafik 1: Jeneratör üretimi
network.c.generators.dynamic.p.plot(figsize=(10, 5), title="Generator dispatch")
plt.ylabel("MW")
plt.tight_layout()

# Grafik 2: Ortalama hat yüklenmesi haritası
lines = network.c.lines
line_loading = lines.dynamic.p0.abs().mean() / lines.static.s_nom_opt * 100

network.plot(
    line_color=line_loading,
    line_cmap="jet",
    title="Average line loading (%)",
    geomap=True,
    jitter=0.3,
)
plt.tight_layout()

# Grafik 3: Bara marjinal fiyatları
network.c.buses.dynamic.marginal_price.plot(figsize=(10, 5), title="Bus marginal prices")
plt.ylabel("Price")
plt.tight_layout()

plt.show()