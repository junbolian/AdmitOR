import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    nodes = list(range(N))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def arc_cost(i, j):
        return params[f"cost_{i}_{j}"]

    model.obj = pyo.Objective(
        expr=sum(arc_cost(i, j) * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    supply = {0: params["supply_node0"]}
    demand = {5: params["demand_node5"]}

    def balance_rule(mdl, n):
        outflow = sum(mdl.x[(n, j)] for j in nodes if j != n)
        inflow = sum(mdl.x[(i, n)] for i in nodes if i != n)
        if n in supply:
            return outflow - inflow == supply[n]
        if n in demand:
            return inflow - outflow == demand[n]
        return outflow - inflow == 0

    model.flow_balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}