import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_cities"])
    cities = list(range(n))
    city_pairs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(city_pairs, domain=pyo.Binary)

    # MTZ position variables for all cities
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    # Fixed position of City 0
    model.pos0 = pyo.Constraint(expr=model.u[0] == params["position_city_0"])

    # Bounds on positions of Cities 1..n-1
    def pos_bounds_rule(mdl, i):
        if i == 0:
            return pyo.Constraint.Skip
        return pyo.inequality(
            params["position_lower_bound"],
            mdl.u[i],
            params["position_upper_bound"],
        )

    model.pos_bounds = pyo.Constraint(cities, rule=pos_bounds_rule)

    # Objective: minimize travel cost
    cost_map = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost_map[(i, j)] = params["cost_%d_%d" % (i, j)]

    model.obj = pyo.Objective(
        expr=sum(cost_map[(i, j)] * model.x[(i, j)] for (i, j) in city_pairs),
        sense=pyo.minimize,
    )

    # Each city: exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    # Each city: exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1

    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination for i, j != 0
    mtz_pairs = [(i, j) for (i, j) in city_pairs if i != 0 and j != 0]

    def mtz_rule(mdl, i, j):
        return (
            params["mtz_big_M"] * mdl.x[(i, j)]
            + mdl.u[i]
            - mdl.u[j]
            <= params["mtz_rhs"]
        )

    model.mtz = pyo.Constraint(mtz_pairs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}