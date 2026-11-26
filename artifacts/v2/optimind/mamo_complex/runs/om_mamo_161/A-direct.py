import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.CITIES = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.dep_arc = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(model.CITIES, domain=pyo.NonNegativeReals, bounds=(0, 4))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.dep_arc[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.dep_arc[i, j] for j in cities if j != i) == 1

    model.out_cons = pyo.Constraint(model.CITIES, rule=out_rule)

    def in_rule(m, j):
        return sum(m.dep_arc[i, j] for i in cities if i != j) == 1

    model.in_cons = pyo.Constraint(model.CITIES, rule=in_rule)

    # Subtour elimination (MTZ); start city is fixed to 1
    non_start = [i for i in cities if i != 1]
    model.SUB = pyo.Set(initialize=non_start)

    def mtz_rule(m, i, k):
        return m.u[i] - m.u[k] + 4 * m.dep_arc[i, k] <= 3

    model.mtz_cons = pyo.Constraint(model.SUB, model.SUB, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}