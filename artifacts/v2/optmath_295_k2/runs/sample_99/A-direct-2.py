import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    arcs = [
        (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 3),
        (3, 0), (3, 1), (3, 2),
    ]
    nodes = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=nodes)

    model.arc_index = pyo.Set(initialize=range(len(arcs)))
    arc_to_idx = {a: i for i, a in enumerate(arcs)}

    model.flow = pyo.Var(model.arc_set, bounds=lambda m, i, j: (0, capacity[arc_to_idx[(i, j)]]))
    model.open_arc = pyo.Var(model.arc_set, domain=pyo.Binary)

    def flow_cap_rule(m, i, j):
        idx = arc_to_idx[(i, j)]
        return m.flow[i, j] <= capacity[idx] * m.open_arc[i, j]
    model.flow_cap_con = pyo.Constraint(model.arc_set, rule=flow_cap_rule)

    def balance_rule(m, n):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == n)
        return inflow - outflow == net_demand[n]
    model.balance_con = pyo.Constraint(model.node_set, rule=balance_rule)

    def obj_rule(m):
        return sum(
            fixed_cost[arc_to_idx[(i, j)]] * m.open_arc[i, j]
            + variable_cost[arc_to_idx[(i, j)]] * m.flow[i, j]
            for (i, j) in arcs
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}