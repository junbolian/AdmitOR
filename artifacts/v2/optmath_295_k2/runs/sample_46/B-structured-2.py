# IR: {"sets":{"L":["L_0","L_1","L_2","L_3","L_4","L_5","L_6","L_7","L_8"],"D":["OD_3_2","OD_2_0","OD_0_1","OD_1_3","OD_3_4","OD_1_0","OD_1_4","OD_2_3","OD_4_3","OD_4_0"],"S":[0,1,2,3,4]},"params":{"fixed_cost":"L -> real","operational_cost":"L -> real","penalty_cost":"D -> real","demand":"D -> nonnegative real","min_frequency":"nonnegative real","max_frequency":"nonnegative real","vehicle_capacity":"nonnegative real","vehicle_usage":"L -> nonnegative real"},"input_encoding":"Indexed parameters may be dictionaries keyed by identifiers or sequences in the corresponding set order; other parameters are scalars.","structural_data":{"serving_lines":{"OD_3_2":["L_0","L_3","L_4","L_5","L_6"],"OD_2_0":["L_2","L_7","L_8"],"OD_0_1":["L_0","L_3","L_5","L_7"],"OD_1_3":["L_8"],"OD_3_4":["L_3","L_6","L_7","L_8"],"OD_1_0":["L_2","L_8"],"OD_1_4":["L_1","L_5","L_7"],"OD_2_3":["L_5"],"OD_4_3":["L_3","L_5","L_8"],"OD_4_0":["L_3","L_5"]},"station_lines":{"0":["L_3","L_4","L_5","L_7","L_8"],"1":["L_1","L_4"],"2":["L_1","L_6"],"3":[],"4":["L_0","L_3","L_4"]}},"variables":{"selected[L]":"binary","frequency[L]":"nonnegative continuous","unmet[D]":"nonnegative continuous","transfer[S]":"binary"},"constraints":["sum(frequency[line] for line in serving_lines[od]) + unmet[od] >= demand[od] for each od in D","frequency[line] >= min_frequency * selected[line] for each line in L","frequency[line] <= max_frequency * selected[line] for each line in L","sum(vehicle_usage[line] * frequency[line] for line in L) <= vehicle_capacity","sum(selected[line] for line in station_lines[station]) >= 2 * transfer[station] for each station in S"],"objective":"minimize sum(fixed_cost[line]*selected[line] + operational_cost[line]*frequency[line] for line in L) + sum(penalty_cost[od]*unmet[od] for od in D)","assumptions":["Candidate lines are predefined continuous routes; no arc topology is supplied, so route construction and independent arc-continuity constraints cannot be specified.","Station incidences govern transfer eligibility only."]}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_values(values, identifiers, parameter_name):
    """Normalize identifier-keyed dictionaries or position-indexed sequences."""
    if isinstance(values, Mapping):
        return {identifier: values[identifier] for identifier in identifiers}

    if len(values) != len(identifiers):
        raise ValueError(
            f"{parameter_name} must contain exactly "
            f"{len(identifiers)} values."
        )

    return {
        identifier: values[position]
        for position, identifier in enumerate(identifiers)
    }


def solve(params):
    lines = tuple(f"L_{line_idx}" for line_idx in range(9))
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
    station_lines = {
        0: ("L_3", "L_4", "L_5", "L_7", "L_8"),
        1: ("L_1", "L_4"),
        2: ("L_1", "L_6"),
        3: (),
        4: ("L_0", "L_3", "L_4"),
    }

    fixed_cost = _indexed_values(params["fixed_cost"], lines, "fixed_cost")
    operational_cost = _indexed_values(
        params["operational_cost"], lines, "operational_cost"
    )
    penalty_cost = _indexed_values(
        params["penalty_cost"], od_pairs, "penalty_cost"
    )
    demand = _indexed_values(params["demand"], od_pairs, "demand")
    vehicle_usage = _indexed_values(
        params["vehicle_usage"], lines, "vehicle_usage"
    )

    model = pyo.ConcreteModel()
    model.L = pyo.Set(initialize=lines, ordered=True)
    model.D = pyo.Set(initialize=od_pairs, ordered=True)
    model.S = pyo.Set(initialize=stations, ordered=True)

    model.fixed_cost = pyo.Param(
        model.L, initialize=fixed_cost, within=pyo.Reals
    )
    model.operational_cost = pyo.Param(
        model.L, initialize=operational_cost, within=pyo.Reals
    )
    model.penalty_cost = pyo.Param(
        model.D, initialize=penalty_cost, within=pyo.Reals
    )
    model.demand = pyo.Param(
        model.D, initialize=demand, within=pyo.NonNegativeReals
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
        model.L, initialize=vehicle_usage, within=pyo.NonNegativeReals
    )

    model.selected = pyo.Var(model.L, domain=pyo.Binary)
    model.frequency = pyo.Var(model.L, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.D, domain=pyo.NonNegativeReals)
    model.transfer = pyo.Var(model.S, domain=pyo.Binary)

    def demand_rule(mod, od):
        return (
            sum(mod.frequency[line] for line in serving_lines[od])
            + mod.unmet[od]
            >= mod.demand[od]
        )

    model.demand_requirement = pyo.Constraint(model.D, rule=demand_rule)

    def minimum_frequency_rule(mod, line):
        return mod.frequency[line] >= mod.min_frequency * mod.selected[line]

    model.frequency_lower_link = pyo.Constraint(
        model.L, rule=minimum_frequency_rule
    )

    def maximum_frequency_rule(mod, line):
        return mod.frequency[line] <= mod.max_frequency * mod.selected[line]

    model.frequency_upper_link = pyo.Constraint(
        model.L, rule=maximum_frequency_rule
    )

    model.fleet_limit = pyo.Constraint(
        expr=sum(
            model.vehicle_usage[line] * model.frequency[line]
            for line in model.L
        )
        <= model.vehicle_capacity
    )

    def transfer_rule(mod, station):
        return (
            sum(mod.selected[line] for line in station_lines[station])
            >= 2 * mod.transfer[station]
        )

    model.transfer_eligibility = pyo.Constraint(
        model.S, rule=transfer_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[line] * model.selected[line]
            + model.operational_cost[line] * model.frequency[line]
            for line in model.L
        )
        + sum(
            model.penalty_cost[od] * model.unmet[od]
            for od in model.D
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}