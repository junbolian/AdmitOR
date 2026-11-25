# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"supply[o,p]":"params['supply'][2*o+p]","demand[d,p]":"params['demand'][2*d+p]","cost[o,d,p]":"params['cost'][(5*o+d)*2+p]","capacity[o,d]":"params['capacity'][5*o+d]"},"variables":{"shipment[o,d,p]":{"type":"continuous","lower_bound":0}},"constraints":["forall o,p: sum(d in D) shipment[o,d,p] = supply[o,p]","forall d,p: sum(o in O) shipment[o,d,p] = demand[d,p]","forall o,d: sum(p in P) shipment[o,d,p] <= capacity[o,d]"],"objective":{"sense":"minimize","expression":"sum(o in O,d in D,p in P) cost[o,d,p]*shipment[o,d,p]"}}

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
        initialize=lambda instance, origin, product: params["supply"][
            2 * origin + product
        ],
    )
    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize=lambda instance, destination, product: params["demand"][
            2 * destination + product
        ],
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize=lambda instance, origin, destination, product: params["cost"][
            (5 * origin + destination) * 2 + product
        ],
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda instance, origin, destination: params["capacity"][
            5 * origin + destination
        ],
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, origin, product):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for destination in instance.destinations
            )
            == instance.supply[origin, product]
        )

    def demand_rule(instance, destination, product):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for origin in instance.origins
            )
            == instance.demand[destination, product]
        )

    def capacity_rule(instance, origin, destination):
        return (
            sum(
                instance.shipment[origin, destination, product]
                for product in instance.products
            )
            <= instance.capacity[origin, destination]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, model.products, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, model.products, rule=demand_rule
    )
    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination, product]
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}