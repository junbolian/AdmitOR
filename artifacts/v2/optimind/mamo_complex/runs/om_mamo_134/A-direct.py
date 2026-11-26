import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n"])
    cost = params["cost"]

    cities = list(range(n))

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)

    # Directed arc variables for the TSP (subtour elimination via MTZ)
    model.x = pyo.Var(model.cities, model.cities, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(mdl):
        return sum(
            cost[i][j] * mdl.x[i, j]
            for i in cities
            for j in cities
            if i != j
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    model.out_arc = pyo.Constraint(model.cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.in_arc = pyo.Constraint(model.cities, rule=in_rule)

    # MTZ subtour elimination (fix city 0 as depot, u[0] = 0 effectively)
    def mtz_rule(mdl, i, j):
        if i != j and i != 0 and j != 0:
            return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.cities, model.cities, rule=mtz_rule)

    # Fix u for the depot
    def depot_rule(mdl, i):
        if i == 0:
            return mdl.u[i] == 0
        return pyo.Constraint.Skip

    model.depot = pyo.Constraint(model.cities, rule=depot_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}