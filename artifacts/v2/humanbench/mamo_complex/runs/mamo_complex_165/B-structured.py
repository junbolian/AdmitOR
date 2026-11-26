# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":"all ordered pairs (i,j) of distinct cities","intermediate":[1,2,3,4]},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for every arc (i,j)"},"variables":{"flow[i,j]":{"type":"NonNegativeReals","index":"arcs"}},"constraints":["flow[i,j] <= capacity[i,j] for every arc (i,j)","sum(flow[j,i] for j != i) == sum(flow[i,j] for j != i) for every intermediate city i"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate = pyo.Set(initialize=(1, 2, 3, 4), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, city):
        inflow = sum(
            network.flow[other, city]
            for other in network.cities
            if other != city
        )
        outflow = sum(
            network.flow[city, other]
            for other in network.cities
            if other != city
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, city] for city in model.cities if city != 0)
            - sum(model.flow[city, 0] for city in model.cities if city != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}