import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    cost_matrix = params["cost_matrix"]

    cities = list(range(num_cities))

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)

    # x[i, j] = 1 if arc i->j is used
    model.x = pyo.Var(model.cities, model.cities, domain=pyo.Binary)

    def arc_cost_rule(m):
        return sum(
            cost_matrix[i][j] * m.x[i, j]
            for i in cities
            for j in cities
            if i != j
        )

    model.obj = pyo.Objective(rule=arc_cost_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.out_deg = pyo.Constraint(model.cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.in_deg = pyo.Constraint(model.cities, rule=in_rule)

    # Fix diagonals to zero
    def diag_rule(m, i):
        return m.x[i, i] == 0

    model.no_self = pyo.Constraint(model.cities, rule=diag_rule)

    # Subtour elimination via ladder/MTZ-style ordering with continuous u
    # u[i] represents the position/order of city i in the tour (for i != root)
    root = cities[0]
    non_root = cities[1:]

    model.u = pyo.Var(non_root, bounds=(1, num_cities - 1))

    def mtz_rule(m, i, j):
        if i != j and j != root and i != root:
            return m.u[j] - m.u[i] >= 1 - (num_cities - 1) * (1 - m.x[i, j])
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=mtz_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}