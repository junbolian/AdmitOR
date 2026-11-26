# IR: {"sets":{"V":"range(num_cities)","E":"ordered (i,j) in V x V with i != j, excluding (1,3) and (2,3)"},"params":{"edge_capacities":"nonnegative capacities indexed in E order","source_node":"source in V","sink_node":"sink in V, distinct from source","num_cities":"frozen city count"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in E","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= edge_capacities[i,j] for each (i,j) in E","sum(flow[v,j]) - sum(flow[i,v]) = throughput if v=source_node, -throughput if v=sink_node, otherwise 0, for each v in V"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    edge_capacities = list(params["edge_capacities"])

    cities = list(range(num_cities))
    edges = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
        and (origin, destination) not in {(1, 3), (2, 3)}
    ]

    if source_node not in cities or sink_node not in cities:
        raise ValueError("Source and sink must belong to the city set.")
    if source_node == sink_node:
        raise ValueError("Source and sink must be distinct.")
    if len(edge_capacities) != len(edges):
        raise ValueError("Capacity count must match the ordered edge set.")

    capacities = dict(zip(edges, edge_capacities))
    outgoing = {
        city: [edge for edge in edges if edge[0] == city]
        for city in cities
    }
    incoming = {
        city: [edge for edge in edges if edge[1] == city]
        for city in cities
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.capacity = pyo.Param(
        model.edges,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(model, origin, destination):
        return (
            model.flow[origin, destination]
            <= model.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.edges, rule=capacity_rule
    )

    def balance_rule(model, city):
        net_outflow = (
            pyo.quicksum(model.flow[edge] for edge in outgoing[city])
            - pyo.quicksum(model.flow[edge] for edge in incoming[city])
        )
        if city == source_node:
            return net_outflow == model.throughput
        if city == sink_node:
            return net_outflow == -model.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )
    model.total_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}