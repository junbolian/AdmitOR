import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    net_outflow_node_0 = params["net_outflow_node_0"]
    net_inflow_node_7 = params["net_inflow_node_7"]

    N = 8
    arcs = [(i, j) for i in range(N) for j in range(N) if i != j]
    arc_index = {a: k for k, a in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def arc_cost(a):
        return cost[arc_index[a]]

    model.obj = pyo.Objective(
        expr=sum(arc_cost((i, j)) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def outflow(i):
        return sum(model.x[i, j] for j in range(N) if i != j)

    def inflow(i):
        return sum(model.x[j, i] for j in range(N) if i != j)

    model.flow_0 = pyo.Constraint(expr=outflow(0) - inflow(0) == net_outflow_node_0)
    model.flow_7 = pyo.Constraint(expr=inflow(7) - outflow(7) == net_inflow_node_7)

    model.bal = pyo.Constraint(
        range(1, 7), rule=lambda m, i: inflow(i) - outflow(i) == 0
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}