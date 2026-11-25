# IR: {"sets":{"Z":"range(num_warehouse_zones)","A[z]":"zone_z_allowed_types","E":"incompatibility_pairs","ZA":"{(z,t): z in Z, t in A[z]}"},"params":["incompatibility_pairs","zone_0_allowed_types","zone_1_allowed_types","zone_2_allowed_types","zone_3_allowed_types","zone_4_allowed_types","zone_5_allowed_types","zone_6_allowed_types","zone_7_allowed_types","zone_8_allowed_types","zone_9_allowed_types","num_warehouse_zones","num_incompatibility_pairs"],"validation":["num_warehouse_zones equals the number of supplied zone lists","num_incompatibility_pairs equals len(incompatibility_pairs)","each incompatibility endpoint belongs to Z"],"variables":{"x[z,t]":"Binary for (z,t) in ZA","maximum_type":"NonNegativeIntegers"},"constraints":["sum(x[z,t] for t in A[z]) = 1 for each z in Z","x[u,t] + x[v,t] <= 1 for each (u,v) in E and t in A[u] intersect A[v]","maximum_type >= sum(t*x[z,t] for t in A[z]) for each z in Z"],"objective":"minimize maximum_type"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_zones = params["num_warehouse_zones"]
    num_pairs = params["num_incompatibility_pairs"]
    incompatibility_pairs = [
        tuple(pair) for pair in params["incompatibility_pairs"]
    ]
    allowed_lists = [
        params["zone_0_allowed_types"],
        params["zone_1_allowed_types"],
        params["zone_2_allowed_types"],
        params["zone_3_allowed_types"],
        params["zone_4_allowed_types"],
        params["zone_5_allowed_types"],
        params["zone_6_allowed_types"],
        params["zone_7_allowed_types"],
        params["zone_8_allowed_types"],
        params["zone_9_allowed_types"],
    ]

    if num_zones != len(allowed_lists):
        raise ValueError("Warehouse zone count does not match supplied zone lists.")
    if num_pairs != len(incompatibility_pairs):
        raise ValueError("Incompatibility pair count does not match supplied pairs.")

    zones = range(num_zones)
    if any(
        len(pair) != 2 or any(zone not in zones for zone in pair)
        for pair in incompatibility_pairs
    ):
        raise ValueError("Each incompatibility pair must contain two valid zones.")

    allowed = {
        zone: tuple(dict.fromkeys(allowed_lists[zone]))
        for zone in zones
    }
    allowed_sets = {
        zone: set(allowed[zone])
        for zone in zones
    }
    assignment_indices = [
        (zone, type_index)
        for zone in zones
        for type_index in allowed[zone]
    ]
    conflict_indices = list(
        dict.fromkeys(
            (first_zone, second_zone, type_index)
            for first_zone, second_zone in incompatibility_pairs
            for type_index in allowed[first_zone]
            if type_index in allowed_sets[second_zone]
        )
    )

    model = pyo.ConcreteModel()
    model.zones = pyo.Set(initialize=zones, ordered=True)
    model.assignment_indices = pyo.Set(
        dimen=2, initialize=assignment_indices, ordered=True
    )
    model.conflict_indices = pyo.Set(
        dimen=3, initialize=conflict_indices, ordered=True
    )

    model.x = pyo.Var(model.assignment_indices, domain=pyo.Binary)
    model.maximum_type = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assignment_rule(current_model, zone):
        expression = pyo.quicksum(
            current_model.x[zone, type_index]
            for type_index in allowed[zone]
        )
        # Tuple form also represents infeasibility for an empty allowed list.
        return (1, expression, 1)

    model.one_type_per_zone = pyo.Constraint(
        model.zones, rule=assignment_rule
    )

    def incompatibility_rule(
        current_model, first_zone, second_zone, type_index
    ):
        return (
            current_model.x[first_zone, type_index]
            + current_model.x[second_zone, type_index]
            <= 1
        )

    model.incompatible_assignments = pyo.Constraint(
        model.conflict_indices, rule=incompatibility_rule
    )

    def maximum_rule(current_model, zone):
        return current_model.maximum_type >= pyo.quicksum(
            type_index * current_model.x[zone, type_index]
            for type_index in allowed[zone]
        )

    model.maximum_type_bounds = pyo.Constraint(
        model.zones, rule=maximum_rule
    )
    model.objective = pyo.Objective(
        expr=model.maximum_type, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise
        return {"objective": None, "status": "no_solution"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}