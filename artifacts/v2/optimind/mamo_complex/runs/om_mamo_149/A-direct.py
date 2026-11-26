import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    cost = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[a] * model.x[a] for a in arcs), sense=pyo.minimize
    )

    # Each city entered exactly once
    model.in_flow = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1
    )
    # Each city left exactly once
    model.out_flow = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1
    )

    # Subtour elimination (MTZ)
    model.u = pyo.Var(cities, bounds=(1, len(cities) - 1))
    model.u[1].fix(1)

    def sec_rule(m, i, j):
        if i == j or i == 1 or j == 1:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + len(cities) * m.x[i, j] <= len(cities) - 1

    model.sec = pyo.Constraint(arcs, rule=sec_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}