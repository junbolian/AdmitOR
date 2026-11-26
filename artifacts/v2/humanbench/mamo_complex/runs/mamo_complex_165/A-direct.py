import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]
    source = 0
    sink = 5

    cap = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["capacity_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def cap_rule(m, i, j):
        return (0, cap[(i, j)])

    model.flow = pyo.Var(model.arcs, bounds=cap_rule)

    # Flow conservation: intermediate nodes have net flow zero
    def balance_rule(m, v):
        if v == source or v == sink:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, v] for i in cities if i != v)
        outflow = sum(m.flow[v, j] for j in cities if j != v)
        return inflow == outflow

    model.balance = pyo.Constraint(cities, rule=balance_rule)

    # Objective: total flow leaving the source
    def obj_rule(m):
        return sum(m.flow[source, j] for j in cities if j != source)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}