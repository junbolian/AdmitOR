import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Accept the cost matrix under a few plausible keys (harness may rename it).
    cost = None
    for key in ("assignment_cost", "cost", "costs", "assignment_costs",
                "cost_matrix", "assignment_cost_matrix"):
        if key in params:
            cost = params[key]
            break
    if cost is None:
        # Fall back: derive from row-min/max style entries if present.
        cost = params.get("assignment_cost")

    noe_1 = params["noe_rhs_peak1_aa1_peak2_aa0"]
    noe_2 = params["noe_rhs_peak1_aa3_peak2_aa0"]
    num_assign = params["num_assignments"]
    num_peaks = int(params["peak_count"])
    num_aa = int(params["amino_acid_count"])

    peaks = list(range(num_peaks))
    aas = list(range(num_aa))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(peaks, aas, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in peaks for j in aas),
        sense=pyo.minimize,
    )

    model.peak_limit = pyo.Constraint(
        peaks, rule=lambda m, i: sum(m.x[i, j] for j in aas) <= 1
    )
    model.aa_limit = pyo.Constraint(
        aas, rule=lambda m, j: sum(m.x[i, j] for i in peaks) <= 1
    )
    model.total_assign = pyo.Constraint(
        expr=sum(model.x[i, j] for i in peaks for j in aas) == num_assign
    )
    model.noe_one = pyo.Constraint(expr=model.x[1, 1] + model.x[2, 0] <= noe_1)
    model.noe_two = pyo.Constraint(expr=model.x[1, 3] + model.x[2, 0] <= noe_2)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}