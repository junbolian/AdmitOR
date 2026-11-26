import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_cities"])

    cost_raw = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }

    cost = {}
    for (i, j), c in cost_raw.items():
        cost[(i, j)] = c
        cost[(j, i)] = c

    cities = list(range(1, n + 1))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(md):
        return sum(cost[(i, j)] * md.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(md, i):
        return sum(md.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(md, j):
        return sum(md.x[(i, j)] for i in cities if i != j) == 1

    model.out_deg = pyo.Constraint(model.cities, rule=out_rule)
    model.in_deg = pyo.Constraint(model.cities, rule=in_rule)

    def subtour_rule(md, i, j):
        if i != j and i != 1 and j != 1:
            return md.u[i] - md.u[j] + (n - 1) * md.x[(i, j)] <= n - 2
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.cities, model.cities, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}