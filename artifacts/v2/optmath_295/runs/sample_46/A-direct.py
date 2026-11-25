import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # --- Sets ---
    lines = list(range(9))  # L_0..L_8
    od_pairs = ["OD_3_2", "OD_2_0", "OD_0_1", "OD_1_3", "OD_3_4",
                "OD_1_0", "OD_1_4", "OD_2_3", "OD_4_3", "OD_4_0"]
    stations = list(range(5))  # 0..4

    # OD coverage: which lines serve each OD pair
    od_lines = {
        "OD_3_2": [0, 3, 4, 5, 6],
        "OD_2_0": [2, 7, 8],
        "OD_0_1": [0, 3, 5, 7],
        "OD_1_3": [8],
        "OD_3_4": [3, 6, 7, 8],
        "OD_1_0": [2, 8],
        "OD_1_4": [1, 5, 7],
        "OD_2_3": [5],
        "OD_4_3": [3, 5, 8],
        "OD_4_0": [3, 5],
    }

    # Station coverage: lines passing through each station
    station_lines = {
        0: [3, 4, 5, 7, 8],
        1: [1, 4],
        2: [1, 6],
        3: [],  # cannot be a transfer station
        4: [0, 3, 4],
    }

    # --- Parameters from params dict ---
    fixed_cost_raw = params["fixed_cost"]
    operational_cost_raw = params["operational_cost"]
    penalty_cost_raw = params["penalty_cost"]
    demand_raw = params["demand"]
    vehicle_usage_raw = params["vehicle_usage_per_frequency"]

    def pick(raw, key, idx):
        if isinstance(raw, dict):
            return raw[key]
        return raw[idx]

    fixed_cost = {i: pick(fixed_cost_raw, "L_%d" % i, i) for i in lines}
    operational_cost = {i: pick(operational_cost_raw, "L_%d" % i, i) for i in lines}
    penalty_cost = {od: pick(penalty_cost_raw, od, k)
                    for k, od in enumerate(od_pairs)}
    demand = {od: pick(demand_raw, od, k)
              for k, od in enumerate(od_pairs)}
    vehicle_usage_per_frequency = {
        i: pick(vehicle_usage_raw, "L_%d" % i, i) for i in lines
    }

    fmin = params["min_frequency"]
    fmax = params["max_frequency"]
    total_vehicle_limit = params["total_vehicle_limit"]

    # --- Decision Variables ---
    model.x = pyo.Var(lines, domain=pyo.Binary)            # line selected
    model.f = pyo.Var(lines, domain=pyo.NonNegativeReals)  # frequency
    model.u = pyo.Var(od_pairs, domain=pyo.NonNegativeReals)  # unmet demand
    model.y = pyo.Var(stations, domain=pyo.Binary)         # transfer station

    # --- Constraints ---
    def freq_min_rule(m, i):
        return m.f[i] >= fmin * m.x[i]

    def freq_max_rule(m, i):
        return m.f[i] <= fmax * m.x[i]

    model.freq_min = pyo.Constraint(lines, rule=freq_min_rule)
    model.freq_max = pyo.Constraint(lines, rule=freq_max_rule)

    def demand_rule(m, od):
        return sum(m.f[i] for i in od_lines[od]) + m.u[od] >= demand[od]

    model.demand_con = pyo.Constraint(od_pairs, rule=demand_rule)

    def vehicle_limit_rule(m):
        return sum(vehicle_usage_per_frequency[i] * m.f[i]
                   for i in lines) <= total_vehicle_limit

    model.vehicle_limit = pyo.Constraint(rule=vehicle_limit_rule)

    def transfer_rule(m, s):
        return 2 * m.y[s] <= sum(m.x[i] for i in station_lines[s])

    model.transfer_con = pyo.Constraint(stations, rule=transfer_rule)

    # --- Objective ---
    def obj_rule(m):
        fixed = sum(fixed_cost[i] * m.x[i] for i in lines)
        op = sum(operational_cost[i] * m.f[i] for i in lines)
        pen = sum(penalty_cost[od] * m.u[od] for od in od_pairs)
        return fixed + op + pen

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # --- Solve ---
    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}