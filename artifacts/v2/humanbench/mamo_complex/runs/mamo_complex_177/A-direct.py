import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    n = 7
    source = 0
    sink = 6

    arcs = [(i, j) for i in range(n) for j in range(n)
            if i != j and capacities[i][j] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.flow[i, j] for (i, j) in m.arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= capacities[i][j]
    model.cap_constraint = pyo.Constraint(model.arcs, rule=cap_rule)

    nodes = [v for v in range(n) if v != source and v != sink]

    def balance_rule(m, v):
        inflow = sum(m.flow[i, v] for (i, j) in m.arcs if j == v)
        outflow = sum(m.flow[v, j] for (i, j) in m.arcs if i == v)
        return inflow == outflow
    model.balance_constraint = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}