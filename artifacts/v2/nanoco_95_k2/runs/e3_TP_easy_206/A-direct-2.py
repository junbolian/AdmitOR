import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_nodes = [0, 1, 2]
    demand_nodes = [3, 4, 5, 6]
    arcs = [(i, j) for i in supply_nodes for j in demand_nodes]

    supply = {i: params["supply_%d" % i] for i in supply_nodes}
    demand = {j: params["demand_%d" % j] for j in demand_nodes}
    cap = {(i, j): params["cap_%d_%d" % (i, j)] for (i, j) in arcs}
    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.supply_nodes = pyo.Set(initialize=supply_nodes)
    model.demand_nodes = pyo.Set(initialize=demand_nodes)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.flow[i, j] for j in demand_nodes) == supply[i]
    model.supply_con = pyo.Constraint(model.supply_nodes, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in supply_nodes) == demand[j]
    model.demand_con = pyo.Constraint(model.demand_nodes, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}