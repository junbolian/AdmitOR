import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n_analysts = len(cost_matrix)
    n_incidents = len(cost_matrix[0])

    analysts = list(range(n_analysts))
    incidents = list(range(n_incidents))
    pairs = [(i, j) for i in analysts for j in incidents]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    model.analyst_constraints = pyo.Constraint(
        analysts,
        rule=lambda m, i: sum(m.x[i, j] for j in incidents) == 1,
    )
    model.incident_constraints = pyo.Constraint(
        incidents,
        rule=lambda m, j: sum(m.x[i, j] for i in analysts) == 1,
    )
    model.bottleneck_constraints = pyo.Constraint(
        pairs,
        rule=lambda m, i, j: cost_matrix[i][j] * m.x[i, j] <= m.z,
    )

    model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}