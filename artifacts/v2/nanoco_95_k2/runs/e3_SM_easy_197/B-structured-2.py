# IR: {"sets":{"suppliers":"0..6","plants":"0..6"},"params":{"supplier_pref_positions":"7x7 zero-indexed supplier rankings","plant_pref_positions":"7x7 zero-indexed plant rankings"},"variables":{"x[i,j]":"binary; 1 iff supplier i is matched to plant j"},"constraints":["For each supplier i: sum_j x[i,j] = 1","For each plant j: sum_i x[i,j] = 1","For every pair (i,j): x[i,j] + sum_{k: supplier_pref_positions[i,k] < supplier_pref_positions[i,j]} x[i,k] + sum_{h: plant_pref_positions[j,h] < plant_pref_positions[j,i]} x[h,j] >= 1"],"objective":"Minimize sum_{i,j} (supplier_pref_positions[i,j] + plant_pref_positions[j,i]) * x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplier_positions = params["supplier_pref_positions"]
    plant_positions = params["plant_pref_positions"]

    model = pyo.ConcreteModel()

    model.suppliers = pyo.RangeSet(0, 6)
    model.plants = pyo.RangeSet(0, 6)

    model.supplier_rank = pyo.Param(
        model.suppliers,
        model.plants,
        initialize=lambda mdl, i, j: supplier_positions[i][j],
        within=pyo.NonNegativeIntegers,
    )
    model.plant_rank = pyo.Param(
        model.plants,
        model.suppliers,
        initialize=lambda mdl, j, i: plant_positions[j][i],
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(
        model.suppliers,
        model.plants,
        domain=pyo.Binary,
    )

    def supplier_assignment_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.plants) == 1

    model.supplier_assignment = pyo.Constraint(
        model.suppliers,
        rule=supplier_assignment_rule,
    )

    def plant_assignment_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.suppliers) == 1

    model.plant_assignment = pyo.Constraint(
        model.plants,
        rule=plant_assignment_rule,
    )

    def stability_rule(mdl, i, j):
        supplier_has_better_partner = sum(
            mdl.x[i, k]
            for k in mdl.plants
            if pyo.value(mdl.supplier_rank[i, k])
            < pyo.value(mdl.supplier_rank[i, j])
        )
        plant_has_better_partner = sum(
            mdl.x[h, j]
            for h in mdl.suppliers
            if pyo.value(mdl.plant_rank[j, h])
            < pyo.value(mdl.plant_rank[j, i])
        )
        return (
            mdl.x[i, j]
            + supplier_has_better_partner
            + plant_has_better_partner
            >= 1
        )

    model.stability = pyo.Constraint(
        model.suppliers,
        model.plants,
        rule=stability_rule,
    )

    model.total_risk = pyo.Objective(
        expr=sum(
            (model.supplier_rank[i, j] + model.plant_rank[j, i])
            * model.x[i, j]
            for i in model.suppliers
            for j in model.plants
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_risk))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}