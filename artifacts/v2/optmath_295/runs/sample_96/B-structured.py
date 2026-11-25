# IR: {"sets":{"peaks":[0,1,2,3,4],"amino_acids":[0,1,2,3,4,5]},"params":{"cost_peak{peak}_aa{aa}":"real cost for every (peak,aa) in peaks x amino_acids","num_assignments_required":"required assignment count","noe_pair_p1aa1_p2aa0_rhs":"first NOE upper bound","noe_pair_p1aa3_p2aa0_rhs":"second NOE upper bound"},"variables":{"x[peak,aa]":"binary"},"constraints":["for each peak: sum_aa x[peak,aa] <= 1","for each aa: sum_peak x[peak,aa] <= 1","sum_peak,aa x[peak,aa] = num_assignments_required","x[1,1] + x[2,0] <= noe_pair_p1aa1_p2aa0_rhs","x[1,3] + x[2,0] <= noe_pair_p1aa3_p2aa0_rhs"],"objective":"minimize sum_peak,aa cost_peak{peak}_aa{aa} * x[peak,aa]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.peaks = pyo.RangeSet(0, 4)
    model.amino_acids = pyo.RangeSet(0, 5)

    model.assignment_cost = pyo.Param(
        model.peaks,
        model.amino_acids,
        initialize={
            (peak, aa): params[f"cost_peak{peak}_aa{aa}"]
            for peak in model.peaks
            for aa in model.amino_acids
        },
        within=pyo.Reals,
    )
    model.required_assignments = pyo.Param(
        initialize=params["num_assignments_required"],
        within=pyo.Reals,
    )
    model.noe_first_rhs = pyo.Param(
        initialize=params["noe_pair_p1aa1_p2aa0_rhs"],
        within=pyo.Reals,
    )
    model.noe_second_rhs = pyo.Param(
        initialize=params["noe_pair_p1aa3_p2aa0_rhs"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.peaks,
        model.amino_acids,
        domain=pyo.Binary,
    )

    def peak_capacity_rule(instance, peak):
        return sum(
            instance.x[peak, aa] for aa in instance.amino_acids
        ) <= 1

    model.peak_capacity = pyo.Constraint(
        model.peaks,
        rule=peak_capacity_rule,
    )

    def amino_acid_capacity_rule(instance, aa):
        return sum(
            instance.x[peak, aa] for peak in instance.peaks
        ) <= 1

    model.amino_acid_capacity = pyo.Constraint(
        model.amino_acids,
        rule=amino_acid_capacity_rule,
    )

    model.assignment_count = pyo.Constraint(
        expr=sum(
            model.x[peak, aa]
            for peak in model.peaks
            for aa in model.amino_acids
        ) == model.required_assignments
    )

    model.noe_first = pyo.Constraint(
        expr=model.x[1, 1] + model.x[2, 0] <= model.noe_first_rhs
    )
    model.noe_second = pyo.Constraint(
        expr=model.x[1, 3] + model.x[2, 0] <= model.noe_second_rhs
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[peak, aa] * model.x[peak, aa]
            for peak in model.peaks
            for aa in model.amino_acids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}