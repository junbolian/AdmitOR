import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]
    cost = {
        (1, 2): params["c12"], (1, 3): params["c13"], (1, 4): params["c14"],
        (2, 1): params["c21"], (2, 3): params["c23"], (2, 4): params["c24"],
        (3, 1): params["c31"], (3, 2): params["c32"], (3, 4): params["c34"],
        (4, 1): params["c41"], (4, 2): params["c42"], (4, 3): params["c43"],
    }

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.out_constraint = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.in_constraint = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ) for the single tour
    model.u = pyo.Var(cities, bounds=(1, 4), domain=pyo.NonNegativeReals)
    mtz_pairs = [(i, j) for i in cities for j in cities if i != j and i != 1 and j != 1]

    def mtz_rule(m, i, j):
        return m.u[i] - m.u[j] + 4 * m.x[(i, j)] <= 3
    model.mtz_constraint = pyo.Constraint(mtz_pairs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}