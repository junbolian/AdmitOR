import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]
    net_outflow = params["net_outflow"]

    arcs = [
        (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 3),
        (3, 0), (3, 1), (3, 2),
    ]
    nodes = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.y = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def flow_rule(model, i, j):
        return model.x[(i, j)] <= capacity[arcs.index((i, j))] * model.y[(i, j)]

    model.flow_link = pyo.Constraint(model.ARCS, rule=flow_rule)

    def balance_rule(model, k):
        inflow = sum(model.x[(i, j)] for (i, j) in arcs if j == k)
        outflow = sum(model.x[(i, j)] for (i, j) in arcs if i == k)
        return outflow - inflow == net_outflow[k]

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(model):
        return sum(
            fixed_cost[idx] * model.y[arc] + variable_cost[idx] * model.x[arc]
            for idx, arc in enumerate(arcs)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}