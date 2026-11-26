import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4]
    edges = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i, j in edges:
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.cost = pyo.Param(model.edges, initialize=cost)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, 3))

    def obj_rule(mdl):
        return sum(mdl.cost[i, j] * mdl.x[i, j] for i, j in mdl.edges)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.cities if j != i) == 1
    model.out_cons = pyo.Constraint(model.cities, rule=out_rule)

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.cities if i != j) == 1
    model.in_cons = pyo.Constraint(model.cities, rule=in_rule)

    # Subtour elimination (MTZ), u[1] fixed as depot
    def mtz_rule(mdl, i, j):
        if i == j or i == 1 or j == 1:
            return pyo.Constraint.Skip
        return mdl.u[i] - mdl.u[j] + 4 * mdl.x[i, j] <= 3
    model.mtz_cons = pyo.Constraint(model.edges, rule=mtz_rule)

    model.u0_fix = pyo.Constraint(expr=model.u[1] == 0)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible_or_unbounded"}

    return {"objective": obj_val, "status": "optimal"}