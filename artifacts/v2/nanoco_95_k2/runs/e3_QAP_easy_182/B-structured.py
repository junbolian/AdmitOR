# IR: {"sets":{"R":"range(num_facilities)","S":"range(num_locations)","A":"range(2)"},"params":{"num_facilities":"params[num_facilities]","num_locations":"params[num_locations]","flow_matrix":"params[flow_matrix], indexed by R x R","distance_matrix":"params[distance_matrix], indexed by S x S","location_coords":"params[location_coords], indexed by S x A; descriptive coordinates"},"variables":{"x[r,s]":"binary rack-to-slot assignment","y[r,t,s,u]":"continuous in [0,1], equal to x[r,s]*x[t,u]"},"constraints":["For each r: sum_s x[r,s] = 1","For each s: sum_r x[r,s] = 1","For each r,t,s,u: y[r,t,s,u] <= x[r,s]","For each r,t,s,u: y[r,t,s,u] <= x[t,u]","For each r,t,s,u: y[r,t,s,u] >= x[r,s] + x[t,u] - 1"],"objective":"Minimize sum_{r,t in R; s,u in S} flow_matrix[r,t]*distance_matrix[s,u]*y[r,t,s,u], using the standard ordered-pair quadratic-assignment convention."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_locations = params["num_locations"]
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    location_coords = params["location_coords"]

    model = pyo.ConcreteModel()

    model.racks = pyo.Set(
        initialize=range(num_facilities), ordered=True
    )
    model.slots = pyo.Set(
        initialize=range(num_locations), ordered=True
    )
    model.coordinate_axes = pyo.Set(
        initialize=range(2), ordered=True
    )

    model.traffic = pyo.Param(
        model.racks,
        model.racks,
        initialize=lambda mdl, rack, other_rack: flow_matrix[rack][other_rack],
        within=pyo.Reals,
    )
    model.slot_distance = pyo.Param(
        model.slots,
        model.slots,
        initialize=lambda mdl, slot, other_slot: distance_matrix[slot][other_slot],
        within=pyo.Reals,
    )

    # Supplied distances define costs; coordinates are retained as input data.
    model.slot_coordinates = pyo.Param(
        model.slots,
        model.coordinate_axes,
        initialize=lambda mdl, slot, axis: location_coords[slot][axis],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.racks,
        model.slots,
        domain=pyo.Binary,
    )
    model.assignment_product = pyo.Var(
        model.racks,
        model.racks,
        model.slots,
        model.slots,
        domain=pyo.UnitInterval,
    )

    def rack_assignment_rule(mdl, rack):
        return sum(
            mdl.assignment[rack, slot] for slot in mdl.slots
        ) == 1

    model.each_rack_assigned = pyo.Constraint(
        model.racks, rule=rack_assignment_rule
    )

    def slot_assignment_rule(mdl, slot):
        return sum(
            mdl.assignment[rack, slot] for rack in mdl.racks
        ) == 1

    model.each_slot_occupied = pyo.Constraint(
        model.slots, rule=slot_assignment_rule
    )

    def product_first_upper_rule(mdl, rack, other_rack, slot, other_slot):
        return (
            mdl.assignment_product[rack, other_rack, slot, other_slot]
            <= mdl.assignment[rack, slot]
        )

    model.product_first_upper = pyo.Constraint(
        model.racks,
        model.racks,
        model.slots,
        model.slots,
        rule=product_first_upper_rule,
    )

    def product_second_upper_rule(mdl, rack, other_rack, slot, other_slot):
        return (
            mdl.assignment_product[rack, other_rack, slot, other_slot]
            <= mdl.assignment[other_rack, other_slot]
        )

    model.product_second_upper = pyo.Constraint(
        model.racks,
        model.racks,
        model.slots,
        model.slots,
        rule=product_second_upper_rule,
    )

    def product_lower_rule(mdl, rack, other_rack, slot, other_slot):
        return (
            mdl.assignment_product[rack, other_rack, slot, other_slot]
            >= mdl.assignment[rack, slot]
            + mdl.assignment[other_rack, other_slot]
            - 1
        )

    model.product_lower = pyo.Constraint(
        model.racks,
        model.racks,
        model.slots,
        model.slots,
        rule=product_lower_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.traffic[rack, other_rack]
            * model.slot_distance[slot, other_slot]
            * model.assignment_product[rack, other_rack, slot, other_slot]
            for rack in model.racks
            for other_rack in model.racks
            for slot in model.slots
            for other_slot in model.slots
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines the returned success status.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}