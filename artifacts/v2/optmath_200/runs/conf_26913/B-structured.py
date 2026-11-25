# IR: {"sets":{"I":"1..6","T":"0..params['num_trucks']-1"},"params":{"truck_capacity":"params['truck_capacity']","shipment_weights":"params['shipment_weights'], sequence ordered by shipment 1..6","num_trucks":"params['num_trucks'], frozen index-set size"},"variables":{"x[i,t]":"binary; shipment i assigned to truck t","y[t]":"binary; truck t used"},"constraints":["For each i: sum_t x[i,t] = 1","For each t: sum_i shipment_weights[i-1]*x[i,t] <= truck_capacity*y[t]","For each i,t: x[i,t] <= y[t]","For each t: y[t] <= sum_i x[i,t]"],"objective":"minimize sum_t y[t]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["truck_capacity"]
    weights = params["shipment_weights"]
    truck_count = params["num_trucks"]

    model = pyo.ConcreteModel()

    model.shipments = pyo.RangeSet(1, 6)
    model.trucks = pyo.Set(initialize=range(truck_count), ordered=True)

    model.capacity = pyo.Param(initialize=capacity)
    model.weights = pyo.Param(
        model.shipments,
        initialize={
            shipment: weights[shipment - 1]
            for shipment in model.shipments
        },
    )

    model.assignment = pyo.Var(
        model.shipments, model.trucks, domain=pyo.Binary
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, shipment):
        # A two-element tuple constructs a native equality constraint,
        # including when the truck set is empty.
        return (
            pyo.quicksum(
                instance.assignment[shipment, truck]
                for truck in instance.trucks
            ),
            1,
        )

    model.assign_once = pyo.Constraint(
        model.shipments, rule=assignment_rule
    )

    def capacity_rule(instance, truck):
        return pyo.quicksum(
            instance.weights[shipment]
            * instance.assignment[shipment, truck]
            for shipment in instance.shipments
        ) <= instance.capacity * instance.truck_used[truck]

    model.capacity_limit = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def usage_link_rule(instance, shipment, truck):
        return (
            instance.assignment[shipment, truck]
            <= instance.truck_used[truck]
        )

    model.usage_link = pyo.Constraint(
        model.shipments, model.trucks, rule=usage_link_rule
    )

    def nonempty_rule(instance, truck):
        return instance.truck_used[truck] <= pyo.quicksum(
            instance.assignment[shipment, truck]
            for shipment in instance.shipments
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.trucks, rule=nonempty_rule
    )

    model.total_trucks = pyo.Objective(
        expr=pyo.quicksum(
            model.truck_used[truck] for truck in model.trucks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}