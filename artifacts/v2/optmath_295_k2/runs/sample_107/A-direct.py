import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    cities = [0, 1, 2, 3]
    non_depot = [1, 2, 3]

    # Cost data pulled from params (directed arcs between distinct cities)
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

    arcs = [(i, j) for i in cities for j in cities if i != j]

    pos_city0 = params["position_city_0"]
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.non_depot = pyo.Set(initialize=non_depot)

    # Binary routing variables
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Position (ordering) variables to eliminate subtours
    model.pos = pyo.Var(model.non_depot, domain=pyo.Reals, bounds=(pos_lb, pos_ub))

    # Objective: minimize total delivery cost
    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city: exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    # Each city: exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination: for arcs between non-depot cities,
    # pos[j] >= pos[i] + 1 if arc (i, j) is used
    def mtz_rule(m, i, j):
        return m.pos[j] >= m.pos[i] + 1 - (len(cities) + 1) * (1 - m.x[(i, j)])

    model.mtz = pyo.Constraint(
        [(i, j) for i in non_depot for j in non_depot if i != j], rule=mtz_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}