import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lines = [f"L_{i}" for i in range(9)]
    ods = ["OD_3_2", "OD_2_0", "OD_0_1", "OD_1_3", "OD_3_4",
           "OD_1_0", "OD_1_4", "OD_2_3", "OD_4_3", "OD_4_0"]
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

    st_lines = {
        0: ["L_3", "L_4", "L_5", "L_7", "L_8"],
        1: ["L_1", "L_4"],
        2: ["L_1", "L_6"],
        3: [],
        4: ["L_0", "L_3", "L_4"],
    }

    fixed_cost = params["fixed_cost"]
    op_cost = params["operational_cost"]
    pen_cost = params["penalty_cost"]
    demand = params["demand"]
    veh_usage = params["vehicle_usage"]
    min_freq = params["min_frequency"]
    max_freq = params["max_frequency"]
    veh_cap = params["vehicle_capacity"]

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=lines, ordered=True)
    model.OD = pyo.Set(initialize=ods, ordered=True)
    model.ST = pyo.Set(initialize=stations, ordered=True)

    model.fixed_cost = pyo.Param(model.L, initialize=lambda m, l: fixed_cost[l])
    model.op_cost = pyo.Param(model.L, initialize=lambda m, l: op_cost[l])
    model.pen_cost = pyo.Param(model.OD, initialize=lambda m, o: pen_cost[o])
    model.demand = pyo.Param(model.OD, initialize=lambda m, o: demand[o])
    model.veh_usage = pyo.Param(model.L, initialize=lambda m, l: veh_usage[l])

    model.y = pyo.Var(model.L, domain=pyo.Binary)
    model.freq = pyo.Var(model.L, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.OD, domain=pyo.NonNegativeReals)
    model.transfer = pyo.Var(model.ST, domain=pyo.Binary)

    def obj_rule(m):
        return (sum(m.fixed_cost[l] * m.y[l] for l in m.L)
                + sum(m.op_cost[l] * m.freq[l] for l in m.L)
                + sum(m.pen_cost[o] * m.unmet[o] for o in m.OD))
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def freq_lb_rule(m, l):
        return m.freq[l] >= min_freq * m.y[l]
    model.freq_lb = pyo.Constraint(model.L, rule=freq_lb_rule)

    def freq_ub_rule(m, l):
        return m.freq[l] <= max_freq * m.y[l]
    model.freq_ub = pyo.Constraint(model.L, rule=freq_ub_rule)

    def demand_rule(m, o):
        return sum(m.freq[l] for l in od_lines[o]) + m.unmet[o] >= m.demand[o]
    model.demand_sat = pyo.Constraint(model.OD, rule=demand_rule)

    def veh_rule(m):
        return sum(m.veh_usage[l] * m.freq[l] for l in m.L) <= veh_cap
    model.veh_cap_con = pyo.Constraint(rule=veh_rule)

    def transfer_rule(m, s):
        if len(st_lines[s]) < 2:
            return m.transfer[s] == 0
        return 2 * m.transfer[s] <= sum(m.y[l] for l in st_lines[s])
    model.transfer_con = pyo.Constraint(model.ST, rule=transfer_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}