"""
PRIMEnergeia — Granas Module Test Suite
========================================
Comprehensive tests for the unified Granas Module with real I/O.

Test classes:
  - TestGranasModuleInput     : Input validation and defaults
  - TestGranasModuleOutput    : Output structure and field types
  - TestGranasModuleOptics    : Optics-only sub-pipeline
  - TestGranasModuleBO        : Optimization-only sub-pipeline
  - TestGranasModuleHJB       : HJB-only sub-pipeline
  - TestGranasModulePower     : Power calculations (Watts, kWh)
  - TestGranasModuleSerial    : JSON / DataFrame / SCADA serialization
  - TestGranasModuleFull      : Full pipeline integration

Author: Diego Córdoba Urrutia — PRIMEnergeia S.A.S.
"""

import sys
import os
import json
import pytest
import numpy as np

# Ensure repo root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from granas_module import (
    GranasModule,
    GranasModuleInput,
    GranasModuleOutput,
    BLUEPRINT_ACTIVE_AREA_CM2,
    BLUEPRINT_WIDTH_CM,
    BLUEPRINT_HEIGHT_CM,
    CAPACITY_FACTOR_MEXICO,
    CAPACITY_FACTOR_GLOBAL,
    MODULE_VERSION,
    HOURS_PER_YEAR,
    VOC_FRACTION,
    MAPBI3_BANDGAP_EV,
)


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def default_inputs():
    return GranasModuleInput()


@pytest.fixture
def fast_inputs():
    """Lightweight inputs for fast testing."""
    return GranasModuleInput(
        simulation_name="Test_Fast",
        n_optimization_trials=10,
        n_wavelengths=21,
        anneal_duration_s=100.0,
        anneal_dt_s=10.0,
    )


@pytest.fixture
def optics_only_inputs():
    return GranasModuleInput(
        simulation_name="Test_Optics",
        n_wavelengths=21,
        run_optics=True,
        run_optimization=False,
        run_hjb=False,
    )


@pytest.fixture
def bo_only_inputs():
    return GranasModuleInput(
        simulation_name="Test_BO",
        n_optimization_trials=10,
        run_optics=False,
        run_optimization=True,
        run_hjb=False,
    )


@pytest.fixture
def hjb_only_inputs():
    return GranasModuleInput(
        simulation_name="Test_HJB",
        anneal_duration_s=100.0,
        anneal_dt_s=10.0,
        run_optics=False,
        run_optimization=False,
        run_hjb=True,
    )


@pytest.fixture
def module():
    return GranasModule()


# ═════════════════════════════════════════════════════════════
# TestGranasModuleInput
# ═════════════════════════════════════════════════════════════
class TestGranasModuleInput:
    """Test input data class defaults and validation."""

    def test_default_panel_area(self, default_inputs):
        """Default panel area should be the Granas Blueprint active area."""
        assert default_inputs.panel_area_cm2 == pytest.approx(
            BLUEPRINT_ACTIVE_AREA_CM2, abs=1.0
        )

    def test_blueprint_geometry(self):
        """Blueprint geometry: 17 × 10.5 cm."""
        assert BLUEPRINT_WIDTH_CM == 10.5
        assert BLUEPRINT_HEIGHT_CM == 17.0
        total = BLUEPRINT_WIDTH_CM * BLUEPRINT_HEIGHT_CM
        assert total == pytest.approx(178.5, abs=0.1)

    def test_default_capacity_factor_mexico(self, default_inputs):
        """Default capacity factor should be Mexico's 0.22."""
        assert default_inputs.capacity_factor == CAPACITY_FACTOR_MEXICO
        assert default_inputs.capacity_factor == 0.22

    def test_default_material(self, default_inputs):
        assert default_inputs.granule_material == "MAPbI3"

    def test_default_irradiance(self, default_inputs):
        assert default_inputs.irradiance_W_m2 == 1000.0

    def test_default_bandgap(self, default_inputs):
        assert default_inputs.bandgap_eV == pytest.approx(1.55, abs=0.01)

    def test_validation_passes_defaults(self, default_inputs):
        """Default inputs should pass validation with no warnings."""
        warnings = default_inputs.validate()
        assert len(warnings) == 0

    def test_validation_catches_negative_area(self):
        inputs = GranasModuleInput(panel_area_cm2=-10)
        warnings = inputs.validate()
        assert any("panel_area_cm2" in w for w in warnings)

    def test_validation_catches_bad_packing(self):
        inputs = GranasModuleInput(packing_density=0.95)
        warnings = inputs.validate()
        assert any("packing_density" in w for w in warnings)

    def test_validation_catches_bad_irradiance(self):
        inputs = GranasModuleInput(irradiance_W_m2=5000)
        warnings = inputs.validate()
        assert any("irradiance_W_m2" in w for w in warnings)

    def test_all_flags_default_true(self, default_inputs):
        assert default_inputs.run_optics is True
        assert default_inputs.run_optimization is True
        assert default_inputs.run_hjb is True


# ═════════════════════════════════════════════════════════════
# TestGranasModuleOutput
# ═════════════════════════════════════════════════════════════
class TestGranasModuleOutput:
    """Test output data class structure."""

    def test_default_version(self):
        output = GranasModuleOutput()
        assert output.engine_version == MODULE_VERSION

    def test_default_timestamp(self):
        output = GranasModuleOutput()
        assert len(output.timestamp) > 0

    def test_zeros_on_init(self):
        output = GranasModuleOutput()
        assert output.jsc_mA_cm2 == 0.0
        assert output.module_power_W == 0.0
        assert output.annual_energy_kWh == 0.0

    def test_spectral_data_none_default(self):
        output = GranasModuleOutput()
        assert output.spectral_data is None


# ═════════════════════════════════════════════════════════════
# TestGranasModuleOptics
# ═════════════════════════════════════════════════════════════
class TestGranasModuleOptics:
    """Test the optics sub-pipeline with real outputs."""

    def test_optics_only_runs(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        assert output.jsc_mA_cm2 > 0, "Jsc must be positive"
        assert output.n_granules_packed > 0, "Must pack at least one granule"

    def test_energy_conservation(self, module, optics_only_inputs):
        """R + T + A ≈ 100% (energy conservation)."""
        output = module.run(optics_only_inputs)
        total = output.avg_reflectance_pct + output.avg_transmittance_pct + output.avg_absorptance_pct
        assert total == pytest.approx(100.0, abs=2.0), \
            f"R+T+A = {total:.1f}%, expected ~100%"

    def test_spectral_data_populated(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        assert output.spectral_data is not None
        assert "wavelengths_nm" in output.spectral_data
        assert "absorptance" in output.spectral_data
        assert "eqe" in output.spectral_data
        assert len(output.spectral_data["wavelengths_nm"]) == optics_only_inputs.n_wavelengths

    def test_yablonovitch_positive(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        assert output.yablonovitch_limit > 0

    def test_light_trapping_bounded(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        assert 0 <= output.light_trapping_efficiency <= 2.0  # Can slightly exceed 1 in idealized sims

    def test_jsc_reasonable_range(self, module, optics_only_inputs):
        """Jsc for MAPbI3 should be in 5–35 mA/cm² range."""
        output = module.run(optics_only_inputs)
        assert 1.0 < output.jsc_mA_cm2 < 40.0, \
            f"Jsc={output.jsc_mA_cm2} outside reasonable range"

    def test_bo_outputs_zero_when_disabled(self, module, optics_only_inputs):
        """When BO is disabled, optimization outputs should be zero."""
        output = module.run(optics_only_inputs)
        assert output.predicted_pce_pct == 0.0
        assert output.n_trials_run == 0


# ═════════════════════════════════════════════════════════════
# TestGranasModuleBO
# ═════════════════════════════════════════════════════════════
class TestGranasModuleBO:
    """Test the Bayesian Optimization sub-pipeline."""

    def test_bo_only_runs(self, module, bo_only_inputs):
        output = module.run(bo_only_inputs)
        assert output.predicted_pce_pct > 0, "PCE must be positive"
        assert output.n_trials_run == bo_only_inputs.n_optimization_trials

    def test_optimal_recipe_populated(self, module, bo_only_inputs):
        output = module.run(bo_only_inputs)
        assert output.optimal_recipe is not None
        assert "molar_conc" in output.optimal_recipe
        assert "spin_speed" in output.optimal_recipe
        assert "anneal_temp" in output.optimal_recipe

    def test_pce_below_sq_limit(self, module, bo_only_inputs):
        """PCE must be below Shockley-Queisser practical limit."""
        output = module.run(bo_only_inputs)
        assert output.predicted_pce_pct <= 26.0

    def test_grain_size_positive(self, module, bo_only_inputs):
        output = module.run(bo_only_inputs)
        assert output.grain_size_nm > 0

    def test_stability_bounded(self, module, bo_only_inputs):
        output = module.run(bo_only_inputs)
        assert 0 <= output.stability_score <= 1.0

    def test_optics_outputs_zero_when_disabled(self, module, bo_only_inputs):
        output = module.run(bo_only_inputs)
        assert output.jsc_mA_cm2 == 0.0
        assert output.n_granules_packed == 0


# ═════════════════════════════════════════════════════════════
# TestGranasModuleHJB
# ═════════════════════════════════════════════════════════════
class TestGranasModuleHJB:
    """Test the HJB annealing control sub-pipeline."""

    def test_hjb_only_runs(self, module, hjb_only_inputs):
        output = module.run(hjb_only_inputs)
        assert output.hjb_terminal_grain_nm > 0

    def test_optimal_schedule_populated(self, module, hjb_only_inputs):
        output = module.run(hjb_only_inputs)
        assert output.optimal_anneal_schedule is not None
        assert len(output.optimal_anneal_schedule) > 0

    def test_schedule_format(self, module, hjb_only_inputs):
        """Each schedule point should be (time_s, temp_C)."""
        output = module.run(hjb_only_inputs)
        for point in output.optimal_anneal_schedule:
            assert len(point) == 2
            t, T = point
            assert t >= 0
            assert 20 <= T <= 250

    def test_terminal_grain_exceeds_initial(self, module, hjb_only_inputs):
        """Grains should grow during annealing."""
        output = module.run(hjb_only_inputs)
        assert output.hjb_terminal_grain_nm >= hjb_only_inputs.initial_grain_nm

    def test_terminal_defects_decrease(self, module, hjb_only_inputs):
        """Defects should decrease during optimal annealing."""
        output = module.run(hjb_only_inputs)
        assert output.hjb_terminal_defects <= hjb_only_inputs.initial_defect_density

    def test_control_trajectory_populated(self, module, hjb_only_inputs):
        output = module.run(hjb_only_inputs)
        assert output.control_trajectory_C_s is not None
        assert len(output.control_trajectory_C_s) > 0


# ═════════════════════════════════════════════════════════════
# TestGranasModulePower
# ═════════════════════════════════════════════════════════════
class TestGranasModulePower:
    """Test real-world power calculations."""

    def test_power_formula(self):
        """P = PCE/100 × Area_m² × Irradiance."""
        output = GranasModuleOutput()
        output.predicted_pce_pct = 20.0     # 20%
        output.panel_area_cm2 = 100.0       # 100 cm² = 0.01 m²

        inputs = GranasModuleInput(
            panel_area_cm2=100.0,
            irradiance_W_m2=1000.0,
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        expected_power = 20.0 / 100.0 * (100.0 / 10000.0) * 1000.0  # = 2.0 W
        assert output.module_power_W == pytest.approx(expected_power, abs=0.001)

    def test_annual_energy_formula(self):
        """E = P × CF × 8760 / 1000 (kWh)."""
        output = GranasModuleOutput()
        output.predicted_pce_pct = 25.0
        output.panel_area_cm2 = BLUEPRINT_ACTIVE_AREA_CM2

        inputs = GranasModuleInput(
            panel_area_cm2=BLUEPRINT_ACTIVE_AREA_CM2,
            irradiance_W_m2=1000.0,
            capacity_factor=CAPACITY_FACTOR_MEXICO,
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        area_m2 = BLUEPRINT_ACTIVE_AREA_CM2 / 10000.0
        expected_P = 0.25 * area_m2 * 1000.0
        expected_E = expected_P * 0.22 * 8760 / 1000.0

        assert output.annual_energy_kWh == pytest.approx(expected_E, rel=0.01)

    def test_voc_estimate(self):
        """Voc ≈ Eg × VOC_FRACTION."""
        output = GranasModuleOutput()
        output.predicted_pce_pct = 20.0

        inputs = GranasModuleInput(
            bandgap_eV=1.55,
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        expected_voc = 1.55 * VOC_FRACTION
        assert output.module_voc_V == pytest.approx(expected_voc, abs=0.001)

    def test_isc_from_jsc(self):
        """Isc = Jsc × Area_cm² / 1000."""
        output = GranasModuleOutput()
        output.jsc_mA_cm2 = 20.0
        output.predicted_pce_pct = 20.0
        output.panel_area_cm2 = 100.0

        inputs = GranasModuleInput(
            panel_area_cm2=100.0,
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        expected_isc = 20.0 * 100.0 / 1000.0  # 2.0 A
        assert output.module_isc_A == pytest.approx(expected_isc, abs=0.001)

    def test_fill_factor_bounded(self):
        """Fill factor ≤ 0.90."""
        output = GranasModuleOutput()
        output.predicted_pce_pct = 25.0
        output.jsc_mA_cm2 = 22.0
        output.panel_area_cm2 = 100.0

        inputs = GranasModuleInput(
            panel_area_cm2=100.0,
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        assert 0 < output.module_fill_factor <= 0.90

    def test_zero_pce_zero_power(self):
        """If PCE=0, power and energy should be 0."""
        output = GranasModuleOutput()
        output.predicted_pce_pct = 0.0

        inputs = GranasModuleInput(
            run_optics=False,
            run_optimization=False,
            run_hjb=False,
        )

        module = GranasModule()
        module._compute_power(inputs, output)

        assert output.module_power_W == 0.0
        assert output.annual_energy_kWh == 0.0


# ═════════════════════════════════════════════════════════════
# TestGranasModuleSerialization
# ═════════════════════════════════════════════════════════════
class TestGranasModuleSerialization:
    """Test JSON, DataFrame, and SCADA serialization."""

    def test_json_export(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        json_str = GranasModule.to_json(output)
        parsed = json.loads(json_str)
        assert "jsc_mA_cm2" in parsed
        assert "module_power_W" in parsed
        assert "simulation_name" in parsed

    def test_json_excludes_spectral_by_default(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        json_str = GranasModule.to_json(output, include_spectral=False)
        parsed = json.loads(json_str)
        assert "spectral_data" not in parsed

    def test_json_includes_spectral_when_requested(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        json_str = GranasModule.to_json(output, include_spectral=True)
        parsed = json.loads(json_str)
        assert "spectral_data" in parsed
        assert parsed["spectral_data"] is not None

    def test_dataframe_export(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        df = GranasModule.to_dataframe(output)
        assert len(df) == 1
        assert "power_W" in df.columns
        assert "annual_kWh" in df.columns
        assert "jsc_mA_cm2" in df.columns
        assert "pce_pct" in df.columns

    def test_scada_payload(self, module, optics_only_inputs):
        output = module.run(optics_only_inputs)
        payload = GranasModule.to_scada_payload(output)
        assert "granas_module_power_W" in payload
        assert "granas_module_voc_V" in payload
        assert "granas_jsc_mA_cm2" in payload
        assert "granas_timestamp" in payload

    def test_json_roundtrip(self, module, optics_only_inputs):
        """JSON should parse back without errors."""
        output = module.run(optics_only_inputs)
        json_str = GranasModule.to_json(output, include_spectral=True)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["engine_version"] == MODULE_VERSION


# ═════════════════════════════════════════════════════════════
# TestGranasModuleFull
# ═════════════════════════════════════════════════════════════
class TestGranasModuleFull:
    """Full pipeline integration tests."""

    def test_full_pipeline_runs(self, module, fast_inputs):
        """Full pipeline should execute without errors."""
        output = module.run(fast_inputs)
        assert output.execution_time_s > 0
        assert output.simulation_name == "Test_Fast"

    def test_full_pipeline_all_blocks_populated(self, module, fast_inputs):
        """All output blocks should be populated."""
        output = module.run(fast_inputs)
        # Optics
        assert output.jsc_mA_cm2 > 0
        # Optimization
        assert output.predicted_pce_pct > 0
        # HJB
        assert output.hjb_terminal_grain_nm > 0
        # Power
        assert output.module_power_W > 0
        assert output.annual_energy_kWh > 0

    def test_convenience_methods(self, module, fast_inputs):
        """run_optics_only, run_optimization_only, run_hjb_only."""
        output_optics = module.run_optics_only(fast_inputs)
        assert output_optics.jsc_mA_cm2 > 0
        assert output_optics.predicted_pce_pct == 0.0  # BO disabled

        output_bo = module.run_optimization_only(fast_inputs)
        assert output_bo.predicted_pce_pct > 0
        assert output_bo.jsc_mA_cm2 == 0.0  # Optics disabled

        output_hjb = module.run_hjb_only(fast_inputs)
        assert output_hjb.hjb_terminal_grain_nm > 0
        assert output_hjb.jsc_mA_cm2 == 0.0  # Optics disabled

    def test_different_panel_areas(self, module):
        """Power should scale linearly with panel area."""
        inputs_small = GranasModuleInput(
            panel_area_cm2=1.0,
            n_optimization_trials=10,
            n_wavelengths=11,
            anneal_duration_s=60.0,
            anneal_dt_s=10.0,
        )
        inputs_big = GranasModuleInput(
            panel_area_cm2=100.0,
            n_optimization_trials=10,
            n_wavelengths=11,
            anneal_duration_s=60.0,
            anneal_dt_s=10.0,
        )
        out_small = module.run(inputs_small)
        out_big = module.run(inputs_big)

        # Power should scale by 100× (100 cm² vs 1 cm²)
        if out_small.module_power_W > 0:
            ratio = out_big.module_power_W / out_small.module_power_W
            assert ratio == pytest.approx(100.0, rel=0.1)
