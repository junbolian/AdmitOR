# IR: {"sets":{"lines":["L_0","L_1","L_2","L_3","L_4","L_5","L_6","L_7","L_8"],"stations":[0,1,2,3,4],"od":["OD_3_2","OD_2_0","OD_0_1","OD_1_3","OD_3_4","OD_1_0","OD_1_4","OD_2_3","OD_4_3","OD_4_0"]},"params":{"fixed_cost":"lines -> nonnegative real","operational_cost":"lines -> nonnegative real","penalty_cost":"od -> nonnegative real","demand":"od -> nonnegative real","min_frequency":"nonnegative real","max_frequency":"nonnegative real","vehicle_capacity":"nonnegative real","vehicle_usage":"lines -> nonnegative real"},"input_format":"Indexed parameters accept mappings keyed by the listed identifiers or sequences in the listed set order; frequency bounds and vehicle_capacity are scalars.","variables":{"selected":"lines -> binary","frequency":"lines -> nonnegative real","unmet":"od -> nonnegative real","transfer":"stations -> binary"},"constraints":["sum(frequency[line] for line in serving[od]) + unmet[od] >= demand[od], for each od","frequency[line] >= min_frequency * selected[line], for each line","frequency[line] <= max_frequency * selected[line], for each line","sum(vehicle_usage[line] * frequency[line] for line in lines) <= vehicle_capacity","2 * transfer[station] <= sum(selected[line] for line in passing[station]), for each station"],"objective":"minimize sum(fixed_cost[line]*selected[line] + operational_cost[line]*frequency[line] for line in lines) + sum(penalty_cost[od]*unmet[od] for od in od)","serving":{"OD_3_2":["L_0","L_3","L_4","L_5","L_6"],"OD_2_0":["L_2","L_7","L_8"],"OD_0_1":["L_0","L_3","L_5","L_7"],"OD_1_3":["L_8"],"OD_3_4":["L_3","L_6","L_7","L_8"],"OD_1_0":["L_2","L_8"],"OD_1_4":["L_1","L_5","L_7"],"OD_2_3":["L_5"],"OD_4_3":["L_3","L_5","L_8"],"OD_4_0":["L_3","L_5"]},"passing":{"0":["L_3","L_4","L_5","L_7","L_8"],"1":["L_1","L_4"],"2":["L_1","L_6"],"3":[],"4":["L_0","L_3","L_4"]},"assumptions":["Candidate lines are fixed continuous routes. No arc data are provided, so arc-level route continuity is assumed rather than independently optimized.","Frequencies and unmet demand are continuous."]}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_values(values, keys, parameter_name):
    """Normalize an identifier-keyed mapping or an ordered sequence."""
    if isinstance(values, Mapping):
        return {key: values[key] for key in keys}

    if len(values) != len(keys):
        raise ValueError(
            f"{parameter_name} must contain exactly {len(keys)} entries."
        )

    return {key: values[position] for position, key in enumerate(keys)}


def solve(params):
    lines = tuple(f"L_{position}" for position in range(9))
    stations = tuple(range(5))
    od_pairs = (
        "OD_3_2",
        "OD_2_0",
        "OD_0_1",
        "OD_1_3",
        "OD_3_4",
        "OD_1_0",
        "OD_1_4",
        "OD_2_3",
        "OD_4_3",
        "OD_4_0",
    )

    serving = {
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
    passing = {
        0: ("L_3", "L_4", "L_5", "L_7", "L_8"),
        1: ("L_1", "L_4"),
        2: ("L_1", "L_6"),
        3: (),
        4: ("L_0", "L_3", "L_4"),
    }

    model = pyo.ConcreteModel()
    model.lines = pyo.Set(initialize=lines, ordered=True)
    model.od_pairs = pyo.Set(initialize=od_pairs, ordered=True)
    model.stations = pyo.Set(initialize=stations, ordered=True)

    model.fixed_cost = pyo.Param(
        model.lines,
        initialize=_indexed_values(params["fixed_cost"], lines, "fixed_cost"),
        within=pyo.NonNegativeReals,
    )
    model.operational_cost = pyo.Param(
        model.lines,
        initialize=_indexed_values(
            params["operational_cost"], lines, "operational_cost"
        ),
        within=pyo.NonNegativeReals,
    )
    model.penalty_cost = pyo.Param(
        model.od_pairs,
        initialize=_indexed_values(
            params["penalty_cost"], od_pairs, "penalty_cost"
        ),
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.od_pairs,
        initialize=_indexed_values(params["demand"], od_pairs, "demand"),
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
    model.vehicle_capacity = pyo.Param(
        initialize=params["vehicle_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.vehicle_usage = pyo.Param(
        model.lines,
        initialize=_indexed_values(
            params["vehicle_usage"], lines, "vehicle_usage"
        ),
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.lines, domain=pyo.Binary)
    model.frequency = pyo.Var(model.lines, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.od_pairs, domain=pyo.NonNegativeReals)
    model.transfer = pyo.Var(model.stations, domain=pyo.Binary)

    def demand_rule(instance, od):
        return (
            pyo.quicksum(instance.frequency[line] for line in serving[od])
            + instance.unmet[od]
            >= instance.demand[od]
        )

    model.demand_coverage = pyo.Constraint(
        model.od_pairs, rule=demand_rule
    )

    def minimum_frequency_rule(instance, line):
        return (
            instance.frequency[line]
            >= instance.min_frequency * instance.selected[line]
        )

    model.minimum_frequency_limit = pyo.Constraint(
        model.lines, rule=minimum_frequency_rule
    )

    def maximum_frequency_rule(instance, line):
        return (
            instance.frequency[line]
            <= instance.max_frequency * instance.selected[line]
        )

    model.maximum_frequency_limit = pyo.Constraint(
        model.lines, rule=maximum_frequency_rule
    )

    model.vehicle_limit = pyo.Constraint(
        expr=pyo.quicksum(
            model.vehicle_usage[line] * model.frequency[line]
            for line in model.lines
        )
        <= model.vehicle_capacity
    )

    def transfer_rule(instance, station):
        return (
            2 * instance.transfer[station]
            <= pyo.quicksum(
                instance.selected[line] for line in passing[station]
            )
        )

    model.transfer_eligibility = pyo.Constraint(
        model.stations, rule=transfer_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.fixed_cost[line] * model.selected[line]
            + model.operational_cost[line] * model.frequency[line]
            for line in model.lines
        )
        + pyo.quicksum(
            model.penalty_cost[od] * model.unmet[od]
            for od in model.od_pairs
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is determined exclusively by objective retrieval below.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}