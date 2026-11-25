import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(5))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    # Binary arc variables
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Position variables
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(params["cost_%d_%d" % (i, j)] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Flow constraints: exactly one outgoing and one incoming arc per city
    def outflow_rule(model, i):
        return sum(model.x[i, j] for j in nodes if j != i) == 1

    def inflow_rule(model, j):
        return sum(model.x[i, j] for i in nodes if i != j) == 1

    model.outflow = pyo.Constraint(nodes, rule=outflow_rule)
    model.inflow = pyo.Constraint(nodes, rule=inflow_rule)

    # Position range constraints
    model.pos_lo = pyo.Constraint(nodes, rule=lambda m, i: m.u[i] >= 0)
    model.pos_hi = pyo.Constraint(nodes, rule=lambda m, i: m.u[i] <= 4)

    # Subtour elimination (MTZ-style), asymmetric: only for non-origin arcs
    non_origin_arcs = [(i, j) for (i, j) in arcs if i != 0 and j != 0]

    def mtz_rule(model, i, j):
        return model.u[i] - model.u[j] + 5 * model.x[i, j] <= 4

    model.mtz = pyo.Constraint(non_origin_arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}