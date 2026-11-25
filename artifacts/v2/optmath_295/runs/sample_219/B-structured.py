# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4],"F":[[1,1,3,0],[1,2,3,0]]},"params":{"costs":"params['costs']: 4x5 assignment-cost matrix","total_assignments":"params['total_assignments']: exact assignment count"},"variables":{"x[i,j]":"binary for i in I, j in J"},"constraints":["For each j in J: sum_i x[i,j] <= 1","For each i in I: sum_j x[i,j] <= 1","sum_i,j x[i,j] == total_assignments","For each (i,j,k,l) in F: x[i,j] + x[k,l] <= 1"],"objective":"minimize sum_i,j costs[i][j]*x[i,j]","assumption":"With no distances or threshold supplied, treat the two illustrated NOE pairs as incompatible; additional spatial exclusions cannot be inferred."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    total_assignments = params["total_assignments"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, 3)
    model.amino_acids = pyo.RangeSet(0, 4)

    # Structural pairs implement the NOE interpretation stated in the IR.
    model.noe_conflict_pairs = pyo.Set(
        dimen=4,
        initialize=[(1, 1, 3, 0), (1, 2, 3, 0)],
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize=lambda mdl, i, j: costs[i][j],
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=total_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def amino_acid_capacity_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.peaks) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_capacity_rule,
    )

    def peak_capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.amino_acids) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks,
        rule=peak_capacity_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ) == model.required_assignments
    )

    def noe_compatibility_rule(mdl, i, j, k, ell):
        return mdl.x[i, j] + mdl.x[k, ell] <= 1

    model.noe_compatibility = pyo.Constraint(
        model.noe_conflict_pairs,
        rule=noe_compatibility_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}