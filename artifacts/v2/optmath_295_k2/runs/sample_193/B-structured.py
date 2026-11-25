# IR: {"sets":{"origins":[0,1,2,3],"destinations":[0,1,2,3,4],"products":[0,1]},"params":{"supply[o,p]":"params[supply_origin{o}_product{p}]","demand[d,p]":"params[demand_dest{d}_product{p}]","cost[o,d,p]":"params[cost_matrix][o][d][p]","capacity[o,d]":"params[capacity_matrix][o][d]"},"variables":{"shipment[o,d,p]":"NonNegativeReals"},"constraints":["For each o,p: sum_d shipment[o,d,p] == supply[o,p]","For each d,p: sum_o shipment[o,d,p] == demand[d,p]","For each o,d: sum_p shipment[o,d,p] <= capacity[o,d]"],"objective":"Minimize sum_{o,d,p} cost[o,d,p] * shipment[o,d,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.origins,
        model.products,
        initialize={
            (origin, product): params[
                f"supply_origin{origin}_product{product}"
            ]
            for origin in model.origins
            for product in model.products
        },
        within=pyo.NonNegativeReals,
    )

    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize={
            (destination, product): params[
                f"demand_dest{destination}_product{product}"
            ]
            for destination in model.destinations
            for product in model.products
        },
        within=pyo.NonNegativeReals,
    )

    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize={
            (origin, destination, product):
                cost_matrix[origin][destination][product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.pair_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): capacity_matrix[origin][destination]
            for origin in model.origins
            for destination in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(model, origin, product):
        return sum(
            model.shipment[origin, destination, product]
            for destination in model.destinations
        ) == model.supply[origin, product]

    model.supply_balance = pyo.Constraint(
        model.origins,
        model.products,
        rule=supply_rule,
    )

    def demand_rule(model, destination, product):
        return sum(
            model.shipment[origin, destination, product]
            for origin in model.origins
        ) == model.demand[destination, product]

    model.demand_balance = pyo.Constraint(
        model.destinations,
        model.products,
        rule=demand_rule,
    )

    def capacity_rule(model, origin, destination):
        return sum(
            model.shipment[origin, destination, product]
            for product in model.products
        ) <= model.pair_capacity[origin, destination]

    model.capacity_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination, product]
            * model.shipment[origin, destination, product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}