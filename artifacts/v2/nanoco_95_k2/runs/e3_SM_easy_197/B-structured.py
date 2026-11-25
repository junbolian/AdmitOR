# IR: {"sets":{"S":"0..6","P":"0..6"},"params":{"supplier_pref_positions":"rank_s[i,j], read from params; rows S, columns P","plant_pref_positions":"rank_p[j,i], read from params; rows P, columns S"},"variables":{"x[i,j]":"binary for (i,j) in S x P"},"constraints":["For each i in S: sum(j in P, x[i,j]) = 1","For each j in P: sum(i in S, x[i,j]) = 1","For each (i,j): x[i,j] + sum(k in P where rank_s[i,k] < rank_s[i,j], x[i,k]) + sum(h in S where rank_p[j,h] < rank_p[j,i], x[h,j]) >= 1"],"objective":"minimize sum(i in S, j in P, (rank_s[i,j] + rank_p[j,i]) * x[i,j])"}

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
        initialize=lambda model, supplier_idx, plant_idx: supplier_positions[
            supplier_idx
        ][plant_idx],
        within=pyo.NonNegativeIntegers,
    )
    model.plant_rank = pyo.Param(
        model.plants,
        model.suppliers,
        initialize=lambda model, plant_idx, supplier_idx: plant_positions[
            plant_idx
        ][supplier_idx],
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.suppliers, model.plants, domain=pyo.Binary)

    def supplier_assignment_rule(model, supplier_idx):
        return sum(
            model.x[supplier_idx, plant_idx] for plant_idx in model.plants
        ) == 1

    model.supplier_assignment = pyo.Constraint(
        model.suppliers, rule=supplier_assignment_rule
    )

    def plant_assignment_rule(model, plant_idx):
        return sum(
            model.x[supplier_idx, plant_idx] for supplier_idx in model.suppliers
        ) == 1

    model.plant_assignment = pyo.Constraint(
        model.plants, rule=plant_assignment_rule
    )

    def stability_rule(model, supplier_idx, plant_idx):
        preferred_plants = sum(
            model.x[supplier_idx, other_plant]
            for other_plant in model.plants
            if pyo.value(model.supplier_rank[supplier_idx, other_plant])
            < pyo.value(model.supplier_rank[supplier_idx, plant_idx])
        )
        preferred_suppliers = sum(
            model.x[other_supplier, plant_idx]
            for other_supplier in model.suppliers
            if pyo.value(model.plant_rank[plant_idx, other_supplier])
            < pyo.value(model.plant_rank[plant_idx, supplier_idx])
        )
        return (
            model.x[supplier_idx, plant_idx]
            + preferred_plants
            + preferred_suppliers
            >= 1
        )

    model.stability = pyo.Constraint(
        model.suppliers, model.plants, rule=stability_rule
    )

    model.total_risk = pyo.Objective(
        expr=sum(
            (
                model.supplier_rank[supplier_idx, plant_idx]
                + model.plant_rank[plant_idx, supplier_idx]
            )
            * model.x[supplier_idx, plant_idx]
            for supplier_idx in model.suppliers
            for plant_idx in model.plants
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI raises RuntimeError when a feasible solution cannot be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_risk))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}