import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    position_city0 = params["position_city0"]
    position_min_others = params["position_min_others"]
    position_max_others = params["position_max_others"]

    n = len(cost)
    cities = list(range(n))

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in cities for j in cities if i != j]
    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.in_flow = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1,
    )
    model.out_flow = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1,
    )

    model.u0 = pyo.Constraint(expr=model.u[0] == position_city0)

    others = [c for c in cities if c != 0]

    def u_bounds_rule(m, c):
        return pyo.inequality(position_min_others, m.u[c], position_max_others)

    model.u_bounds = pyo.Constraint(others, rule=u_bounds_rule)

    paths = [(i, j) for i in cities for j in cities if i != 0 and j != 0 and i != j]

    def mt_rule(m, i, j):
        big_m = n
        return m.u[j] >= m.u[i] + 1 - big_m * (1 - m.x[i, j])

    model.mtz = pyo.Constraint(paths, rule=mt_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}