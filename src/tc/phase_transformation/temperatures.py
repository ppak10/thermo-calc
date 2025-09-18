import math

from pint import Quantity
from tc_python import (
    CalculationAxis,
    Linear,
    TCPython,
    ThermodynamicQuantity,
    PhaseNameStyle,
)
from typing_extensions import cast

from tc.database.utils import select_thermocalc_database
from tc.schema import Composition, PhaseTransformationTemperatures

TEMPERATURE_MIN = 500.0
TEMPERATURE_MAX = 3500.0


def compute_phase_transformation_temperatures(
    composition: Composition,
    temperature_min=TEMPERATURE_MIN,
    temperature_max=TEMPERATURE_MAX,
) -> PhaseTransformationTemperatures:
    """
    Uses Thermo-Calc to compute solidus & liquidus from elements/fractions.
    Returns (solidus_K, liquidus_K, database_name)
    """
    database = select_thermocalc_database(composition)

    elements = composition.elements()
    fractions = composition.fractions()

    with TCPython() as client:
        client.set_cache_folder("cache")
        client.set_ges_version(6)

        calc = (
            client.select_database_and_elements(database, elements)
            .get_system()
            .with_property_diagram_calculation()
            .with_axis(
                CalculationAxis(ThermodynamicQuantity.temperature())
                .set_min(temperature_min)
                .set_max(temperature_max)
                .with_axis_type(Linear().set_min_nr_of_steps(50))
            )
        )

        # Set composition via mass fractions. Skip the first element; Thermo-Calc will normalize.
        for el, wf in list(fractions.items())[1:]:
            calc.set_condition(f"W({el})", wf)

        diagram = calc.calculate()

        print(diagram)
        diagram.set_phase_name_style(PhaseNameStyle.ALL)

        groups = diagram.get_values_grouped_by_quantity_of(
            ThermodynamicQuantity.temperature(),
            ThermodynamicQuantity.volume_fraction_of_a_phase("LIQUID"),
        )

    solidus_T = None
    liquidus_T = None

    for group in groups.values():
        xT = group.x
        yL = group.y

        # Find solidus: last temperature where liquid fraction is essentially 0
        for i in range(len(yL)):
            if yL[i] > 1e-6:  # First point where liquid starts forming
                solidus_T = xT[i - 1] if i > 0 else xT[i]
                break

        # Find liquidus: first temperature where liquid fraction is essentially 1
        for i in range(len(yL)):
            if abs(yL[i] - 1.0) < 1e-6:  # First point where it's fully liquid
                liquidus_T = xT[i]
                break

    if solidus_T is None and liquidus_T is None:
        raise RuntimeError(
            f"Could not determine solidus and liquidus temperatures within range [{temperature_min:.1f}, {temperature_max:.1f}] K. Potentially an invalid composition, please try a different composition."
        )

    if solidus_T is None:
        raise RuntimeError(
            f"Could not determine solidus temperatrue within range [{temperature_min:.1f}, {temperature_max:.1f}] K. Potentially an invalid composition, please try a different composition."
        )

    if liquidus_T is None:
        raise RuntimeError(
            f"Could not determine liquidus temperatrue within range [{temperature_min:.1f}, {temperature_max:.1f}] K. Potentially an invalid composition, please try a different composition."
        )

    if math.isnan(solidus_T) or math.isnan(liquidus_T):
        raise RuntimeError(
            f"Encountered invalid liquidus / solidus temperature values. Potentially an invalid composition, please try a different composition."
        )

    temperature_melt = cast(Quantity, Quantity((liquidus_T + solidus_T) / 2, "K"))
    temperature_liquidus = cast(Quantity, Quantity(liquidus_T, "K"))
    temperature_solidus = cast(Quantity, Quantity(solidus_T, "K"))

    phase_transformation_temperatures = PhaseTransformationTemperatures(
        name=composition.name,
        temperature_melt=temperature_melt,
        temperature_liquidus=temperature_liquidus,
        temperature_solidus=temperature_solidus,
    )

    return phase_transformation_temperatures
