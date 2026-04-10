# Granas-Module — Production-Scale Perovskite/TOPCon Tandem

[![PRIMEnergeia](https://img.shields.io/badge/PRIMEnergeia-Sovereign-00ff64)](https://github.com/cordiego)
[![Module](https://img.shields.io/badge/Module-2.1m×3.4m-00d1ff)](.)

## 📐 Module Specification

**2.1m × 3.4m** production-scale Granas perovskite/TOPCon tandem module with CFRP skeleton and green reflectance cooling.

| Parameter | Value |
|-----------|-------|
| Dimensions | **2.1 m × 3.4 m** |
| Total Area | **7.14 m²** |
| Active Area | **6.24 m²** (87.4%, CFRP skeleton) |
| Sub-cells | **100** (10×10 grid of 21×34 cm) |
| Configuration | **50 series × 2 parallel** |
| Cell Voc | **~1,147 mV** (1,100 + green cooling) |
| Module Voc | **~56.75 V** (50 × cell Voc) |
| Module Isc | **~45 A** (2 parallel strings) |
| Peak Power | **~2,100 W** (STC) |
| Tandem PCE | **~33.6%** |
| Annual Energy | **~4,040 kWh** (CF=0.22, Mexico) |
| Weight | **17.9 kg** (CFRP, 5× lighter than glass) |
| T80 Lifetime | **~26 years** (green cooling + ETFE) |

## 🌎 Power Scaling: Home → Continent

| Scale | Consumption | Modules | Installed Power |
|-------|-------------|---------|-----------------|
| 🏠 Home | 10,000 kWh/yr | **~3** | ~6 kW |
| 🏘️ Neighborhood | 1 GWh/yr | **~248** | ~0.5 MW |
| 🏙️ City | 5 TWh/yr | **~1.24M** | ~2.5 GW |
| 🗺️ State | 50 TWh/yr | **~12.4M** | ~25 GW |
| 🇲🇽 Country | 300 TWh/yr | **~74.3M** | ~153 GW |
| 🌎 Continent | 6,500 TWh/yr | **~1.61B** | ~3,300 GW |

## 🏗️ Architecture

```
┌──────────────────────────────────┐
│  ETFE Front Sheet (96% T)       │
│  ─────────────────────────────── │
│  Perovskite Top Cell            │
│  Cs₀.₁₅FA₀.₈₅Pb₀.₉₅Ni₀.₀₃Mn₀.₀₂I₃  │
│  ─────────────────────────────── │
│  TOPCon Silicon Bottom Cell     │
│  n-type Cz, 180μm              │
│  ─────────────────────────────── │
│  CFRP Skeleton (87.4% active)   │
│  2.5 kg/m² (5× lighter)        │
└──────────────────────────────────┘
```

## 🚀 Quick Start

```bash
pip install streamlit plotly numpy
streamlit run granas_module/dashboard.py
```

## 📁 Structure

```
Granas-Module/
├── granas_module/
│   ├── __init__.py
│   ├── module_spec.py      # 2.1m×3.4m physics engine
│   ├── power_scaling.py    # Home→Continent calculator
│   ├── blueprint.py        # Border-only blueprint renderer
│   └── dashboard.py        # Streamlit dashboard
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## 📜 License

Copyright © 2026 Diego Córdoba Urrutia — PRIMEnergeia S.A.S.

*Soberanía Energética Global* ⚡🇲🇽
