import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n_peaks = len(cost)
    n_aa = len(cost[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_peaks - 1)
    model.A = pyo.RangeSet(0, n_aa - 1)

    def cost_rule(mdl, i, j):
        return cost[i][j]

    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.P for j in model.A),
        sense=pyo.minimize,
    )

    # Each peak assigned to at most one amino acid
    def peak_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.A) <= 1

    model.peak_con = pyo.Constraint(model.P, rule=peak_rule)

    # Each amino acid assigned to at most one peak
    def aa_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.P) <= 1

    model.aa_con = pyo.Constraint(model.A, rule=aa_rule)

    # Exactly 3 assignments
    model.total_con = pyo.Constraint(
        expr=sum(model.x[i, j] for i in model.P for j in model.A) == 3
    )

    # Conflict constraints
    model.conflict1 = pyo.Constraint(
        expr=model.x[0, 1] + model.x[2, 4] <= 1
    )
    model.conflict2 = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 4] <= 1
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}