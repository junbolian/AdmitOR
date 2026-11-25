# IR: {"sets":{"P":[0,1,2,3,4],"A":[0,1,2,3,4,5],"NOE":[[0,4,0,1],[0,4,0,3],[0,4,0,4],[1,2,0,1],[1,2,0,3],[1,2,0,4]]},"params":{"assignment_cost":"5x6 numeric matrix from params","required_assignments":"exact assignment count from params"},"variables":{"x[P,A]":"binary"},"constraints":["forall i in P: sum(j in A,x[i,j]) <= 1","forall j in A: sum(i in P,x[i,j]) <= 1","sum(i in P,j in A,x[i,j]) == required_assignments","forall (i,k,j,l) in NOE: x[i,j] + x[k,l] <= 1"],"objective":"minimize sum(i in P,j in A,assignment_cost[i][j]*x[i,j])"}
# Specification limitation: the referenced LP data was not provided.
# This implements all six explicitly described NOE restrictions; additional
# restrictions cannot be inferred from the supplied problem statement.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_cost = params["assignment_cost"]
    required_assignments = params["required_assignments"]

    model = pyo.ConcreteModel()

    model.peaks = pyo.Set(initialize=range(5), ordered=True)
    model.amino_acids = pyo.Set(initialize=range(6), ordered=True)
    model.noe_pairs = pyo.Set(
        dimen=4,
        initialize=[
            (0, 4, 0, 1),
            (0, 4, 0, 3),
            (0, 4, 0, 4),
            (1, 2, 0, 1),
            (1, 2, 0, 3),
            (1, 2, 0, 4),
        ],
        ordered=True,
    )

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (i, j): assignment_cost[i][j]
            for i in model.peaks
            for j in model.amino_acids
        },
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=required_assignments,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_limit_rule(current_model, i):
        return sum(
            current_model.x[i, j] for j in current_model.amino_acids
        ) <= 1

    model.peak_limits = pyo.Constraint(
        model.peaks,
        rule=peak_limit_rule,
    )

    def amino_acid_limit_rule(current_model, j):
        return sum(
            current_model.x[i, j] for i in current_model.peaks
        ) <= 1

    model.amino_acid_limits = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_limit_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[i, j]
            for i in model.peaks
            for j in model.amino_acids
        ) == model.required_assignments
    )

    def noe_rule(current_model, i, k, j, l):
        return current_model.x[i, j] + current_model.x[k, l] <= 1

    model.noe_constraints = pyo.Constraint(
        model.noe_pairs,
        rule=noe_rule,
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
        # APPSI HiGHS raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}