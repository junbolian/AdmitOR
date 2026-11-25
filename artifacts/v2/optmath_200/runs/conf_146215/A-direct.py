import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_costs = params["activation_costs"]
    coverage_matrix = params["coverage_matrix"]

    # Structural constants
    n_teams = 18
    n_areas = 34
    teams = list(range(1, n_teams + 1))
    areas = list(range(1, n_areas + 1))

    model = pyo.ConcreteModel()

    # Decision variables: x[j] = 1 if team j is activated
    model.x = pyo.Var(teams, domain=pyo.Binary)

    # Objective: minimize total activation cost
    model.total_cost = pyo.Objective(
        expr=sum(activation_costs[j - 1] * model.x[j] for j in teams),
        sense=pyo.minimize,
    )

    # Constraints: each area must be covered by at least one activated team
    def coverage_rule(mdl, i):
        return sum(coverage_matrix[i - 1][j - 1] * mdl.x[j] for j in teams) >= 1

    model.coverage = pyo.Constraint(areas, rule=coverage_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}