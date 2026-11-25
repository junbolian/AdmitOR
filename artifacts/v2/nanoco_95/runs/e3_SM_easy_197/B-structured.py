# IR: {"sets":{"S":"0..6","P":"0..6"},"params":{"supplier_pref_positions":"rS[S,P], read from params","plant_pref_positions":"rP[P,S], read from params"},"variables":{"x[S,P]":"binary"},"constraints":["For each i in S: sum(j in P, x[i,j]) = 1","For each j in P: sum(i in S, x[i,j]) = 1","For each (i,j): x[i,j] + sum(k in P: rS[i,k] < rS[i,j], x[i,k]) + sum(h in S: rP[j,h] < rP[j,i], x[h,j]) >= 1"],"objective":"minimize sum(i in S, j in P, (rS[i,j] + rP[j,i]) * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplier_ranks = params["supplier_pref_positions"]
    plant_ranks = params["plant_pref_positions"]

    model = pyo.ConcreteModel()

    model.S = pyo.RangeSet(0, 6)
    model.P = pyo.RangeSet(0, 6)

    model.rS = pyo.Param(
        model.S,
        model.P,
        initialize=lambda mdl, supplier, plant: supplier_ranks[supplier][plant],
        within=pyo.NonNegativeIntegers,
    )
    model.rP = pyo.Param(
        model.P,
        model.S,
        initialize=lambda mdl, plant, supplier: plant_ranks[plant][supplier],
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.S, model.P, domain=pyo.Binary)

    def supplier_assignment_rule(mdl, supplier):
        return sum(mdl.x[supplier, plant] for plant in mdl.P) == 1

    model.supplier_assignment = pyo.Constraint(
        model.S, rule=supplier_assignment_rule
    )

    def plant_assignment_rule(mdl, plant):
        return sum(mdl.x[supplier, plant] for supplier in mdl.S) == 1

    model.plant_assignment = pyo.Constraint(
        model.P, rule=plant_assignment_rule
    )

    def stability_rule(mdl, supplier, plant):
        preferred_plants = sum(
            mdl.x[supplier, other_plant]
            for other_plant in mdl.P
            if pyo.value(mdl.rS[supplier, other_plant])
            < pyo.value(mdl.rS[supplier, plant])
        )
        preferred_suppliers = sum(
            mdl.x[other_supplier, plant]
            for other_supplier in mdl.S
            if pyo.value(mdl.rP[plant, other_supplier])
            < pyo.value(mdl.rP[plant, supplier])
        )
        return (
            mdl.x[supplier, plant]
            + preferred_plants
            + preferred_suppliers
            >= 1
        )

    model.stability = pyo.Constraint(
        model.S, model.P, rule=stability_rule
    )

    model.total_risk = pyo.Objective(
        expr=sum(
            (model.rS[supplier, plant] + model.rP[plant, supplier])
            * model.x[supplier, plant]
            for supplier in model.S
            for plant in model.P
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_risk))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}