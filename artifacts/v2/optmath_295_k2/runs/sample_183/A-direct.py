import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = params["num_cities"]
    dist = params["distance_matrix"]
    lb = params["position_lower_bound"]
    ub = params["position_upper_bound"]
    start = params["start_city"]

    cities = list(range(N))

    model = pyo.ConcreteModel()

    # Binary arc variables: x[i,j] = 1 if traveling directly from i to j
    model.x = pyo.Var(cities, cities, domain=pyo.Binary)

    # Continuous position variables (MTZ-style subtour elimination)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    # Objective: minimize total distance traveled
    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for i in cities for j in cities if i != j),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing arc
    model.out_arc = pyo.Constraint(
        cities,
        rule=lambda model, i: sum(model.x[i, j] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_arc = pyo.Constraint(
        cities,
        rule=lambda model, j: sum(model.x[i, j] for i in cities if i != j) == 1,
    )

    # No self-loops
    model.no_self = pyo.Constraint(
        cities,
        rule=lambda model, i: model.x[i, i] == 0,
    )

    # Position bounds
    model.pos_lb = pyo.Constraint(
        cities,
        rule=lambda model, i: model.u[i] >= lb,
    )
    model.pos_ub = pyo.Constraint(
        cities,
        rule=lambda model, i: model.u[i] <= ub,
    )

    # Fix start city position
    model.start_pos = pyo.Constraint(
        expr=model.u[start] == lb,
    )

    # MTZ subtour elimination for non-start nodes.
    # Use (ub - lb + 1) as the big-M so bounds stay consistent with the
    # [lb, ub] position range (a tour has N-1 = ub-lb arcs from start onward).
    others = [i for i in cities if i != start]
    big_m = (ub - lb) + 1

    def mtz_rule(model, i, j):
        return model.u[i] + 1 <= model.u[j] + big_m * (1 - model.x[i, j])

    model.mtz = pyo.Constraint(
        [(i, j) for i in others for j in cities if j != i],
        rule=mtz_rule,
    )

    # Solve with HiGHS
    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}