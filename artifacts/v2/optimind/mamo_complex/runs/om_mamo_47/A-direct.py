import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(a, b) for a in cities for b in cities if a != b]

    model = pyo.ConcreteModel()

    model.flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(model, a, b):
        return model.flow[(a, b)] <= params["cap_%d_%d" % (a, b)]

    model.cap_con = pyo.Constraint(arcs, rule=cap_rule)

    # Flow conservation at each internal city (1, 2, 3, 4)
    internal = [1, 2, 3, 4]

    def conserve_rule(model, k):
        inflow = sum(model.flow[(i, k)] for i in cities if i != k)
        outflow = sum(model.flow[(k, j)] for j in cities if j != k)
        return inflow - outflow == 0

    model.conserve = pyo.Constraint(internal, rule=conserve_rule)

    # Objective: maximize net flow into City 5 (destination)
    model.obj = pyo.Objective(
        expr=sum(model.flow[(i, 5)] for i in cities if i != 5)
        - sum(model.flow[(5, j)] for j in cities if j != 5),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}