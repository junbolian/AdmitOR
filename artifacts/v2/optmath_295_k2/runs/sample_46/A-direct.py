import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lines = [f"L_{i}" for i in range(9)]
    od_pairs = [
        "OD_3_2", "OD_2_0", "OD_0_1", "OD_1_3", "OD_3_4",
        "OD_1_0", "OD_1_4", "OD_2_3", "OD_4_3", "OD_4_0",
    ]
    stations = [0, 1, 2, 3, 4]

    od_lines = {
        "OD_3_2": ["L_0", "L_3", "L_4", "L_5", "L_6"],
        "OD_2_0": ["L_2", "L_7", "L_8"],
        "OD_0_1": ["L_0", "L_3", "L_5", "L_7"],
        "OD_1_3": ["L_8"],
        "OD_3_4": ["L_3", "L_6", "L_7", "L_8"],
        "OD_1_0": ["L_2", "L_8"],
        "OD_1_4": ["L_1", "L_5", "L_7"],
        "OD_2_3": ["L_5"],
        "OD_4_3": ["L_3", "L_5", "L_8"],
        "OD_4_0": ["L_3", "L_5"],
    }

    station_lines = {
        0: ["L_3", "L_4", "L_5", "L_7", "L_8"],
        1: ["L_1", "L_4"],
        2: ["L_1", "L_6"],
        3: [],
        4: ["L_0", "L_3", "L_4"],
    }

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=lines, ordered=True)
    model.OD = pyo.Set(initialize=od_pairs, ordered=True)
    model.S = pyo.Set(initialize=stations, ordered=True)

    fixed_cost = {L: params["fixed_cost"] for L in lines}
    operational_cost = {L: params["operational_cost"] for L in lines}
    vehicle_usage = {L: params["vehicle_usage"] for L in lines}
    penalty_cost = {od: params["penalty_cost"] for od in od_pairs}
    demand = {od: params["demand"] for od in od_pairs}

    model.y = pyo.Var(model.L, domain=pyo.Binary)
    model.z = pyo.Var(model.S, domain=pyo.Binary)
    model.f = pyo.Var(model.L, domain=pyo.NonNegativeReals)
    model.u = pyo.Var(model.OD, domain=pyo.NonNegativeReals)

    min_freq = params["min_frequency"]
    max_freq = params["max_frequency"]

    def freq_bounds_rule(m, L):
        return (min_freq * m.y[L], max_freq * m.y[L])
    model.freq_bounds = pyo.Constraint(model.L, rule=freq_bounds_rule)

    def demand_rule(m, od):
        expr = sum(m.f[L] for L in od_lines[od]) + m.u[od]
        return expr >= demand[od]
    model.demand_con = pyo.Constraint(model.OD, rule=demand_rule)

    def vehicle_rule(m):
        return sum(vehicle_usage[L] * m.f[L] for L in lines) <= params["vehicle_capacity"]
    model.vehicle_con = pyo.Constraint(rule=vehicle_rule)

    def transfer_rule(m, s):
        if len(station_lines[s]) < 2:
            return m.z[s] == 0
        return 2 * m.z[s] <= sum(m.y[L] for L in station_lines[s])
    model.transfer_con = pyo.Constraint(model.S, rule=transfer_rule)

    def obj_rule(m):
        fixed = sum(fixed_cost[L] * m.y[L] for L in lines)
        op = sum(operational_cost[L] * m.f[L] for L in lines)
        pen = sum(penalty_cost[od] * m.u[od] for od in od_pairs)
        return fixed + op + pen
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}