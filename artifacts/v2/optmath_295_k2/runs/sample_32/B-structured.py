# IR: {"sets":{"origins":[0,1,2,3,4],"destinations":[0,1,2,3,4]},"params":{"supply_origin":"nonnegative vector indexed by origins","demand_destination":"nonnegative vector indexed by destinations","cost_matrix":"real matrix indexed by origins,destinations","capacity_matrix":"nonnegative matrix indexed by origins,destinations"},"variables":{"shipment[o,d]":"nonnegative continuous"},"constraints":["sum_d shipment[o,d] = supply_origin[o] for each origin o","sum_o shipment[o,d] = demand_destination[d] for each destination d","shipment[o,d] <= capacity_matrix[o,d] for each pair (o,d)"],"objective":"minimize sum_(o,d) cost_matrix[o,d] * shipment[o,d]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_origin = params["supply_origin"]
    demand_destination = params["demand_destination"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 4)

    model.supply_origin = pyo.Param(
        model.origins,
        initialize={o: supply_origin[o] for o in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand_destination = pyo.Param(
        model.destinations,
        initialize={d: demand_destination[d] for d in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (o, d): cost_matrix[o][d]
            for o in model.origins
            for d in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity_matrix = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (o, d): capacity_matrix[o][d]
            for o in model.origins
            for d in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(block, o):
        return (
            sum(block.shipment[o, d] for d in block.destinations)
            == block.supply_origin[o]
        )

    def demand_rule(block, d):
        return (
            sum(block.shipment[o, d] for o in block.origins)
            == block.demand_destination[d]
        )

    def capacity_rule(block, o, d):
        return block.shipment[o, d] <= block.capacity_matrix[o, d]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[o, d] * model.shipment[o, d]
            for o in model.origins
            for d in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}