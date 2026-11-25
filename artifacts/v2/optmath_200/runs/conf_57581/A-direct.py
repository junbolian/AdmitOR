import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    selection_cost = params["selection_cost"]
    coverage_requirement = params["coverage_requirement"]

    n_locations = 12
    locations = list(range(1, n_locations + 1))

    coverage_sets = [
        [2, 6, 8, 10, 11, 12],
        [7, 9, 11, 12],
        [2, 5, 7, 9, 10, 12],
        [1, 2, 3, 5, 6, 10, 11, 12],
        [4, 7, 10, 11, 12],
        [1, 2, 3, 4],
        [1, 2, 3, 6, 7, 8],
        [1, 3, 5, 7, 12],
        [4, 5, 8, 9, 10],
        [5, 6, 10],
        [2, 5, 9, 12],
        [2, 3, 4, 5, 8],
        [2, 3, 6, 7],
        [7, 8],
        [2, 6, 7, 9],
        [1, 3, 6, 8, 12],
        [3, 4, 5, 6, 12],
        [4, 7, 8, 11],
        [3, 4, 6, 7, 10],
        [1, 3, 6, 8],
        [1, 3, 4, 7, 9, 10],
    ]

    coverage_requirements = list(coverage_requirement)
    n_constraints = len(coverage_sets)

    model = pyo.ConcreteModel()

    model.LOC = pyo.Set(initialize=locations)
    model.CON = pyo.Set(initialize=list(range(n_constraints)))

    model.select = pyo.Var(model.LOC, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(selection_cost[i - 1] * model.select[i] for i in model.LOC),
        sense=pyo.minimize,
    )

    def coverage_rule(m, j):
        return sum(m.select[i] for i in coverage_sets[j]) >= coverage_requirements[j]

    model.coverage = pyo.Constraint(model.CON, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}