import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = [0, 1, 2, 3]
    non_depot = [1, 2, 3]

    travel_cost = {
        (0, 1): params["travel_cost_0_1"],
        (0, 2): params["travel_cost_0_2"],
        (0, 3): params["travel_cost_0_3"],
        (1, 0): params["travel_cost_1_0"],
        (1, 2): params["travel_cost_1_2"],
        (1, 3): params["travel_cost_1_3"],
        (2, 0): params["travel_cost_2_0"],
        (2, 1): params["travel_cost_2_1"],
        (2, 3): params["travel_cost_2_3"],
        (3, 0): params["travel_cost_3_0"],
        (3, 1): params["travel_cost_3_1"],
        (3, 2): params["travel_cost_3_2"],
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.Reals)

    model.u[0].fix(params["u_depot_fixed"])
    for i in non_depot:
        model.u[i].setlb(params["u_bound_lower"])
        model.u[i].setub(params["u_bound_upper"])

    def obj_rule(m):
        return sum(travel_cost[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    def subtour_rule(m, i, j):
        if i != 0 and j != 0 and i != j:
            return m.u[i] - m.u[j] + 4 * m.x[(i, j)] <= 3
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.arcs, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}