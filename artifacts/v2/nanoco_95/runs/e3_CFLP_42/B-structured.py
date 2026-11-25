# IR: {"sets":{"C":"0..4","H":"0..19"},"params":{"opening_cost":"params['opening_cost'][c]","capacity":"params['capacity'][c]","demand":"params['demand'][h]","transport_cost":"params['transport_cost']; accept 5x20 center-major or 20x5 hospital-major; normalize to cost[c,h]"},"variables":{"opened[c]":"Binary","assigned[c,h]":"Binary"},"constraints":["For each h: sum(c in C, assigned[c,h]) == 1","For each c: sum(h in H, demand[h]*assigned[c,h]) <= capacity[c]*opened[c]","For each c,h: assigned[c,h] <= opened[c]"],"objective":"Minimize sum(c in C, opening_cost[c]*opened[c]) + sum(c in C,h in H, demand[h]*cost[c,h]*assigned[c,h])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    if len(opening_cost) != 5:
        raise ValueError("opening_cost must contain five values.")
    if len(capacity) != 5:
        raise ValueError("capacity must contain five values.")
    if len(demand) != 20:
        raise ValueError("demand must contain twenty values.")

    if len(transport_cost) == 5 and all(
        len(row) == 20 for row in transport_cost
    ):
        normalized_cost = {
            (center, hospital): transport_cost[center][hospital]
            for center in range(5)
            for hospital in range(20)
        }
    elif len(transport_cost) == 20 and all(
        len(row) == 5 for row in transport_cost
    ):
        normalized_cost = {
            (center, hospital): transport_cost[hospital][center]
            for center in range(5)
            for hospital in range(20)
        }
    else:
        raise ValueError("transport_cost must have shape 5x20 or 20x5.")

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 4)
    model.hospitals = pyo.RangeSet(0, 19)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize=lambda _, center: opening_cost[center],
        within=pyo.NonNegativeReals,
    )
    model.processing_capacity = pyo.Param(
        model.centers,
        initialize=lambda _, center: capacity[center],
        within=pyo.NonNegativeReals,
    )
    model.hospital_demand = pyo.Param(
        model.hospitals,
        initialize=lambda _, hospital: demand[hospital],
        within=pyo.NonNegativeReals,
    )
    model.unit_transport_cost = pyo.Param(
        model.centers,
        model.hospitals,
        initialize=normalized_cost,
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.centers, model.hospitals, domain=pyo.Binary
    )

    def single_source_rule(instance, hospital):
        return sum(
            instance.assigned[center, hospital]
            for center in instance.centers
        ) == 1

    model.single_source = pyo.Constraint(
        model.hospitals, rule=single_source_rule
    )

    def capacity_rule(instance, center):
        return sum(
            instance.hospital_demand[hospital]
            * instance.assigned[center, hospital]
            for hospital in instance.hospitals
        ) <= instance.processing_capacity[center] * instance.opened[center]

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    def opening_link_rule(instance, center, hospital):
        return instance.assigned[center, hospital] <= instance.opened[center]

    model.opening_link = pyo.Constraint(
        model.centers, model.hospitals, rule=opening_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.hospital_demand[hospital]
            * model.unit_transport_cost[center, hospital]
            * model.assigned[center, hospital]
            for center in model.centers
            for hospital in model.hospitals
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}