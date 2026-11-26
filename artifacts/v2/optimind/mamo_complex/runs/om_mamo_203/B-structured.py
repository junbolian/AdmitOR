# IR: {"sets":{"cities":"range(params['num_cities']); size frozen at 9","destinations":[[1,2,3,4,5,6,7,8],[0,2,4,5,6,7,8],[0,1,4,5,6,7,8],[0,1,2,4,5,6,7,8],[0,1,2,3,5,6,7,8],[0,1,2,3,4,6,7,8],[0,1,2,3,4,5,7,8],[0,1,2,3,4,5,6,8],[0,1,2,3,4,5,6,7]],"arcs":"(origin,destination) in row order from destinations","intermediate":"cities excluding source 0 and sink 8"},"params":{"num_cities":"params['num_cities']","capacity":"params['edge_capacities'], flat sequence aligned with arcs"},"variables":{"flow[origin,destination]":"nonnegative continuous tons"},"constraints":["flow[i,j] <= capacity[i,j] for every arc (i,j)","sum(flow[i,v] for incoming arcs) = sum(flow[v,j] for outgoing arcs) for every intermediate city v"],"objective":"maximize sum(flow[0,j]) - sum(flow[i,0]), the net flow leaving the warehouse"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    destinations = (
        (1, 2, 3, 4, 5, 6, 7, 8),
        (0, 2, 4, 5, 6, 7, 8),
        (0, 1, 4, 5, 6, 7, 8),
        (0, 1, 2, 4, 5, 6, 7, 8),
        (0, 1, 2, 3, 5, 6, 7, 8),
        (0, 1, 2, 3, 4, 6, 7, 8),
        (0, 1, 2, 3, 4, 5, 7, 8),
        (0, 1, 2, 3, 4, 5, 6, 8),
        (0, 1, 2, 3, 4, 5, 6, 7),
    )

    num_cities = params["num_cities"]
    edge_capacities = list(params["edge_capacities"])

    if num_cities != len(destinations):
        raise ValueError("num_cities must match the frozen network size.")

    arcs = [
        (origin, destination)
        for origin, row in enumerate(destinations)
        for destination in row
    ]
    if len(edge_capacities) != len(arcs):
        raise ValueError(
            "edge_capacities must contain one value per listed directed route."
        )

    cities = range(len(destinations))
    source = 0
    sink = len(destinations) - 1
    incoming = {
        city: [origin for origin, destination in arcs if destination == city]
        for city in cities
    }
    outgoing = {
        city: [destination for origin, destination in arcs if origin == city]
        for city in cities
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, num_cities - 1)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_cities = pyo.Set(
        initialize=[city for city in cities if city not in (source, sink)]
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, edge_capacities)),
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, city):
        return (
            sum(network.flow[origin, city] for origin in incoming[city])
            == sum(
                network.flow[city, destination]
                for destination in outgoing[city]
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_cities, rule=conservation_rule
    )
    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[source, destination] for destination in outgoing[source])
            - sum(model.flow[origin, source] for origin in incoming[source])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}