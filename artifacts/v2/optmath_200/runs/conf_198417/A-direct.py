import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = [0, 1, 2]
    arcs = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }

    # Decision variables: binary arc selection
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Auxiliary position variables for City 1 and City 2, bounded [0, 2]
    model.u = pyo.Var([1, 2], domain=pyo.NonNegativeReals, bounds=(0, 2))

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(cost[a] * m.x[a] for a in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city visited exactly once: exactly one outgoing and one incoming arc
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_constraint = pyo.Constraint(cities, rule=out_rule)
    model.in_constraint = pyo.Constraint(cities, rule=in_rule)

    # Big-M for the two relevant arcs (sufficiently large)
    big_m = 3

    # Subtour elimination for arc (1, 2): if used, u1 < u2 => u1 - u2 <= -1
    def sec_1_2(m):
        return m.u[1] - m.u[2] <= -1 + big_m * (1 - m.x[(1, 2)])

    # Subtour elimination for arc (2, 1): if used, u2 < u1 => u2 - u1 <= -1
    def sec_2_1(m):
        return m.u[2] - m.u[1] <= -1 + big_m * (1 - m.x[(2, 1)])

    model.subtour_1_2 = pyo.Constraint(rule=sec_1_2)
    model.subtour_2_1 = pyo.Constraint(rule=sec_2_1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}