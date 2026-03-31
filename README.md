# Granas-Module
## Perovskite Solar Module Intelligence — Unified I/O Pipeline

> **From Photons to Watts. One Pipeline.**

Granas Module connects **Mie/TMM optics**, **Bayesian ink optimization**, and **HJB annealing control** into a single orchestrator — outputting real Watts, mA/cm², and kWh from the 17×10.5 cm Granas Blueprint geometry.

**PRIMEnergeia S.A.S.** · Diego Córdoba Urrutia · Soberanía Energética Global ⚡🇲🇽

---

## Architecture

```
GranasModuleInput (real physics)
    │
    ├── Optics Engine ──→ Jsc (mA/cm²), A/R/T (%), PLE (×)
    ├── Bayesian BO   ──→ Optimal recipe, PCE (%), grain (nm)
    ├── HJB Controller ──→ Anneal schedule (°C/s), grain growth
    │
    └── Power Calculator ──→ Watts, Voc (V), Isc (A), FF, kWh/year
                               │
                               ├── to_json()         → API / REST
                               ├── to_scada_payload() → Modbus / MQTT
                               └── to_dataframe()     → Analytics
```

## Quick Start

```python
from granas_module import GranasModule, GranasModuleInput

inputs = GranasModuleInput(
    panel_area_cm2=156.0,           # Granas Blueprint active area
    granule_material="MAPbI3",
    granule_radius_nm=250.0,
    packing_density=0.55,
    n_optimization_trials=50,
    capacity_factor=0.22,           # Mexico
)

module = GranasModule()
output = module.run(inputs)

print(f"Power:  {output.module_power_W:.4f} W")
print(f"Jsc:    {output.jsc_mA_cm2:.2f} mA/cm²")
print(f"Annual: {output.annual_energy_kWh:.4f} kWh")
print(GranasModule.to_json(output))
```

## Real Outputs

| Output | Unit | Description |
|--------|------|-------------|
| `module_power_W` | W | PCE × area × irradiance |
| `jsc_mA_cm2` | mA/cm² | AM1.5G short-circuit current density |
| `module_voc_V` | V | Open-circuit voltage from bandgap |
| `module_isc_A` | A | Short-circuit current |
| `annual_energy_kWh` | kWh | P × CF × 8760 |
| `optimal_recipe` | dict | Best ink recipe (6 parameters) |
| `optimal_anneal_schedule` | [(s, °C)] | HJB temperature trajectory |

## Granas Blueprint

Panel: **17 × 10.5 cm** · Active: **156 cm²** · CFRP skeleton: 12.6%

## Showcase Page

Open `index.html` in a browser to view the interactive platform page with:
- 🔬 Engine documentation
- 📊 Output catalog
- ⚡ Module power simulator
- 📐 Blueprint geometry canvas

## Engines

| Engine | File | Physics |
|--------|------|---------|
| Optics | `optics/granas_optics.py` | Mie + TMM + AM1.5G |
| Optimizer | `optimization/granas_bayesian.py` | GP + EI (6D) |
| HJB | `optimization/granas_hjb.py` | Value iteration DP |
| **Module** | `granas_module.py` | Unified orchestrator |

## Tests

```bash
python3 -m pytest tests/ -v
```

## License

MIT — PRIMEnergeia S.A.S.
