import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    pos_city0 = params["position_city0"]
    pos_min = params["position_min_others"]
    pos_max = params["position_max_others"]

    n = len(cost)
    cities = list(range(n))

    model = pyo.ConcreteModel()

    # Binary arc variables x[i,j] for i != j
    model.x = pyo.Var(
        ((i, j) for i in cities for j in cities if i != j),
        domain=pyo.Binary,
    )

    # Position (order) of each city in the tour
    model.u = pyo.Var(cities, domain=pyo.Reals)

    # Objective: minimize total travel cost
    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j]
                 for i in cities for j in cities if i != j),
        sense=pyo.minimize,
    )

    # Each city has exactly one incoming arc
    model.in_arc = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1,
    )

    # Each city has exactly one outgoing arc
    model.out_arc = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if i != j) == 1,
    )

    # Position bounds
    model.pos0 = pyo.Constraint(expr=model.u[0] == pos_city0)
    model.pos_lo = pyo.Constraint(
        [1, 2, 3], rule=lambda m, i: m.u[i] >= pos_min
    )
    model.pos_hi = pyo.Constraint(
        [1, 2, 3], rule=lambda m, i: m.u[i] <= pos_max
    )

    # Subtour elimination: position must increase along used arcs (for i,j != 0)
    model.subtour = pyo.Constraint(
        ((i, j) for i in cities for j in cities if i != j and i != 0 and j != 0),
        rule=lambda m, i, j: m.u[j] >= m.u[i] + 1 - n * (1 - m.x[i, j]),
    )

    Highs().solve(model)
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {'objective': None, 'status': 'infeasible or no solution'}
    return {'objective': obj_val, 'status': 'optimal'}