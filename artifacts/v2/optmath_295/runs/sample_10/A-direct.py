import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model.cost_expr = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.supply_0 = pyo.Constraint(
        expr=sum(model.x[(0, j)] for j in nodes if j != 0)
        - sum(model.x[(i, 0)] for i in nodes if i != 0)
        == params["supply_node_0"]
    )

    model.demand_6 = pyo.Constraint(
        expr=sum(model.x[(i, 6)] for i in nodes if i != 6)
        - sum(model.x[(6, j)] for j in nodes if j != 6)
        == params["demand_node_6"]
    )

    def _balance_rule(m, k):
        outflow = sum(m.x[(k, j)] for j in nodes if j != k)
        inflow = sum(m.x[(i, k)] for i in nodes if i != k)
        return outflow - inflow == 0

    model.balance = pyo.Constraint([1, 2, 3, 4, 5], rule=_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_expr))
    return {"objective": obj_val, "status": "optimal"}