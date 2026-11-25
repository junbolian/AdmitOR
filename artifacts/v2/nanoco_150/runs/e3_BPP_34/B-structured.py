# IR: {"sets":{"I":"0..15 shipments","T":"0..15 candidate trucks"},"params":{"truck_capacity":"params['truck_capacity'], nonnegative","shipment_weights":"params['shipment_weights'], 16 nonnegative weights"},"variables":{"assign[i,t]":"binary","truck_used[t]":"binary"},"constraints":["For each i: sum_t assign[i,t] = 1","For each t: sum_i shipment_weights[i]*assign[i,t] <= truck_capacity*truck_used[t]","For each i,t: assign[i,t] <= truck_used[t]"],"objective":"Minimize sum_t truck_used[t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_capacity = params["truck_capacity"]
    shipment_weights = params["shipment_weights"]

    if len(shipment_weights) != 16:
        return {"objective": None, "status": "invalid_shipment_count"}

    model = pyo.ConcreteModel()

    model.shipments = pyo.RangeSet(0, 15)
    model.trucks = pyo.RangeSet(0, 15)

    model.capacity = pyo.Param(
        initialize=truck_capacity,
        within=pyo.NonNegativeReals,
    )
    model.weights = pyo.Param(
        model.shipments,
        initialize={
            shipment_idx: shipment_weights[shipment_idx]
            for shipment_idx in model.shipments
        },
        within=pyo.NonNegativeReals,
    )

    model.assign = pyo.Var(
        model.shipments, model.trucks, domain=pyo.Binary
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(problem, shipment_idx):
        return sum(
            problem.assign[shipment_idx, truck_idx]
            for truck_idx in problem.trucks
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.shipments, rule=assignment_rule
    )

    def capacity_rule(problem, truck_idx):
        return sum(
            problem.weights[shipment_idx]
            * problem.assign[shipment_idx, truck_idx]
            for shipment_idx in problem.shipments
        ) <= problem.capacity * problem.truck_used[truck_idx]

    model.capacity_constraints = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def activation_rule(problem, shipment_idx, truck_idx):
        return (
            problem.assign[shipment_idx, truck_idx]
            <= problem.truck_used[truck_idx]
        )

    model.activation_constraints = pyo.Constraint(
        model.shipments, model.trucks, rule=activation_rule
    )

    model.total_trucks = pyo.Objective(
        expr=sum(
            model.truck_used[truck_idx] for truck_idx in model.trucks
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
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}