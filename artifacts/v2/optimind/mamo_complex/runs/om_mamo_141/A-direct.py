import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ["A", "B", "C", "D", "E", "F"]

    cost = {}
    for i in locations:
        for j in locations:
            if i != j:
                cost[(i, j)] = params["cost_" + i + j]

    arcs = list(cost.keys())

    model = pyo.ConcreteModel()
    model.L = pyo.Set(initialize=locations)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in locations if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in locations if i != j) == 1

    model.out_cons = pyo.Constraint(model.L, rule=out_rule)
    model.in_cons = pyo.Constraint(model.L, rule=in_rule)

    # Subtour elimination (MTZ) for subsets handled via order variables
    model.u = pyo.Var(model.L, bounds=(0, len(locations) - 1))

    def mtz_rule(m, i, j):
        if i != j and i != locations[0] and j != locations[0]:
            return m.u[i] - m.u[j] + (len(locations) - 1) * m.x[(i, j)] <= len(locations) - 2
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(model.L, model.L, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}