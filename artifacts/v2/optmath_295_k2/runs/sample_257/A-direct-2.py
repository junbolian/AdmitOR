import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, within=pyo.Binary)

    cost = {(i, j): params["c_%d_%d" % (i, j)] for (i, j) in arcs}
    supply_node0 = params["supply_node0"]
    demand_node7 = params["demand_node7"]

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def flow_balance_rule(mdl, k):
        inflow = sum(mdl.x[(i, k)] for i in nodes if i != k)
        outflow = sum(mdl.x[(k, j)] for j in nodes if j != k)
        if k == 0:
            return outflow - inflow == supply_node0
        elif k == 7:
            return inflow - outflow == demand_node7
        else:
            return inflow - outflow == 0

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}