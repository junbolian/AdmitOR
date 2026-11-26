# IR: {"sets":{"W":["Verona","Perugia","Rome","Pescara","Taranto","La Spezia"],"P":["Genoa","Venice","Ancona","Naples","Bari"]},"params":{"supply":"nonnegative[W]","demand":"nonnegative[P]","cost_rate":"nonnegative scalar","distance":"nonnegative[W,P]","truck_capacity":"nonnegative scalar"},"variables":{"containers[W,P]":"nonnegative integer","trucks[W,P]":"nonnegative integer"},"constraints":{"warehouse_supply":"sum(p in P, containers[w,p]) <= supply[w] for w in W","port_demand":"sum(w in W, containers[w,p]) == demand[p] for p in P","truck_loading":"containers[w,p] <= truck_capacity * trucks[w,p] for (w,p) in W x P"},"objective":"minimize sum((w,p) in W x P, cost_rate * distance[w,p] * containers[w,p])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouses = (
        "Verona",
        "Perugia",
        "Rome",
        "Pescara",
        "Taranto",
        "La Spezia",
    )
    ports = ("Genoa", "Venice", "Ancona", "Naples", "Bari")

    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_rate_data = params["cost_rate"]
    distance_data = params["distance"]
    truck_capacity_data = params["truck_capacity"]

    # Vectors accept ordered sequences or mappings keyed by location name.
    def vector_value(data, position, location):
        if isinstance(data, Mapping):
            return data[location]
        return data[position]

    # Distances accept an ordered matrix, nested location mappings,
    # or a mapping keyed by (warehouse_name, port_name).
    def distance_value(warehouse_position, port_position):
        warehouse = warehouses[warehouse_position]
        port = ports[port_position]
        if isinstance(distance_data, Mapping):
            if (warehouse, port) in distance_data:
                return distance_data[warehouse, port]
            row = distance_data[warehouse]
        else:
            row = distance_data[warehouse_position]
        return vector_value(row, port_position, port)

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses, ordered=True)
    model.P = pyo.Set(initialize=ports, ordered=True)

    model.supply = pyo.Param(
        model.W,
        initialize={
            warehouse: vector_value(supply_data, position, warehouse)
            for position, warehouse in enumerate(warehouses)
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.P,
        initialize={
            port: vector_value(demand_data, position, port)
            for position, port in enumerate(ports)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost_rate = pyo.Param(
        initialize=cost_rate_data,
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.W,
        model.P,
        initialize={
            (warehouse, port): distance_value(
                warehouse_position, port_position
            )
            for warehouse_position, warehouse in enumerate(warehouses)
            for port_position, port in enumerate(ports)
        },
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=truck_capacity_data,
        within=pyo.NonNegativeReals,
    )

    model.containers = pyo.Var(
        model.W, model.P, domain=pyo.NonNegativeIntegers
    )
    model.trucks = pyo.Var(
        model.W, model.P, domain=pyo.NonNegativeIntegers
    )

    def warehouse_supply_rule(instance, warehouse):
        return (
            sum(instance.containers[warehouse, port] for port in instance.P)
            <= instance.supply[warehouse]
        )

    def port_demand_rule(instance, port):
        return (
            sum(
                instance.containers[warehouse, port]
                for warehouse in instance.W
            )
            == instance.demand[port]
        )

    def truck_loading_rule(instance, warehouse, port):
        return (
            instance.containers[warehouse, port]
            <= instance.truck_capacity * instance.trucks[warehouse, port]
        )

    model.warehouse_supply = pyo.Constraint(
        model.W, rule=warehouse_supply_rule
    )
    model.port_demand = pyo.Constraint(
        model.P, rule=port_demand_rule
    )
    model.truck_loading = pyo.Constraint(
        model.W, model.P, rule=truck_loading_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_rate
            * model.distance[warehouse, port]
            * model.containers[warehouse, port]
            for warehouse in model.W
            for port in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}