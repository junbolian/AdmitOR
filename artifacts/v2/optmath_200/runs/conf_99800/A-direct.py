import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    num_peaks = len(cost_matrix)
    num_aas = len(cost_matrix[0])
    peaks = list(range(num_peaks))
    aas = list(range(num_aas))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, aas, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for i in peaks for j in aas),
        sense=pyo.minimize,
    )

    model.peak_constraints = pyo.Constraint(
        peaks, rule=lambda m, i: sum(m.x[i, j] for j in aas) <= 1
    )
    model.aa_constraints = pyo.Constraint(
        aas, rule=lambda m, j: sum(m.x[i, j] for i in peaks) <= 1
    )
    model.total_assignments = pyo.Constraint(
        expr=sum(model.x[i, j] for i in peaks for j in aas) == 2
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}