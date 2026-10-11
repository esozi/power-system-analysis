import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pypsa

plt.rc("figure", figsize=(10, 8))

network = pypsa.examples.ac_dc_meshed()
network.optimize(solver_name="highs")

# Her bara için, carrier bazında ortalama üretim (pasta grafik verisi)
gens = network.c.generators
gen = (
    gens.static.assign(g=gens.dynamic.p.mean())
    .groupby(["bus", "carrier"])
    .g.sum()
)

colors = {"gas": "indianred", "wind": "midnightblue"}

# 1) Harita olmadan, ortalama akış okları
network.plot(
    bus_size=gen / 5e3,
    bus_color=colors,
    margin=0.5,
    line_flow="mean",
    link_flow="mean",
    line_width=0.1,
    link_width=0.05,
    geomap=False,
    title="Ortalama üretim ve akış",
)
plt.show()

# 2) Harita üzerinde, EqualEarth projeksiyonu
network.plot(
    bus_size=gen / 5e3,
    bus_color=colors,
    margin=0.5,
    line_flow="mean",
    link_flow="mean",
    line_width=0.1,
    link_width=0.05,
    projection=ccrs.EqualEarth(),
    geomap=True,
    title="Ortalama üretim ve akış (harita)",
)
plt.show()

# 3) Sabit 10 MW'lık ok boyutu, hatlar ortalama |p0| ile renklendirilmiş
network.plot(
    bus_size=gen / 5e3,
    bus_color=colors,
    margin=0.5,
    line_flow=10,
    link_flow=10,
    line_width=2.7,
    link_width=0,
    projection=ccrs.EqualEarth(),
    geomap=True,
    line_color=network.c.lines.dynamic.p0.mean().abs(),
    title="Hat rengi: ortalama |p0| (MW)",
)
plt.show()