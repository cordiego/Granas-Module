#!/usr/bin/env python3
"""
PRIMEnergeia — Granas Module (Unified I/O)
============================================
Top-level orchestrator that wires together the Optics Engine,
Bayesian Optimizer, and HJB Controller into a single module
with real, physically-meaningful inputs and outputs.

Pipeline:
  1. Optics   → Mie + TMM + AM1.5G → Jsc, A/R/T, PLE
  2. BO       → GP + EI → Optimal ink recipe → PCE
  3. HJB      → Value Iteration → Optimal anneal schedule
  4. Power    → PCE × Area × Irradiance → Watts, kWh

Granas Blueprint Geometry:
  Panel:  17 × 10.5 cm  (178.5 cm² total)
  Active: ~156 cm² after CFRP skeleton
  Segments: Triangular tessellation (see Blueprint)

Author: Diego Córdoba Urrutia — PRIMEnergeia S.A.S.
"""

import json
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple, Any

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [Granas Module] - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
MODULE_VERSION = "1.0.0"

# Granas Blueprint Geometry (17 × 10.5 cm panel)
BLUEPRINT_WIDTH_CM = 10.5
BLUEPRINT_HEIGHT_CM = 17.0
BLUEPRINT_TOTAL_AREA_CM2 = BLUEPRINT_WIDTH_CM * BLUEPRINT_HEIGHT_CM  # 178.5 cm²
BLUEPRINT_ACTIVE_FRACTION = 0.874  # ~87.4% active area (CFRP skeleton takes ~12.6%)
BLUEPRINT_ACTIVE_AREA_CM2 = BLUEPRINT_TOTAL_AREA_CM2 * BLUEPRINT_ACTIVE_FRACTION  # ~156 cm²

# Solar capacity factors
CAPACITY_FACTOR_MEXICO = 0.22   # Mexico average
CAPACITY_FACTOR_GLOBAL = 0.18   # Global average
DEFAULT_CAPACITY_FACTOR = CAPACITY_FACTOR_MEXICO

# MAPbI3 bandgap for Voc estimation
MAPBI3_BANDGAP_EV = 1.55
VOC_FRACTION = 0.75  # Voc ≈ 75% of Eg/q (practical loss fraction)

HOURS_PER_YEAR = 8760


# ─────────────────────────────────────────────────────────────
# Input Data Class
# ─────────────────────────────────────────────────────────────
@dataclass
class GranasModuleInput:
    """
    Real physical inputs for a Granas simulation.

    All quantities are in SI-compatible units with explicit unit suffixes.
    Provides full control over the optics domain, optimizer budget,
    HJB time horizon, and module power sizing.
    """
    # ── Device Geometry ──────────────────────────────────────
    panel_area_cm2: float = BLUEPRINT_ACTIVE_AREA_CM2
    """Active panel area (cm²). Default: Granas Blueprint 17×10.5 active area ~156 cm²."""

    # ── Optics Parameters ────────────────────────────────────
    granule_material: str = "MAPbI3"
    """Material key from the built-in library: 'MAPbI3', 'BioHybrid-Chl', 'TiO2-Anatase'."""

    granule_radius_nm: float = 250.0
    """Mean granule radius (nm) for Mie scattering."""

    granule_radius_std_nm: float = 50.0
    """Std deviation of granule radius distribution (nm)."""

    packing_density: float = 0.55
    """Target volume fraction of granules in the domain (0–0.74)."""

    domain_nm: Tuple[float, float, float] = (2000.0, 2000.0, 1000.0)
    """Optical simulation domain (Lx, Ly, Lz) in nm."""

    wavelength_min_nm: float = 300.0
    """Minimum wavelength for spectral simulation (nm)."""

    wavelength_max_nm: float = 1200.0
    """Maximum wavelength for spectral simulation (nm)."""

    n_wavelengths: int = 91
    """Number of wavelength points in the spectral grid."""

    # ── Optimization Parameters ──────────────────────────────
    n_optimization_trials: int = 50
    """Total Bayesian Optimization evaluations (10–200)."""

    target_pce_pct: float = 25.0
    """Design target PCE (%)."""

    acq_func: str = "EI"
    """Acquisition function: 'EI', 'PI', or 'LCB'."""

    multi_objective: bool = False
    """If True, optimize PCE + stability jointly."""

    optimization_seed: int = 42
    """Random seed for reproducibility."""

    # ── HJB Annealing Parameters ─────────────────────────────
    anneal_duration_s: float = 1200.0
    """Total annealing time horizon (s). Default: 1200s = 20 min."""

    anneal_dt_s: float = 2.0
    """HJB time step (s)."""

    initial_grain_nm: float = 50.0
    """Pre-anneal initial grain size (nm)."""

    initial_defect_density: float = 1.5
    """Pre-anneal defect density (a.u.)."""

    initial_film_temp_C: float = 25.0
    """Initial film temperature (°C)."""

    # ── Operating Conditions ─────────────────────────────────
    irradiance_W_m2: float = 1000.0
    """Operating irradiance (W/m²). Default: 1000 = STC."""

    capacity_factor: float = DEFAULT_CAPACITY_FACTOR
    """Solar capacity factor for annual energy. Default: 0.22 (Mexico)."""

    bandgap_eV: float = MAPBI3_BANDGAP_EV
    """Active material bandgap (eV) for Voc estimation."""

    # ── Simulation Control ───────────────────────────────────
    simulation_name: str = "Granas_Module_V1"
    """Run identifier."""

    run_optics: bool = True
    """Enable optics sub-pipeline."""

    run_optimization: bool = True
    """Enable Bayesian Optimization sub-pipeline."""

    run_hjb: bool = True
    """Enable HJB annealing control sub-pipeline."""

    def validate(self) -> List[str]:
        """Validate all input bounds. Returns list of warnings (empty = OK)."""
        warnings = []
        if self.panel_area_cm2 <= 0:
            warnings.append(f"panel_area_cm2 must be positive, got {self.panel_area_cm2}")
        if not (0 < self.packing_density <= 0.74):
            warnings.append(f"packing_density must be in (0, 0.74], got {self.packing_density}")
        if not (100 <= self.granule_radius_nm <= 1000):
            warnings.append(f"granule_radius_nm should be 100–1000 nm, got {self.granule_radius_nm}")
        if not (10 <= self.n_optimization_trials <= 500):
            warnings.append(f"n_optimization_trials should be 10–500, got {self.n_optimization_trials}")
        if not (0 < self.irradiance_W_m2 <= 2000):
            warnings.append(f"irradiance_W_m2 should be 0–2000, got {self.irradiance_W_m2}")
        if not (0 < self.capacity_factor <= 1.0):
            warnings.append(f"capacity_factor must be in (0, 1], got {self.capacity_factor}")
        if not (0.5 <= self.bandgap_eV <= 3.5):
            warnings.append(f"bandgap_eV should be 0.5–3.5 eV, got {self.bandgap_eV}")
        if self.anneal_duration_s <= 0:
            warnings.append(f"anneal_duration_s must be positive, got {self.anneal_duration_s}")
        return warnings


# ─────────────────────────────────────────────────────────────
# Output Data Class
# ─────────────────────────────────────────────────────────────
@dataclass
class GranasModuleOutput:
    """
    Complete output payload with real engineering numbers.

    Every field carries its physical unit in the field name suffix.
    Designed for direct ingestion by SCADA/EMS/API systems.
    """
    # ── Metadata ─────────────────────────────────────────────
    simulation_name: str = ""
    engine_version: str = MODULE_VERSION
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_time_s: float = 0.0

    # ── Optics Block ─────────────────────────────────────────
    jsc_mA_cm2: float = 0.0
    """Short-circuit current density (mA/cm²) from AM1.5G EQE integration."""

    weighted_absorption_pct: float = 0.0
    """AM1.5G irradiance-weighted absorption (%)."""

    path_length_enhancement: float = 0.0
    """Path length enhancement vs. single-pass (×)."""

    yablonovitch_limit: float = 0.0
    """Theoretical 4n² limit (×)."""

    light_trapping_efficiency: float = 0.0
    """PLE / Yablonovitch (0–1)."""

    avg_reflectance_pct: float = 0.0
    """Broadband average reflectance (%)."""

    avg_transmittance_pct: float = 0.0
    """Broadband average transmittance (%)."""

    avg_absorptance_pct: float = 0.0
    """Broadband average absorptance (%)."""

    n_granules_packed: int = 0
    """Number of granules packed in the simulation domain."""

    spectral_data: Optional[Dict[str, Any]] = None
    """Spectral arrays: {wavelengths_nm, R, T, A, EQE} — set to None for JSON compat."""

    # ── Optimization Block ───────────────────────────────────
    optimal_recipe: Optional[Dict[str, float]] = None
    """Best ink recipe {molar_conc, solvent_ratio, spin_speed, additive_pct, anneal_temp, anneal_time}."""

    predicted_pce_pct: float = 0.0
    """Physics-model predicted power conversion efficiency (%)."""

    grain_size_nm: float = 0.0
    """Predicted grain diameter from optimal recipe (nm)."""

    defect_density: float = 0.0
    """Predicted defect density from optimal recipe (a.u.)."""

    stability_score: float = 0.0
    """T80 lifetime proxy stability score (0–1)."""

    n_trials_run: int = 0
    """Number of BO evaluations executed."""

    # ── Module Power Block (Real Watts) ──────────────────────
    panel_area_cm2: float = 0.0
    """Active panel area used for calculation (cm²)."""

    module_power_W: float = 0.0
    """Module output power at operating irradiance (W)."""

    module_voc_V: float = 0.0
    """Estimated open-circuit voltage (V)."""

    module_isc_A: float = 0.0
    """Short-circuit current: Jsc × Area (A)."""

    module_fill_factor: float = 0.0
    """Estimated fill factor (0–1)."""

    annual_energy_kWh: float = 0.0
    """Estimated annual energy production (kWh)."""

    # ── HJB Control Block ────────────────────────────────────
    optimal_anneal_schedule: Optional[List[Tuple[float, float]]] = None
    """Optimal annealing schedule: [(time_s, temp_C), ...]."""

    hjb_terminal_grain_nm: float = 0.0
    """Terminal grain size after HJB-optimal anneal (nm)."""

    hjb_terminal_defects: float = 0.0
    """Terminal defect density after HJB-optimal anneal (a.u.)."""

    hjb_pce_boost_pct: float = 0.0
    """PCE improvement from HJB vs. static anneal (%)."""

    hjb_total_cost: float = 0.0
    """HJB total accumulated cost."""

    control_trajectory_C_s: Optional[List[float]] = None
    """Ramp rate sequence (°C/s) — set to None for JSON compat."""


# ─────────────────────────────────────────────────────────────
# Granas Module — Top-Level Orchestrator
# ─────────────────────────────────────────────────────────────
class GranasModule:
    """
    Unified Granas orchestrator with real physical I/O.

    Connects three engines into a single pipeline:
      Optics (Mie/TMM/AM1.5G) → Bayesian Optimizer (GP/EI) → HJB Controller

    Each sub-pipeline can be run independently or as a full stack.

    Usage:
        module = GranasModule()
        inputs = GranasModuleInput(panel_area_cm2=156.0)
        output = module.run(inputs)
        print(f"Power: {output.module_power_W:.2f} W")
        print(module.to_json(output))
    """

    def __init__(self):
        self._optics_result = None
        self._bo_result = None
        self._hjb_result = None

    # ─── Full Pipeline ───────────────────────────────────────
    def run(self, inputs: GranasModuleInput) -> GranasModuleOutput:
        """
        Execute the complete Granas pipeline with real inputs → real outputs.

        Pipeline:
          1. Validate inputs
          2. Run optical simulation (if enabled)
          3. Run Bayesian Optimization (if enabled)
          4. Run HJB annealing control (if enabled)
          5. Compute real-world power metrics
          6. Assemble output payload

        Parameters
        ----------
        inputs : GranasModuleInput
            Complete physical input specification.

        Returns
        -------
        GranasModuleOutput
            Complete output payload with real engineering numbers.
        """
        t_start = time.time()

        logger.info("=" * 70)
        logger.info(" GRANAS MODULE — Unified Pipeline")
        logger.info(f" Simulation:   {inputs.simulation_name}")
        logger.info(f" Panel Area:   {inputs.panel_area_cm2:.1f} cm²")
        logger.info(f" Material:     {inputs.granule_material}")
        logger.info(f" Irradiance:   {inputs.irradiance_W_m2:.0f} W/m²")
        logger.info(f" Cap. Factor:  {inputs.capacity_factor:.2f}")
        logger.info("=" * 70)

        # Validate inputs
        warnings = inputs.validate()
        for w in warnings:
            logger.warning(f"Input warning: {w}")

        output = GranasModuleOutput(
            simulation_name=inputs.simulation_name,
            panel_area_cm2=inputs.panel_area_cm2,
        )

        # ── Sub-pipeline 1: Optics ───────────────────────────
        if inputs.run_optics:
            self._run_optics(inputs, output)

        # ── Sub-pipeline 2: Bayesian Optimization ────────────
        if inputs.run_optimization:
            self._run_optimization(inputs, output)

        # ── Sub-pipeline 3: HJB Annealing Control ────────────
        if inputs.run_hjb:
            self._run_hjb(inputs, output)

        # ── Sub-pipeline 4: Real-World Power ─────────────────
        self._compute_power(inputs, output)

        output.execution_time_s = time.time() - t_start

        self._log_summary(inputs, output)
        return output

    # ─── Optics Only ─────────────────────────────────────────
    def run_optics_only(self, inputs: GranasModuleInput) -> GranasModuleOutput:
        """Run only the optics sub-pipeline."""
        inputs_copy = GranasModuleInput(**{
            **asdict(inputs),
            'run_optics': True,
            'run_optimization': False,
            'run_hjb': False,
        })
        return self.run(inputs_copy)

    # ─── Optimization Only ───────────────────────────────────
    def run_optimization_only(self, inputs: GranasModuleInput) -> GranasModuleOutput:
        """Run only the Bayesian Optimization sub-pipeline."""
        inputs_copy = GranasModuleInput(**{
            **asdict(inputs),
            'run_optics': False,
            'run_optimization': True,
            'run_hjb': False,
        })
        return self.run(inputs_copy)

    # ─── HJB Only ────────────────────────────────────────────
    def run_hjb_only(self, inputs: GranasModuleInput) -> GranasModuleOutput:
        """Run only the HJB annealing control sub-pipeline."""
        inputs_copy = GranasModuleInput(**{
            **asdict(inputs),
            'run_optics': False,
            'run_optimization': False,
            'run_hjb': True,
        })
        return self.run(inputs_copy)

    # ─── Internal: Optics Pipeline ───────────────────────────
    def _run_optics(self, inputs: GranasModuleInput,
                    output: GranasModuleOutput) -> None:
        """Execute the Granas optics engine and populate output."""
        from optics.granas_optics import GranasEngine

        logger.info("▸ Running Optics Engine...")

        engine = GranasEngine(inputs.simulation_name)

        # Configure domain
        engine.domain_nm = inputs.domain_nm
        engine.antireflection_thickness_nm = 80.0
        engine.substrate_n = 1.5

        # Build granular matrix
        engine.build_granular_matrix(
            density=inputs.packing_density,
            radius_mean=inputs.granule_radius_nm,
            radius_std=inputs.granule_radius_std_nm,
            material=inputs.granule_material,
            seed=inputs.optimization_seed,
        )

        # Wavelength grid
        wavelengths = np.linspace(
            inputs.wavelength_min_nm,
            inputs.wavelength_max_nm,
            inputs.n_wavelengths,
        )

        # Run full analysis
        result = engine.run_analysis(wavelengths)
        self._optics_result = result

        # Populate output
        output.jsc_mA_cm2 = result.jsc_mA_cm2
        output.weighted_absorption_pct = result.weighted_absorption
        output.path_length_enhancement = result.path_length_enhancement
        output.yablonovitch_limit = result.yablonovitch_limit
        output.light_trapping_efficiency = result.light_trapping_efficiency
        output.avg_reflectance_pct = float(np.mean(result.reflectance) * 100)
        output.avg_transmittance_pct = float(np.mean(result.transmittance) * 100)
        output.avg_absorptance_pct = float(np.mean(result.absorptance) * 100)
        output.n_granules_packed = len(result.granule_positions)

        # Spectral data (numpy → list for JSON compatibility)
        output.spectral_data = {
            "wavelengths_nm": result.wavelengths_nm.tolist(),
            "reflectance": result.reflectance.tolist(),
            "transmittance": result.transmittance.tolist(),
            "absorptance": result.absorptance.tolist(),
            "eqe": result.eqe.tolist(),
        }

        logger.info(f"  Optics complete: Jsc={output.jsc_mA_cm2:.2f} mA/cm², "
                     f"A={output.weighted_absorption_pct:.1f}%, "
                     f"PLE={output.path_length_enhancement:.1f}×")

    # ─── Internal: Bayesian Optimization Pipeline ────────────
    def _run_optimization(self, inputs: GranasModuleInput,
                          output: GranasModuleOutput) -> None:
        """Execute the Bayesian Optimizer and populate output."""
        import importlib
        mod = importlib.import_module('optimization.granas_bayesian')
        GranasOptimizer = mod.GranasOptimizer

        logger.info("▸ Running Bayesian Optimizer...")

        optimizer = GranasOptimizer(
            n_calls=inputs.n_optimization_trials,
            n_initial=max(3, inputs.n_optimization_trials // 6),
            acq_func=inputs.acq_func,
            multi_objective=inputs.multi_objective,
            random_state=inputs.optimization_seed,
            output_dir="granas_results",
        )
        optimizer.run()
        self._bo_result = optimizer

        best = optimizer.get_best()
        if best:
            output.optimal_recipe = {
                "molar_conc": round(best.recipe.molar_conc, 4),
                "solvent_ratio": round(best.recipe.solvent_ratio, 4),
                "spin_speed": best.recipe.spin_speed,
                "additive_pct": round(best.recipe.additive_pct, 4),
                "anneal_temp": round(best.recipe.anneal_temp, 1),
                "anneal_time": round(best.recipe.anneal_time, 1),
            }
            output.predicted_pce_pct = round(best.pce, 3)
            output.grain_size_nm = round(best.grain_size_nm, 1)
            output.defect_density = round(best.defect_density, 4)
            output.stability_score = round(best.stability_score, 3)
            output.n_trials_run = len(optimizer.trials)

            logger.info(f"  BO complete: PCE={output.predicted_pce_pct:.2f}%, "
                         f"Grain={output.grain_size_nm:.0f}nm, "
                         f"Stability={output.stability_score:.3f}")

    # ─── Internal: HJB Pipeline ──────────────────────────────
    def _run_hjb(self, inputs: GranasModuleInput,
                 output: GranasModuleOutput) -> None:
        """Execute the HJB controller and populate output."""
        import importlib
        hjb_mod = importlib.import_module('optimization.granas_hjb')
        GranasHJBController = hjb_mod.GranasHJBController
        AnnealingState = hjb_mod.AnnealingState

        logger.info("▸ Running HJB Controller...")

        controller = GranasHJBController(
            total_time_s=inputs.anneal_duration_s,
            dt=inputs.anneal_dt_s,
            n_grain=25,
            n_defect=20,
            n_temp=15,
            n_control=9,
        )

        initial = AnnealingState(
            grain_size_nm=inputs.initial_grain_nm,
            defect_density=inputs.initial_defect_density,
            film_temp_C=inputs.initial_film_temp_C,
        )

        result = controller.simulate_trajectory(initial)
        self._hjb_result = result

        output.optimal_anneal_schedule = result.optimal_schedule
        output.hjb_terminal_grain_nm = result.terminal_grain_nm
        output.hjb_terminal_defects = result.terminal_defects
        output.hjb_pce_boost_pct = result.pce_boost_pct
        output.hjb_total_cost = result.total_cost
        output.control_trajectory_C_s = result.control_trajectory.tolist()

        logger.info(f"  HJB complete: Grain={output.hjb_terminal_grain_nm:.1f}nm, "
                     f"Defects={output.hjb_terminal_defects:.4f}, "
                     f"Boost=+{output.hjb_pce_boost_pct:.2f}%")

    # ─── Internal: Power Calculations ────────────────────────
    def _compute_power(self, inputs: GranasModuleInput,
                       output: GranasModuleOutput) -> None:
        """
        Compute real-world module power from PCE, area, and irradiance.

        Physics:
          P = η × A × G
            η = PCE / 100
            A = panel_area_cm² / 10000  (→ m²)
            G = irradiance (W/m²)

          Voc ≈ Eg × VOC_FRACTION / q  (simplified)
          Isc = Jsc × A_cm² / 1000     (mA→A)
          FF  = P / (Voc × Isc)
          E_annual = P × CF × 8760 / 1000  (kWh)
        """
        pce = output.predicted_pce_pct if output.predicted_pce_pct > 0 else 0.0
        area_m2 = inputs.panel_area_cm2 / 10000.0  # cm² → m²

        # Module power (W)
        output.module_power_W = (pce / 100.0) * area_m2 * inputs.irradiance_W_m2

        # Open-circuit voltage estimate (V)
        output.module_voc_V = inputs.bandgap_eV * VOC_FRACTION

        # Short-circuit current (A)
        jsc = output.jsc_mA_cm2 if output.jsc_mA_cm2 > 0 else 0.0
        output.module_isc_A = jsc * inputs.panel_area_cm2 / 1000.0  # mA/cm² × cm² → mA → A

        # Fill Factor (derived)
        voc_isc_product = output.module_voc_V * output.module_isc_A
        if voc_isc_product > 0:
            output.module_fill_factor = min(
                output.module_power_W / voc_isc_product, 0.90
            )
        else:
            output.module_fill_factor = 0.0

        # Annual energy (kWh)
        output.annual_energy_kWh = (
            output.module_power_W * inputs.capacity_factor * HOURS_PER_YEAR / 1000.0
        )

        logger.info(f"  Power: {output.module_power_W:.4f} W | "
                     f"Voc={output.module_voc_V:.3f} V | "
                     f"Isc={output.module_isc_A:.4f} A | "
                     f"FF={output.module_fill_factor:.3f} | "
                     f"Annual={output.annual_energy_kWh:.4f} kWh")

    # ─── Summary Log ─────────────────────────────────────────
    def _log_summary(self, inputs: GranasModuleInput,
                     output: GranasModuleOutput) -> None:
        """Print the full output summary."""
        logger.info("=" * 70)
        logger.info(" GRANAS MODULE — OUTPUT SUMMARY")
        logger.info("─" * 70)

        if inputs.run_optics:
            logger.info(" OPTICS:")
            logger.info(f"   Jsc:                    {output.jsc_mA_cm2:.2f} mA/cm²")
            logger.info(f"   AM1.5G Absorption:      {output.weighted_absorption_pct:.1f}%")
            logger.info(f"   Path Enhancement:       {output.path_length_enhancement:.1f}×")
            logger.info(f"   Yablonovitch Limit:     {output.yablonovitch_limit:.1f}×")
            logger.info(f"   Light Trapping Eff:     {output.light_trapping_efficiency:.3f}")
            logger.info(f"   R / T / A (avg):        {output.avg_reflectance_pct:.1f}% / "
                         f"{output.avg_transmittance_pct:.1f}% / "
                         f"{output.avg_absorptance_pct:.1f}%")
            logger.info(f"   Granules:               {output.n_granules_packed}")

        if inputs.run_optimization:
            logger.info(" OPTIMIZATION:")
            logger.info(f"   Predicted PCE:          {output.predicted_pce_pct:.2f}%")
            logger.info(f"   Grain Size:             {output.grain_size_nm:.1f} nm")
            logger.info(f"   Defect Density:         {output.defect_density:.4f}")
            logger.info(f"   Stability Score:        {output.stability_score:.3f}")
            logger.info(f"   Trials Run:             {output.n_trials_run}")
            if output.optimal_recipe:
                logger.info(f"   Recipe:                 {output.optimal_recipe}")

        if inputs.run_hjb:
            logger.info(" HJB CONTROL:")
            logger.info(f"   Terminal Grain:         {output.hjb_terminal_grain_nm:.1f} nm")
            logger.info(f"   Terminal Defects:       {output.hjb_terminal_defects:.4f}")
            logger.info(f"   PCE Boost:              +{output.hjb_pce_boost_pct:.2f}%")
            logger.info(f"   Schedule Points:        {len(output.optimal_anneal_schedule or [])}")

        logger.info(" MODULE POWER:")
        logger.info(f"   Panel Area:             {output.panel_area_cm2:.1f} cm²")
        logger.info(f"   Module Power:           {output.module_power_W:.4f} W")
        logger.info(f"   Voc:                    {output.module_voc_V:.3f} V")
        logger.info(f"   Isc:                    {output.module_isc_A:.4f} A")
        logger.info(f"   Fill Factor:            {output.module_fill_factor:.3f}")
        logger.info(f"   Annual Energy:          {output.annual_energy_kWh:.4f} kWh")
        logger.info(f"   Capacity Factor:        {inputs.capacity_factor:.2f} (Mexico)")

        logger.info("─" * 70)
        logger.info(f" Execution Time:           {output.execution_time_s:.2f}s")
        logger.info("=" * 70)

    # ─── Serialization ───────────────────────────────────────
    @staticmethod
    def to_json(output: GranasModuleOutput, include_spectral: bool = False) -> str:
        """
        Serialize output to JSON string for API/SCADA ingestion.

        Parameters
        ----------
        output : GranasModuleOutput
        include_spectral : bool
            If False, strips the large spectral arrays for compact output.

        Returns
        -------
        str : JSON string
        """
        data = asdict(output)

        if not include_spectral:
            data.pop("spectral_data", None)
            data.pop("control_trajectory_C_s", None)

        # Convert any remaining numpy types
        def _convert(obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        return json.dumps(data, indent=2, default=_convert)

    @staticmethod
    def to_dataframe(output: GranasModuleOutput) -> pd.DataFrame:
        """
        Convert output to a summary DataFrame for tabular reporting.

        Returns a single-row DataFrame with key metrics.
        """
        row = {
            "simulation_name": output.simulation_name,
            "timestamp": output.timestamp,
            "execution_time_s": round(output.execution_time_s, 2),
            # Optics
            "jsc_mA_cm2": round(output.jsc_mA_cm2, 2),
            "absorption_pct": round(output.weighted_absorption_pct, 1),
            "path_enhancement_x": round(output.path_length_enhancement, 1),
            "yablonovitch_x": round(output.yablonovitch_limit, 1),
            "lte": round(output.light_trapping_efficiency, 3),
            "R_pct": round(output.avg_reflectance_pct, 1),
            "T_pct": round(output.avg_transmittance_pct, 1),
            "A_pct": round(output.avg_absorptance_pct, 1),
            "n_granules": output.n_granules_packed,
            # Optimization
            "pce_pct": round(output.predicted_pce_pct, 2),
            "grain_nm": round(output.grain_size_nm, 1),
            "defects": round(output.defect_density, 4),
            "stability": round(output.stability_score, 3),
            "n_trials": output.n_trials_run,
            # Power
            "panel_cm2": round(output.panel_area_cm2, 1),
            "power_W": round(output.module_power_W, 4),
            "voc_V": round(output.module_voc_V, 3),
            "isc_A": round(output.module_isc_A, 4),
            "fill_factor": round(output.module_fill_factor, 3),
            "annual_kWh": round(output.annual_energy_kWh, 4),
            # HJB
            "hjb_grain_nm": round(output.hjb_terminal_grain_nm, 1),
            "hjb_defects": round(output.hjb_terminal_defects, 4),
            "hjb_boost_pct": round(output.hjb_pce_boost_pct, 2),
        }
        return pd.DataFrame([row])

    @staticmethod
    def to_scada_payload(output: GranasModuleOutput) -> Dict[str, Any]:
        """
        Minimal SCADA/EMS-compatible payload with only essential real-time signals.

        Returns a flat dictionary suitable for Modbus/MQTT/OPC-UA telemetry.
        """
        return {
            "granas_module_power_W": round(output.module_power_W, 4),
            "granas_module_voc_V": round(output.module_voc_V, 3),
            "granas_module_isc_A": round(output.module_isc_A, 4),
            "granas_module_ff": round(output.module_fill_factor, 3),
            "granas_module_pce_pct": round(output.predicted_pce_pct, 2),
            "granas_jsc_mA_cm2": round(output.jsc_mA_cm2, 2),
            "granas_absorption_pct": round(output.weighted_absorption_pct, 1),
            "granas_ple_x": round(output.path_length_enhancement, 1),
            "granas_grain_nm": round(output.grain_size_nm, 1),
            "granas_defects": round(output.defect_density, 4),
            "granas_annual_kWh": round(output.annual_energy_kWh, 4),
            "granas_panel_cm2": round(output.panel_area_cm2, 1),
            "granas_hjb_boost_pct": round(output.hjb_pce_boost_pct, 2),
            "granas_timestamp": output.timestamp,
        }


# ─────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*70}")
    print(f" 🧪 GRANAS MODULE — Real Input / Output Pipeline")
    print(f" PRIMEnergeia S.A.S. | v{MODULE_VERSION}")
    print(f" Panel: {BLUEPRINT_WIDTH_CM}×{BLUEPRINT_HEIGHT_CM} cm "
          f"({BLUEPRINT_ACTIVE_AREA_CM2:.1f} cm² active)")
    print(f"{'='*70}\n")

    # Default inputs: Granas Blueprint panel, Mexico capacity factor
    inputs = GranasModuleInput(
        simulation_name="Granas_Blueprint_17x10.5",
        panel_area_cm2=BLUEPRINT_ACTIVE_AREA_CM2,
        granule_material="MAPbI3",
        granule_radius_nm=250.0,
        packing_density=0.55,
        n_optimization_trials=30,  # Lighter for CLI demo
        capacity_factor=CAPACITY_FACTOR_MEXICO,
    )

    module = GranasModule()
    output = module.run(inputs)

    # Print JSON output
    print(f"\n{'─'*70}")
    print(" 📦 JSON Output (SCADA-ready):")
    print(f"{'─'*70}")
    print(module.to_json(output))

    # Print SCADA payload
    print(f"\n{'─'*70}")
    print(" 📡 SCADA Telemetry Payload:")
    print(f"{'─'*70}")
    scada = module.to_scada_payload(output)
    for k, v in scada.items():
        print(f"  {k:40s} = {v}")

    # Print DataFrame
    print(f"\n{'─'*70}")
    print(" 📊 DataFrame Summary:")
    print(f"{'─'*70}")
    df = module.to_dataframe(output)
    print(df.T.to_string())

    print(f"\n{'='*70}")
    print(f" ✅ Pipeline complete in {output.execution_time_s:.2f}s")
    print(f"{'='*70}")
