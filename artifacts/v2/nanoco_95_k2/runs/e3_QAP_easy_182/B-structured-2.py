# IR: {"sets":{"I":"range(params['num_facilities'])","K":"range(params['num_locations'])"},"params":{"flow_matrix":"F[i,j]","distance_matrix":"D[k,l]","num_facilities":"|I|","num_locations":"|K|","location_coords":"coordinate metadata for K; supplied D defines costs"},"variables":{"x[i,k]":"Binary","y[i,j,k,l]":"continuous in [0,1]"},"constraints":["sum_k x[i,k] = 1 for each i","sum_i x[i,k] = 1 for each k","y[i,j,k,l] <= x[i,k] for each i,j,k,l","y[i,j,k,l] <= x[j,l] for each i,j,k,l","y[i,j,k,l] >= x[i,k] + x[j,l] - 1 for each i,j,k,l"],"objective":"minimize sum_{i,j,k,l} F[i,j]*D[k,l]*y[i,j,k,l], using the ordered-pair quadratic-assignment convention"}

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

    model.traffic = pyo.Param(
        model.racks,
        model.racks,
        initialize=lambda _, rack_a, rack_b: flow_matrix[rack_a][rack_b],
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.slots,
        model.slots,
        initialize=lambda _, slot_a, slot_b: distance_matrix[slot_a][slot_b],
        within=pyo.Reals,
    )

    # Coordinates are retained as metadata. The supplied distance matrix
    # is authoritative, so distances are not recomputed from coordinates.
    model.slot_coordinates = pyo.Param(
        model.slots,
        initialize={
            slot: tuple(location_coords[slot])
            for slot in range(num_locations)
        },
        within=pyo.Any,
    )

    model.assignment = pyo.Var(
        model.racks, model.slots, domain=pyo.Binary
    )
    model.assignment_product = pyo.Var(
        model.racks,
        model.racks,
        model.slots,
        model.slots,
        domain=pyo.UnitInterval,
    )

    def rack_assignment_rule(instance, rack):
        return sum(
            instance.assignment[rack, slot] for slot in instance.slots
        ) == 1

    model.one_slot_per_rack = pyo.Constraint(
        model.racks, rule=rack_assignment_rule
    )

    def slot_assignment_rule(instance, slot):
        return sum(
            instance.assignment[rack, slot] for rack in instance.racks
        ) == 1

    model.one_rack_per_slot = pyo.Constraint(
        model.slots, rule=slot_assignment_rule
    )

    def product_upper_first_rule(instance, rack_a, rack_b, slot_a, slot_b):
        return (
            instance.assignment_product[rack_a, rack_b, slot_a, slot_b]
            <= instance.assignment[rack_a, slot_a]
        )

    def product_upper_second_rule(instance, rack_a, rack_b, slot_a, slot_b):
        return (
            instance.assignment_product[rack_a, rack_b, slot_a, slot_b]
            <= instance.assignment[rack_b, slot_b]
        )

    def product_lower_rule(instance, rack_a, rack_b, slot_a, slot_b):
        return (
            instance.assignment_product[rack_a, rack_b, slot_a, slot_b]
            >= instance.assignment[rack_a, slot_a]
            + instance.assignment[rack_b, slot_b]
            - 1
        )

    product_indices = (
        model.racks, model.racks, model.slots, model.slots
    )
    model.product_upper_first = pyo.Constraint(
        *product_indices, rule=product_upper_first_rule
    )
    model.product_upper_second = pyo.Constraint(
        *product_indices, rule=product_upper_second_rule
    )
    model.product_lower = pyo.Constraint(
        *product_indices, rule=product_lower_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.traffic[rack_a, rack_b]
            * model.distance[slot_a, slot_b]
            * model.assignment_product[rack_a, rack_b, slot_a, slot_b]
            for rack_a in model.racks
            for rack_b in model.racks
            for slot_a in model.slots
            for slot_b in model.slots
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi HiGHS raises this when automatic solution loading finds
        # no feasible solution. Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}