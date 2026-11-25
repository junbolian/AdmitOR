# IR: {"sets":{"shipments":"0..7","vehicles":"0..7"},"params":{"flammability_capacity_per_vehicle":"nonnegative scalar from params","toxicity_capacity_per_vehicle":"nonnegative scalar from params","flammability_demand":"8 nonnegative values from params, in shipment order","toxicity_demand":"8 nonnegative values from params, in shipment order"},"variables":{"assigned[i,v]":"binary","vehicle_used[v]":"binary"},"constraints":["For each shipment i: sum_v assigned[i,v] = 1","For each shipment i and vehicle v: assigned[i,v] <= vehicle_used[v]","For each vehicle v: sum_i flammability_demand[i]*assigned[i,v] <= flammability_capacity_per_vehicle*vehicle_used[v]","For each vehicle v: sum_i toxicity_demand[i]*assigned[i,v] <= toxicity_capacity_per_vehicle*vehicle_used[v]"],"objective":"minimize sum_v vehicle_used[v]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flammability_capacity = params["flammability_capacity_per_vehicle"]
    toxicity_capacity = params["toxicity_capacity_per_vehicle"]
    flammability_loads = list(params["flammability_demand"])
    toxicity_loads = list(params["toxicity_demand"])

    if len(flammability_loads) != 8 or len(toxicity_loads) != 8:
        raise ValueError("Each demand sequence must contain exactly 8 values.")

    model = pyo.ConcreteModel()

    model.shipments = pyo.RangeSet(0, 7)
    model.vehicles = pyo.RangeSet(0, 7)

    model.flammability_capacity_per_vehicle = pyo.Param(
        initialize=flammability_capacity,
        within=pyo.NonNegativeReals,
    )
    model.toxicity_capacity_per_vehicle = pyo.Param(
        initialize=toxicity_capacity,
        within=pyo.NonNegativeReals,
    )
    model.flammability_demand = pyo.Param(
        model.shipments,
        initialize=dict(enumerate(flammability_loads)),
        within=pyo.NonNegativeReals,
    )
    model.toxicity_demand = pyo.Param(
        model.shipments,
        initialize=dict(enumerate(toxicity_loads)),
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.shipments, model.vehicles, domain=pyo.Binary
    )
    model.vehicle_used = pyo.Var(model.vehicles, domain=pyo.Binary)

    def shipment_assignment_rule(block, shipment):
        return sum(
            block.assigned[shipment, vehicle] for vehicle in block.vehicles
        ) == 1

    model.shipment_assignment = pyo.Constraint(
        model.shipments, rule=shipment_assignment_rule
    )

    def activation_link_rule(block, shipment, vehicle):
        return block.assigned[shipment, vehicle] <= block.vehicle_used[vehicle]

    model.activation_link = pyo.Constraint(
        model.shipments, model.vehicles, rule=activation_link_rule
    )

    def flammability_limit_rule(block, vehicle):
        return sum(
            block.flammability_demand[shipment]
            * block.assigned[shipment, vehicle]
            for shipment in block.shipments
        ) <= (
            block.flammability_capacity_per_vehicle
            * block.vehicle_used[vehicle]
        )

    model.flammability_limit = pyo.Constraint(
        model.vehicles, rule=flammability_limit_rule
    )

    def toxicity_limit_rule(block, vehicle):
        return sum(
            block.toxicity_demand[shipment]
            * block.assigned[shipment, vehicle]
            for shipment in block.shipments
        ) <= (
            block.toxicity_capacity_per_vehicle
            * block.vehicle_used[vehicle]
        )

    model.toxicity_limit = pyo.Constraint(
        model.vehicles, rule=toxicity_limit_rule
    )

    model.total_vehicles = pyo.Objective(
        expr=sum(model.vehicle_used[vehicle] for vehicle in model.vehicles),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_vehicles))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}