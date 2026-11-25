import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    exact_assignments = params["exact_assignments"]
    noe_parameters = params["noe_parameters"]

    num_peaks = len(cost_matrix)
    num_aa = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.PEAKS = pyo.RangeSet(0, num_peaks - 1)
    model.AA = pyo.RangeSet(0, num_aa - 1)

    model.x = pyo.Var(model.PEAKS, model.AA, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[p][a] * model.x[p, a]
                 for p in model.PEAKS for a in model.AA),
        sense=pyo.minimize,
    )

    model.peak_limit = pyo.Constraint(
        model.PEAKS,
        rule=lambda mm, p: sum(mm.x[p, a] for a in mm.AA) <= 1,
    )

    model.aa_limit = pyo.Constraint(
        model.AA,
        rule=lambda mm, a: sum(mm.x[p, a] for p in mm.PEAKS) <= 1,
    )

    model.total_assign = pyo.Constraint(
        expr=sum(model.x[p, a] for p in model.PEAKS for a in model.AA)
        == exact_assignments
    )

    noe_active = [key for key, val in noe_parameters.items() if val == 1]

    if noe_active:
        model.NOE_INDEX = pyo.Set(initialize=noe_active, dimen=4)
        model.noe_con = pyo.Constraint(
            model.NOE_INDEX,
            rule=lambda mm, p1, a1, p2, a2: mm.x[p1, a1] + mm.x[p2, a2] <= 1,
        )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}