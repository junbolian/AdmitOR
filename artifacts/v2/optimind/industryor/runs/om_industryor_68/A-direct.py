import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance = {
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 1): params["distance_21"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 1): params["distance_31"],
        (3, 2): params["distance_32"],
        (3, 4): params["distance_34"],
        (4, 1): params["distance_41"],
        (4, 2): params["distance_42"],
        (4, 3): params["distance_43"],
    }

    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.CITIES = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(model.CITIES, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(distance[(i, j)] * mdl.x[i, j] for (i, j) in arcs)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.out_degree = pyo.Constraint(model.CITIES, rule=out_rule)
    model.in_degree = pyo.Constraint(model.CITIES, rule=in_rule)

    # Subtour elimination (MTZ) for cities 2..n
    non_root = [c for c in cities if c != cities[0]]
    n = len(cities)

    def mtz_rule(mdl, i, j):
        if i == j or i == cities[0] or j == cities[0]:
            return pyo.Constraint.Skip
        return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2

    model.mtz = pyo.Constraint(model.CITIES, model.CITIES, rule=mtz_rule)

    def u_bounds_rule(mdl, i):
        return pyo.inequality(1, mdl.u[i], n - 1)

    model.u_bounds = pyo.Constraint(non_root, rule=u_bounds_rule)

    try:
        Highs().solve(model)
    except Exception:
        return {"objective": None, "status": "solver_failed"}

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}