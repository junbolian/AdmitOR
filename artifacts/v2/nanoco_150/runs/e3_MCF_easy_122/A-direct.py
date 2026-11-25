import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 2, "capacity_0_2", "cost_0_2"),
        (0, 3, "capacity_0_3", "cost_0_3"),
        (1, 2, "capacity_1_2", "cost_1_2"),
        (1, 3, "capacity_1_3", "cost_1_3"),
        (2, 4, "capacity_2_4", "cost_2_4"),
        (2, 5, "capacity_2_5", "cost_2_5"),
        (3, 4, "capacity_3_4", "cost_3_4"),
        (3, 5, "capacity_3_5", "cost_3_5"),
        (0, 4, "capacity_0_4", "cost_0_4"),
        (0, 5, "capacity_0_5", "cost_0_5"),
        (1, 4, "capacity_1_4", "cost_1_4"),
        (1, 5, "capacity_1_5", "cost_1_5"),
    ]

    nodes = list(range(6))
    supplies = [
        params["supply_0"],
        params["supply_1"],
        params["supply_2"],
        params["supply_3"],
        params["supply_4"],
        params["supply_5"],
    ]

    model = pyo.ConcreteModel()

    model.arc_index = pyo.Set(initialize=[(i, j) for i, j, _, _ in arcs])
    model.node_index = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arc_index, domain=pyo.NonNegativeReals)

    def cap_rule(model, i, j):
        cap_name = None
        for a, b, capn, _ in arcs:
            if a == i and b == j:
                cap_name = capn
                break
        return model.flow[i, j] <= params[cap_name]

    model.capacity_constraint = pyo.Constraint(model.arc_index, rule=cap_rule)

    def balance_rule(model, k):
        outflow = sum(model.flow[k, j] for (i, j) in model.arc_index if i == k)
        inflow = sum(model.flow[i, k] for (i, j) in model.arc_index if j == k)
        return outflow - inflow == supplies[k]

    model.balance_constraint = pyo.Constraint(model.node_index, rule=balance_rule)

    def cost_rule(model):
        total = 0
        for i, j, _, costn in arcs:
            total += params[costn] * model.flow[i, j]
        return total

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}