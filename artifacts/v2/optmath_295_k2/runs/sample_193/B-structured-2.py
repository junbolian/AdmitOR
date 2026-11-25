# IR: {"sets":{"origins":[0,1,2,3],"destinations":[0,1,2,3,4],"products":[0,1]},"params":{"supply[o,p]":"params[f'supply_origin{o}_product{p}']","demand[d,p]":"params[f'demand_dest{d}_product{p}']","cost[o,d,p]":"params['cost_matrix'][o][d][p]","capacity[o,d]":"params['capacity_matrix'][o][d]"},"variables":{"shipment[o,d,p]":"NonNegativeReals"},"constraints":["forall o,p: sum_d shipment[o,d,p] = supply[o,p]","forall d,p: sum_o shipment[o,d,p] = demand[d,p]","forall o,d: sum_p shipment[o,d,p] <= capacity[o,d]"],"objective":"minimize sum_{o,d,p} cost[o,d,p] * shipment[o,d,p]"}
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
    )

    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize={
            (origin, destination, product): cost_matrix[origin][destination][product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        },
    )

    model.route_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): capacity_matrix[origin][destination]
            for origin in model.origins
            for destination in model.destinations
        },
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(current_model, origin, product):
        return (
            sum(
                current_model.shipment[origin, destination, product]
                for destination in current_model.destinations
            )
            == current_model.supply[origin, product]
        )

    model.supply_balance = pyo.Constraint(
        model.origins,
        model.products,
        rule=supply_rule,
    )

    def demand_rule(current_model, destination, product):
        return (
            sum(
                current_model.shipment[origin, destination, product]
                for origin in current_model.origins
            )
            == current_model.demand[destination, product]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations,
        model.products,
        rule=demand_rule,
    )

    def capacity_rule(current_model, origin, destination):
        return (
            sum(
                current_model.shipment[origin, destination, product]
                for product in current_model.products
            )
            <= current_model.route_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination, product]
            * model.shipment[origin, destination, product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading cannot
        # retrieve a feasible solution. Unexpected runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}