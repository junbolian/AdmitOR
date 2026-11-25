import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    n = params["num_cities"]
    cities = list(range(n))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    # Binary decision variables: 1 if route from i to j is used
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Position variables for each city
    model.u = pyo.Var(cities, domain=pyo.Reals)
    model.u[0].fix(params["position_city_0"])
    for i in cities:
        if i != 0:
            model.u[i].setlb(params["position_lower_bound"])
            model.u[i].setub(params["position_upper_bound"])

    # Objective: minimize total delivery cost
    def objective_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc (depart exactly once)
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc (arrive exactly once)
    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ) for pairs excluding City 0
    arcs_excl0 = [(i, j) for (i, j) in arcs if i != 0 and j != 0]

    def mtz_rule(m, i, j):
        return m.u[j] >= m.u[i] + 1 - n * (1 - m.x[(i, j)])

    model.subtour = pyo.Constraint(arcs_excl0, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}