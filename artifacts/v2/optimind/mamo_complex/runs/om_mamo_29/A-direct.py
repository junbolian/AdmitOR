import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    stations = list(range(9))
    arcs = [(i, j) for i in stations for j in stations if i != j]
    source = 0
    sink = 8

    model = pyo.ConcreteModel()

    model.flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def cap_rule(model, i, j):
        return model.flow[(i, j)] <= params["capacity_%d_to_%d" % (i, j)]

    model.cap_con = pyo.Constraint(arcs, rule=cap_rule)

    # Flow conservation: net outflow = 0 at all internal nodes
    def balance_rule(model, k):
        outflow = sum(model.flow[(k, j)] for j in stations if j != k)
        inflow = sum(model.flow[(i, k)] for i in stations if i != k)
        if k == source:
            return inflow - outflow == 0
        elif k == sink:
            return outflow - inflow == 0
        else:
            return inflow - outflow == 0

    model.balance_con = pyo.Constraint(stations, rule=balance_rule)

    # Objective: maximize net flow into sink
    def obj_rule(model):
        return sum(model.flow[(i, sink)] for i in stations if i != sink)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}