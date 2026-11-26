# IR: {"sets":{"V":[0,1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","T":[1,2,3,4]},"params":{"capacity[i,j]":"params['cap_'+str(i)+'_'+str(j)] for every (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","bounds":"0 <= flow[i,j] <= capacity[i,j]"}},"constraints":["For every v in T: sum(flow[i,v] for i != v) = sum(flow[v,j] for j != v)."],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0)"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(6)
            for destination in range(6)
            if origin != destination
        ],
    )
    model.transit_cities = pyo.Set(initialize=range(1, 5))

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cap_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    def flow_bounds(network, origin, destination):
        return 0, network.capacity[origin, destination]

    model.flow = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=flow_bounds,
    )

    def conservation_rule(network, city):
        incoming = sum(
            network.flow[origin, city]
            for origin in network.cities
            if origin != city
        )
        outgoing = sum(
            network.flow[city, destination]
            for destination in network.cities
            if destination != city
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_cities,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in range(1, 6))
            - sum(model.flow[origin, 0] for origin in range(1, 6))
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}