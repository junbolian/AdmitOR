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

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.pos = pyo.Var(cities)

    # Bounds on position variables (City 0 unrestricted)
    model.pos[1].setlb(params["pos1_lower"])
    model.pos[1].setub(params["pos1_upper"])
    model.pos[2].setlb(params["pos2_lower"])
    model.pos[2].setub(params["pos2_upper"])

    # Objective
    model.total_cost = pyo.Expression(
        expr=sum(cost[a] * model.x[a] for a in arcs)
    )
    model.obj = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)

    # Each city visited exactly once (in-degree)
    model.visit = pyo.ConstraintList()
    for j in cities:
        model.visit.add(
            sum(model.x[(i, j)] for i in cities if i != j) == 1
        )

    # Each city departed exactly once (out-degree)
    model.depart = pyo.ConstraintList()
    for i in cities:
        model.depart.add(
            sum(model.x[(i, j)] for j in cities if j != i) == 1
        )

    # Subtour elimination (MTZ-style for the two non-depot arcs)
    big_m = params["pos1_upper"] - params["pos2_lower"] + 3
    model.subtour_12 = pyo.Constraint(
        expr=model.pos[1] - model.pos[2] + big_m * model.x[(1, 2)] <= big_m - 1
    )
    model.subtour_21 = pyo.Constraint(
        expr=model.pos[2] - model.pos[1] + big_m * model.x[(2, 1)] <= big_m - 1
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}