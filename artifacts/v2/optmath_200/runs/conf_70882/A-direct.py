import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    lines = [f"L_{i}" for i in range(12)]
    od_pairs = ["OD_7_4", "OD_5_4", "OD_0_6", "OD_4_0", "OD_3_1",
                "OD_7_0", "OD_4_7", "OD_7_2", "OD_3_5", "OD_7_6",
                "OD_2_1", "OD_2_3", "OD_4_1", "OD_1_6", "OD_0_7"]

    stations = [0, 1, 2, 3, 4, 5, 6, 7]

    station_lines = {
        0: ["L_0", "L_1", "L_2", "L_9", "L_11"],
        1: ["L_1", "L_3", "L_5"],
        2: ["L_2", "L_4", "L_6"],
        3: ["L_0", "L_3", "L_7"],
        4: ["L_4", "L_5", "L_6", "L_8"],
        5: ["L_5", "L_7", "L_9"],
        6: ["L_6", "L_8", "L_10"],
        7: ["L_1", "L_2", "L_7", "L_8", "L_10"],
    }

    od_lines = {
        "OD_7_4": ["L_1", "L_2", "L_8", "L_9", "L_10"],
        "OD_5_4": ["L_4", "L_5", "L_6", "L_8"],
        "OD_0_6": ["L_0", "L_1", "L_2", "L_6", "L_8", "L_10"],
        "OD_4_0": ["L_0", "L_4", "L_5", "L_6", "L_8"],
        "OD_3_1": ["L_1", "L_3", "L_5", "L_7"],
        "OD_7_0": ["L_1", "L_2", "L_7", "L_8", "L_10"],
        "OD_4_7": ["L_4", "L_5", "L_6", "L_7", "L_8", "L_10"],
        "OD_7_2": ["L_2", "L_4", "L_6", "L_7", "L_8", "L_10"],
        "OD_3_5": ["L_3", "L_5", "L_7", "L_9"],
        "OD_7_6": ["L_6", "L_7", "L_8", "L_10"],
        "OD_2_1": ["L_1", "L_2", "L_4", "L_6"],
        "OD_2_3": ["L_3", "L_4", "L_6", "L_7"],
        "OD_4_1": ["L_1", "L_3", "L_4", "L_5", "L_6"],
        "OD_1_6": ["L_1", "L_2", "L_6", "L_8", "L_10"],
        "OD_0_7": ["L_0", "L_1", "L_2", "L_7", "L_9", "L_11"],
    }

    # Fixed costs vector (index by position)
    fixed_vec = params["fixed_cost"]
    op_vec = params["operational_cost"]
    veh_vec = params["vehicle_time_per_frequency"]

    def as_list(v, n):
        if isinstance(v, dict):
            return [v[f"L_{i}"] for i in range(n)]
        return list(v)

    fixed_list = as_list(fixed_vec, 12)
    op_list = as_list(op_vec, 12)
    veh_list = as_list(veh_vec, 12)

    pen_raw = params["penalty_cost"]
    if isinstance(pen_raw, dict):
        penalty_map = {od: pen_raw[od] for od in od_pairs}
    else:
        penalty_map = {od: pen_raw for od in od_pairs}

    # Demand per OD: only OD_7_4 specified explicitly.
    od_demand = {od: 0.0 for od in od_pairs}
    od_demand["OD_7_4"] = params["example_od_7_4_demand"]

    model = pyo.ConcreteModel()

    model.LINES = pyo.Set(initialize=lines)
    model.OD = pyo.Set(initialize=od_pairs)
    model.STATIONS = pyo.Set(initialize=stations)

    model.fixed_cost = pyo.Param(model.LINES, initialize={lines[i]: fixed_list[i] for i in range(12)})
    model.operational_cost = pyo.Param(model.LINES, initialize={lines[i]: op_list[i] for i in range(12)})
    model.penalty_cost = pyo.Param(model.OD, initialize=penalty_map)
    model.vehicle_time = pyo.Param(model.LINES, initialize={lines[i]: veh_list[i] for i in range(12)})

    model.y = pyo.Var(model.LINES, domain=pyo.Binary)
    model.f = pyo.Var(model.LINES, domain=pyo.NonNegativeReals)
    model.u = pyo.Var(model.OD, domain=pyo.NonNegativeReals)
    model.h = pyo.Var(model.STATIONS, domain=pyo.Binary)

    min_f = params["min_frequency_if_selected"]
    max_f = params["max_frequency_if_selected"]
    min_od_f = params["min_od_frequency"]
    min_hub_lines = params["min_transfer_hub_lines"]

    def freq_lb_rule(m, l):
        return m.f[l] >= min_f * m.y[l]
    model.freq_lb = pyo.Constraint(model.LINES, rule=freq_lb_rule)

    def freq_ub_rule(m, l):
        return m.f[l] <= max_f * m.y[l]
    model.freq_ub = pyo.Constraint(model.LINES, rule=freq_ub_rule)

    def veh_rule(m):
        return sum(m.vehicle_time[l] * m.f[l] for l in m.LINES) <= params["total_vehicle_capacity"]
    model.veh = pyo.Constraint(rule=veh_rule)

    def od_minfreq_rule(m, od):
        return sum(m.f[l] for l in od_lines[od]) >= min_od_f
    model.od_minfreq = pyo.Constraint(model.OD, rule=od_minfreq_rule)

    def od_demand_rule(m, od):
        return sum(m.f[l] for l in od_lines[od]) + m.u[od] >= od_demand[od]
    model.od_demand_con = pyo.Constraint(model.OD, rule=od_demand_rule)

    def hub_rule(m, s):
        return sum(m.y[l] for l in station_lines[s]) >= min_hub_lines * m.h[s]
    model.hub_con = pyo.Constraint(model.STATIONS, rule=hub_rule)

    def obj_rule(m):
        return (sum(m.fixed_cost[l] * m.y[l] for l in m.LINES)
                + sum(m.operational_cost[l] * m.f[l] for l in m.LINES)
                + sum(m.penalty_cost[od] * m.u[od] for od in m.OD))
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}