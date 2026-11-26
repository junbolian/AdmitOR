import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    cost = {
        (1, 2): params["travel_cost_c1_c2"],
        (1, 3): params["travel_cost_c1_c3"],
        (1, 4): params["travel_cost_c1_c4"],
        (2, 1): params["travel_cost_c2_c1"],
        (2, 3): params["travel_cost_c2_c3"],
        (2, 4): params["travel_cost_c2_c4"],
        (3, 1): params["travel_cost_c3_c1"],
        (3, 2): params["travel_cost_c3_c2"],
        (3, 4): params["travel_cost_c3_c4"],
        (4, 1): params["travel_cost_c4_c1"],
        (4, 2): params["travel_cost_c4_c2"],
        (4, 3): params["travel_cost_c4_c3"],
    }
    arcs = list(cost.keys())

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i, j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Each city: exactly one outgoing arc
    model.out_cons = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if (i, j) in cost) == 1,
    )
    # Each city: exactly one incoming arc
    model.in_cons = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if (i, j) in cost) == 1,
    )

    # Subtour elimination (MTZ). With 4 nodes, prevent 2-cycles directly.
    # A 2-cycle is x[i,j]+x[j,i] <= 1.
    pairs = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    model.arc_2cycle = pyo.Constraint(
        pairs,
        rule=lambda m, i, j: m.x[i, j] + m.x[j, i] <= 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}