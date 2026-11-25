# IR: {"sets":{"lines":["L_0","L_1","L_2","L_3","L_4","L_5","L_6","L_7","L_8"],"stations":[0,1,2,3,4],"od_pairs":["OD_3_2","OD_2_0","OD_0_1","OD_1_3","OD_3_4","OD_1_0","OD_1_4","OD_2_3","OD_4_3","OD_4_0"],"serving_lines":{"OD_3_2":["L_0","L_3","L_4","L_5","L_6"],"OD_2_0":["L_2","L_7","L_8"],"OD_0_1":["L_0","L_3","L_5","L_7"],"OD_1_3":["L_8"],"OD_3_4":["L_3","L_6","L_7","L_8"],"OD_1_0":["L_2","L_8"],"OD_1_4":["L_1","L_5","L_7"],"OD_2_3":["L_5"],"OD_4_3":["L_3","L_5","L_8"],"OD_4_0":["L_3","L_5"]},"station_lines":{"0":["L_3","L_4","L_5","L_7","L_8"],"1":["L_1","L_4"],"2":["L_1","L_6"],"3":[],"4":["L_0","L_3","L_4"]}},"params":{"fixed_cost":"nonnegative[line]","operational_cost":"nonnegative[line]","penalty_cost":"nonnegative[od]","demand":"nonnegative[od]","min_frequency":"nonnegative scalar","max_frequency":"nonnegative scalar","total_vehicle_limit":"nonnegative scalar","vehicle_usage_per_frequency":"nonnegative[line]"},"input_indexing":"Indexed parameters accept canonical labels, zero-based integer keys, zero-based string keys, or sequences in the declared set order; normalize to canonical labels before constructing Pyomo Params.","decision_variables":{"selected":"binary[line]","frequency":"nonnegative real[line]","unmet":"nonnegative real[od]","transfer":"binary[station]"},"constraints":["For each od: sum(frequency[line] for line in serving_lines[od]) + unmet[od] >= demand[od].","For each line: frequency[line] >= min_frequency * selected[line].","For each line: frequency[line] <= max_frequency * selected[line].","sum(vehicle_usage_per_frequency[line] * frequency[line] for line in lines) <= total_vehicle_limit.","For each station: 2 * transfer[station] <= sum(selected[line] for line in station_lines[station])."],"objective":"Minimize sum(fixed_cost[line]*selected[line] + operational_cost[line]*frequency[line] for line in lines) + sum(penalty_cost[od]*unmet[od] for od in od_pairs).","assumptions":["Candidate lines are fixed continuous routes selected as a whole; arc topology was not supplied, so independent arc-level continuity cannot be formulated or verified.","Station-to-line incidence lists are exhaustive."]}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _normalize_indexed_values(raw_values, labels):
    """Convert labeled or positional input into a canonical-label dictionary."""
    if isinstance(raw_values, Mapping):
        canonical_keys = tuple(labels)
        integer_keys = tuple(range(len(labels)))
        string_keys = tuple(str(position) for position in integer_keys)

        for candidate_keys in (canonical_keys, integer_keys, string_keys):
            if all(key in raw_values for key in candidate_keys):
                return {
                    label: raw_values[key]
                    for label, key in zip(labels, candidate_keys)
                }

        raise ValueError(
            "Indexed parameter must contain all canonical labels or all "
            "zero-based positional keys."
        )

    if isinstance(raw_values, (str, bytes)):
        raise TypeError("Indexed parameter must be a mapping or a sequence.")

    values = tuple(raw_values)
    if len(values) != len(labels):
        raise ValueError(
            f"Indexed parameter requires {len(labels)} values; "
            f"received {len(values)}."
        )

    return dict(zip(labels, values))


def solve(params):
    lines = tuple(f"L_{line_index}" for line_index in range(9))
    stations = tuple(range(5))

    serving_lines = {
        "OD_3_2": ("L_0", "L_3", "L_4", "L_5", "L_6"),
        "OD_2_0": ("L_2", "L_7", "L_8"),
        "OD_0_1": ("L_0", "L_3", "L_5", "L_7"),
        "OD_1_3": ("L_8",),
        "OD_3_4": ("L_3", "L_6", "L_7", "L_8"),
        "OD_1_0": ("L_2", "L_8"),
        "OD_1_4": ("L_1", "L_5", "L_7"),
        "OD_2_3": ("L_5",),
        "OD_4_3": ("L_3", "L_5", "L_8"),
        "OD_4_0": ("L_3", "L_5"),
    }
    od_pairs = tuple(serving_lines)

    station_lines = {
        0: ("L_3", "L_4", "L_5", "L_7", "L_8"),
        1: ("L_1", "L_4"),
        2: ("L_1", "L_6"),
        3: (),
        4: ("L_0", "L_3", "L_4"),
    }

    model = pyo.ConcreteModel()

    model.LINES = pyo.Set(initialize=lines, ordered=True)
    model.STATIONS = pyo.Set(initialize=stations, ordered=True)
    model.OD_PAIRS = pyo.Set(initialize=od_pairs, ordered=True)

    model.fixed_cost = pyo.Param(
        model.LINES,
        initialize=_normalize_indexed_values(params["fixed_cost"], lines),
        within=pyo.NonNegativeReals,
    )
    model.operational_cost = pyo.Param(
        model.LINES,
        initialize=_normalize_indexed_values(params["operational_cost"], lines),
        within=pyo.NonNegativeReals,
    )
    model.penalty_cost = pyo.Param(
        model.OD_PAIRS,
        initialize=_normalize_indexed_values(params["penalty_cost"], od_pairs),
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.OD_PAIRS,
        initialize=_normalize_indexed_values(params["demand"], od_pairs),
        within=pyo.NonNegativeReals,
    )
    model.min_frequency = pyo.Param(
        initialize=params["min_frequency"],
        within=pyo.NonNegativeReals,
    )
    model.max_frequency = pyo.Param(
        initialize=params["max_frequency"],
        within=pyo.NonNegativeReals,
    )
    model.total_vehicle_limit = pyo.Param(
        initialize=params["total_vehicle_limit"],
        within=pyo.NonNegativeReals,
    )
    model.vehicle_usage_per_frequency = pyo.Param(
        model.LINES,
        initialize=_normalize_indexed_values(
            params["vehicle_usage_per_frequency"], lines
        ),
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.LINES, domain=pyo.Binary)
    model.frequency = pyo.Var(model.LINES, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.OD_PAIRS, domain=pyo.NonNegativeReals)
    model.transfer = pyo.Var(model.STATIONS, domain=pyo.Binary)

    def demand_coverage_rule(mdl, od):
        return (
            sum(mdl.frequency[line] for line in serving_lines[od])
            + mdl.unmet[od]
            >= mdl.demand[od]
        )

    model.demand_coverage = pyo.Constraint(
        model.OD_PAIRS,
        rule=demand_coverage_rule,
    )

    def minimum_frequency_rule(mdl, line):
        return mdl.frequency[line] >= mdl.min_frequency * mdl.selected[line]

    model.minimum_frequency_bound = pyo.Constraint(
        model.LINES,
        rule=minimum_frequency_rule,
    )

    def maximum_frequency_rule(mdl, line):
        return mdl.frequency[line] <= mdl.max_frequency * mdl.selected[line]

    model.maximum_frequency_bound = pyo.Constraint(
        model.LINES,
        rule=maximum_frequency_rule,
    )

    model.vehicle_capacity = pyo.Constraint(
        expr=sum(
            model.vehicle_usage_per_frequency[line] * model.frequency[line]
            for line in model.LINES
        )
        <= model.total_vehicle_limit
    )

    def transfer_eligibility_rule(mdl, station):
        return 2 * mdl.transfer[station] <= sum(
            mdl.selected[line] for line in station_lines[station]
        )

    model.transfer_eligibility = pyo.Constraint(
        model.STATIONS,
        rule=transfer_eligibility_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[line] * model.selected[line]
            + model.operational_cost[line] * model.frequency[line]
            for line in model.LINES
        )
        + sum(
            model.penalty_cost[od] * model.unmet[od]
            for od in model.OD_PAIRS
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}