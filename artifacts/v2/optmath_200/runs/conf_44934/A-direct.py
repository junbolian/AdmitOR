import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lines = [f"L_{i}" for i in range(10)]
    ods = ["OD_6_7", "OD_6_1", "OD_3_0", "OD_4_6", "OD_1_0", "OD_5_3",
           "OD_4_2", "OD_4_1", "OD_1_4", "OD_2_3", "OD_4_0", "OD_6_4"]
    stations = [f"S_{i}" for i in range(8)]

    fixed_cost = params["fixed_cost"]
    op_cost = params["operational_cost_per_freq"]
    cap_per_trip = params["capacity_per_trip"]
    res_per_trip = params["resource_usage_per_trip"]
    min_freq = params["min_frequency"]
    max_freq = params["max_frequency"]
    demand = params["demand"]
    penalty_unmet = params["penalty_unmet"]
    res_budget = params["total_resource_budget"]

    od_lines = {
        "OD_6_7": ["L_0", "L_1", "L_2"],
        "OD_6_1": ["L_1", "L_3", "L_4"],
        "OD_3_0": ["L_2", "L_5"],
        "OD_4_6": ["L_0", "L_4", "L_6"],
        "OD_1_0": ["L_3", "L_7"],
        "OD_5_3": ["L_5", "L_8"],
        "OD_4_2": ["L_4", "L_6", "L_9"],
        "OD_4_1": ["L_6", "L_7", "L_8"],
        "OD_1_4": ["L_1", "L_4", "L_9"],
        "OD_2_3": ["L_2", "L_8"],
        "OD_4_0": ["L_0", "L_7", "L_9"],
        "OD_6_4": ["L_3", "L_6", "L_8"],
    }

    station_lines = {
        "S_0": ["L_0", "L_2", "L_5"],
        "S_1": ["L_1", "L_3", "L_4"],
        "S_2": ["L_4", "L_6", "L_9"],
        "S_3": ["L_2", "L_5", "L_8"],
        "S_4": ["L_0", "L_4", "L_6"],
        "S_5": ["L_3", "L_7"],
        "S_6": ["L_6", "L_7", "L_8"],
        "S_7": ["L_0", "L_7", "L_9"],
    }

    model = pyo.ConcreteModel()

    model.LINES = pyo.Set(initialize=lines, ordered=True)
    model.ODS = pyo.Set(initialize=ods, ordered=True)
    model.STATIONS = pyo.Set(initialize=stations, ordered=True)

    model.select = pyo.Var(model.LINES, domain=pyo.Binary)
    model.freq = pyo.Var(model.LINES, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.ODS, domain=pyo.NonNegativeReals)
    model.transfer = pyo.Var(model.STATIONS, domain=pyo.Binary)

    model.freq_upper = pyo.Constraint(
        model.LINES, rule=lambda mdl, l: mdl.freq[l] <= max_freq[l] * mdl.select[l]
    )
    model.freq_lower = pyo.Constraint(
        model.LINES, rule=lambda mdl, l: mdl.freq[l] >= min_freq[l] * mdl.select[l]
    )

    model.demand_con = pyo.Constraint(
        model.ODS,
        rule=lambda mdl, od: sum(cap_per_trip[l] * mdl.freq[l] for l in od_lines[od])
        + mdl.unmet[od] >= demand[od],
    )

    model.min_freq_con = pyo.Constraint(
        model.ODS,
        rule=lambda mdl, od: sum(mdl.freq[l] for l in od_lines[od]) >= min_freq[od_lines[od][0]],
    )

    model.resource_con = pyo.Constraint(
        rule=lambda mdl: sum(res_per_trip[l] * mdl.freq[l] for l in lines) <= res_budget
    )

    model.transfer_con = pyo.Constraint(
        model.STATIONS,
        rule=lambda mdl, s: mdl.transfer[s] <= sum(mdl.select[l] for l in station_lines[s]) / 2.0,
    )

    model.total_cost = pyo.Objective(
        rule=lambda mdl: sum(fixed_cost[l] * mdl.select[l] for l in lines)
        + sum(op_cost[l] * mdl.freq[l] for l in lines)
        + sum(penalty_unmet[od] * mdl.unmet[od] for od in ods),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}