import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_nodes"])
    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    fixed = {(i, j): params[f"fixed_cost_{i}_{j}"] for (i, j) in arcs}
    var = {(i, j): params[f"variable_cost_{i}_{j}"] for (i, j) in arcs}
    cap = {(i, j): params[f"capacity_{i}_{j}"] for (i, j) in arcs}
    net_out = {i: params[f"net_outflow_node{i}"] for i in nodes}

    model = pyo.ConcreteModel()
    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=nodes)

    model.y = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.x = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(fixed[a] * model.y[a] for a in arcs)
        + sum(var[a] * model.x[a] for a in arcs),
        sense=pyo.minimize,
    )

    model.cap_link = pyo.Constraint(
        model.arc_set,
        rule=lambda model, i, j: model.x[i, j] <= cap[(i, j)] * model.y[i, j],
    )

    def balance_rule(model, k):
        outflow = sum(model.x[k, j] for j in nodes if j != k)
        inflow = sum(model.x[i, k] for i in nodes if i != k)
        return outflow - inflow == net_out[k]

    model.balance = pyo.Constraint(model.node_set, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}