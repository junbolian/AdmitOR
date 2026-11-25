# IR: {"sets":{"cargo_ids":"0..5","vehicle_ids":"0..5"},"params":{"cargo_weight[i]":"params['cargo_weights'][i]","capacity":"params['vehicle_capacity']"},"variables":{"assigned[i,v]":"binary","vehicle_used[v]":"binary"},"constraints":["For each i: sum_v assigned[i,v] = 1","For each v: sum_i cargo_weight[i]*assigned[i,v] <= capacity*vehicle_used[v]","For each i,v: assigned[i,v] <= vehicle_used[v]"],"objective":"minimize sum_v vehicle_used[v]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cargo_weights = params["cargo_weights"]
    vehicle_capacity = params["vehicle_capacity"]

    model = pyo.ConcreteModel()
    model.cargo_ids = pyo.RangeSet(0, 5)
    model.vehicle_ids = pyo.RangeSet(0, 5)

    model.cargo_weight = pyo.Param(
        model.cargo_ids,
        initialize={item: cargo_weights[item] for item in model.cargo_ids},
    )
    model.capacity = pyo.Param(initialize=vehicle_capacity)

    model.assigned = pyo.Var(
        model.cargo_ids, model.vehicle_ids, domain=pyo.Binary
    )
    model.vehicle_used = pyo.Var(model.vehicle_ids, domain=pyo.Binary)

    def assignment_rule(instance, item):
        return sum(
            instance.assigned[item, vehicle]
            for vehicle in instance.vehicle_ids
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.cargo_ids, rule=assignment_rule
    )

    def capacity_rule(instance, vehicle):
        return sum(
            instance.cargo_weight[item] * instance.assigned[item, vehicle]
            for item in instance.cargo_ids
        ) <= instance.capacity * instance.vehicle_used[vehicle]

    model.capacity_constraints = pyo.Constraint(
        model.vehicle_ids, rule=capacity_rule
    )

    def usage_rule(instance, item, vehicle):
        return instance.assigned[item, vehicle] <= instance.vehicle_used[vehicle]

    model.usage_constraints = pyo.Constraint(
        model.cargo_ids, model.vehicle_ids, rule=usage_rule
    )

    model.total_vehicles = pyo.Objective(
        expr=sum(
            model.vehicle_used[vehicle] for vehicle in model.vehicle_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_vehicles))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}