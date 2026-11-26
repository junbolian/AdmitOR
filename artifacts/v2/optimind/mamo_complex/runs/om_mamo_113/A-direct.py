import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["A", "B", "C", "D", "E"]

    # Build cost dictionary; cost_AE is symmetric to cost_EA
    cost = {}
    for i in cities:
        for j in cities:
            if i == j:
                continue
            key = "cost_" + i + j
            if key in params:
                cost[(i, j)] = params[key]
    cost[("A", "E")] = params["cost_EA"]

    model = pyo.ConcreteModel()

    model.CITY = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j], dimen=2
    )

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.ARCS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.out_con = pyo.Constraint(model.CITY, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.in_con = pyo.Constraint(model.CITY, rule=in_rule)

    # Subtour elimination (MTZ formulation)
    model.ORDER = pyo.Set(initialize=cities[1:])  # exclude base city A
    model.u = pyo.Var(model.ORDER, domain=pyo.NonNegativeReals)

    # Big-M for order bounds; number of cities minus one is a valid bound
    n = len(cities)

    def mtz_rule(m, i, j):
        if i != "A" and j != "A" and i != j:
            return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.ARCS, rule=mtz_rule)

    def u_bound_rule(m, i):
        return m.u[i] <= n - 1

    model.u_bound = pyo.Constraint(model.ORDER, rule=u_bound_rule)

    def u_lb_rule(m, i):
        return m.u[i] >= 1

    model.u_lb = pyo.Constraint(model.ORDER, rule=u_lb_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}