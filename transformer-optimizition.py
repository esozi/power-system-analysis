"""
20/0.4 kV alçak gerilim şebekesi güç akışı analizi (PyPSA)

Şebeke:  OG bara --[Trafo]-- AG1 bara --[Kablo]-- AG2 bara (yük)

Betik şunları yapar:
  1. Şebekeyi kurar
  2. Tüm trafo kademeleri için güç akışını çalıştırır
  3. Gerilim, yüklenme ve kayıp sonuçlarını tek tabloda toplar
  4. Gerilimi izin verilen sınırlar içinde tutan kademeleri işaretler

Gereksinimler: pip install pypsa
"""

import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore")
logging.getLogger("pypsa").setLevel(logging.ERROR)

# ----------------------------------------------------------------------
# Ayarlar (değiştirmek istediklerinizi buradan değiştirin)
# ----------------------------------------------------------------------
TRAFO_TIPI = "0.4 MVA 20/0.4 kV"
KABLO_TIPI = "NAYY 4x50 SE"
KABLO_UZUNLUK_KM = 0.1

OG_GERILIM_PU = 1.01      # OG bara (slack) gerilimi
YUK_P_MW = 0.1            # Aktif yük
YUK_Q_MVAR = 0.05         # Reaktif yük

V_MIN_PU = 0.95           # İzin verilen alt gerilim
V_MAX_PU = 1.05           # İzin verilen üst gerilim

FAZ_KAYMASINI_SIFIRLA = False   # True: Dyn5'in 150° faz kaymasını kaldırır
TRAFO_ADI = "MV-LV Trafo"


# ----------------------------------------------------------------------
# 1) Şebekeyi kur
# ----------------------------------------------------------------------
def sebeke_kur() -> pypsa.Network:
    n = pypsa.Network(name="LV Electrical Grid")

    # Baralar
    n.add("Bus", "MV bus", v_nom=20, v_mag_pu_set=OG_GERILIM_PU)
    n.add("Bus", "LV1 bus", v_nom=0.4)
    n.add("Bus", "LV2 bus", v_nom=0.4)

    # Dış şebeke (slack): OG barasındaki gerilimi ve açıyı belirler
    n.add("Generator", "External Grid", bus="MV bus", control="Slack")

    # Trafo ve kablo hazır tiplerden gelir (x, r, s_nom, kademe bilgisi otomatik)
    n.add("Transformer", TRAFO_ADI, type=TRAFO_TIPI, bus0="MV bus", bus1="LV1 bus")
    n.add("Line", "LV Cable", type=KABLO_TIPI, bus0="LV1 bus", bus1="LV2 bus",
          length=KABLO_UZUNLUK_KM)

    # PyPSA kablo s_nom'unu tipten otomatik hesaplamaz: S = √3 · I_nom · V_nom
    i_nom_kA = n.line_types.loc[KABLO_TIPI, "i_nom"]
    n.lines.loc["LV Cable", "s_nom"] = np.sqrt(3) * i_nom_kA * 0.4   # MVA

    # Yük
    n.add("Load", "LV Load", bus="LV2 bus", p_set=YUK_P_MW, q_set=YUK_Q_MVAR)

    if FAZ_KAYMASINI_SIFIRLA:
        n.transformers.loc[TRAFO_ADI, "phase_shift"] = 0.0

    return n


# ----------------------------------------------------------------------
# 2) Tek bir kademe için güç akışı
# ----------------------------------------------------------------------
def guc_akisi(n: pypsa.Network, kademe: int) -> dict:
    n.transformers.loc[TRAFO_ADI, "tap_position"] = kademe

    n.lpf()                       # doğrusal çözüm: açılar için başlangıç tahmini
    sonuc = n.pf(use_seed=True)   # doğrusal olmayan (Newton-Raphson) çözüm
    yakinsadi = bool(sonuc["converged"].all().all())

    v = n.buses_t.v_mag_pu.loc["now"]
    ang = n.buses_t.v_ang.loc["now"] * 180.0 / np.pi

    # Yüklenme: görünür güç / nominal güç
    trafo_s = np.hypot(n.transformers_t.p0.loc["now", TRAFO_ADI],
                       n.transformers_t.q0.loc["now", TRAFO_ADI])
    trafo_yuk = 100 * trafo_s / n.transformers.loc[TRAFO_ADI, "s_nom"]

    kablo_s = np.hypot(n.lines_t.p0.loc["now", "LV Cable"],
                       n.lines_t.q0.loc["now", "LV Cable"])
    kablo_yuk = 100 * kablo_s / n.lines.loc["LV Cable", "s_nom"]

    # Kayıplar (kW): giriş gücü + çıkış gücü
    kayip_trafo = 1e3 * (n.transformers_t.p0 + n.transformers_t.p1).loc["now", TRAFO_ADI]
    kayip_kablo = 1e3 * (n.lines_t.p0 + n.lines_t.p1).loc["now", "LV Cable"]

    return {
        "Kademe": kademe,
        "Tap ratio": n.transformers.loc[TRAFO_ADI, "tap_ratio"],
        "V_LV1 (pu)": v["LV1 bus"],
        "V_LV2 (pu)": v["LV2 bus"],
        "Açı LV2 (°)": ang["LV2 bus"],
        "Trafo yük (%)": trafo_yuk,
        "Kablo yük (%)": kablo_yuk,
        "Kayıp (kW)": kayip_trafo + kayip_kablo,
        "Yakınsadı": yakinsadi,
    }


# ----------------------------------------------------------------------
# 3) Tüm kademeleri tara
# ----------------------------------------------------------------------
def kademe_taramasi() -> pd.DataFrame:
    n = sebeke_kur()
    tip = n.transformer_types.loc[TRAFO_TIPI]
    kademeler = range(int(tip["tap_min"]), int(tip["tap_max"]) + 1)

    tablo = pd.DataFrame([guc_akisi(n, k) for k in kademeler]).set_index("Kademe")

    v_min = tablo[["V_LV1 (pu)", "V_LV2 (pu)"]].min(axis=1)
    v_max = tablo[["V_LV1 (pu)", "V_LV2 (pu)"]].max(axis=1)
    tablo["Gerilim sınırı OK"] = (v_min >= V_MIN_PU) & (v_max <= V_MAX_PU)
    return tablo


def trafo_ozeti(n: pypsa.Network) -> pd.Series:
    """Trafo tipinin başlıca özellikleri."""
    tip = n.transformer_types.loc[TRAFO_TIPI]
    return tip[["s_nom", "v_nom_0", "v_nom_1", "vsc", "vscr", "pfe", "i0",
                "phase_shift", "tap_side", "tap_min", "tap_max", "tap_step"]]


# ----------------------------------------------------------------------
if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

    print("\n=== Trafo tipi özellikleri ===")
    print(trafo_ozeti(sebeke_kur()))

    print("\n=== Kademe taraması ===")
    sonuc_tablosu = kademe_taramasi()
    print(sonuc_tablosu)

    uygun = sonuc_tablosu[sonuc_tablosu["Gerilim sınırı OK"]]
    print(f"\nİzin verilen aralık: {V_MIN_PU}-{V_MAX_PU} pu")
    if uygun.empty:
        print("Hiçbir kademe tüm baraları sınırlar içinde tutmuyor.")
    else:
        # Hedef: yük barası (LV2) gerilimi 1.0 pu'ya en yakın olan kademe
        en_iyi = (uygun["V_LV2 (pu)"] - 1.0).abs().idxmin()
        print(f"Uygun kademeler: {list(uygun.index)}")
        print(f"Önerilen kademe (LV2 gerilimi 1.0 pu'ya en yakın): {en_iyi}")