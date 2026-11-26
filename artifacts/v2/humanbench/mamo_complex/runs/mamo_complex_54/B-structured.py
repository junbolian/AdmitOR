# IR: {"sets":{"V":[0,1,2,3,4,5],"A":"all ordered pairs (i,j) in V x V with i != j, except (0,3)"},"params":{"capacity[i,j]":{"index":"A","source":"params[f'capacity_{i}_{j}']","type":"nonnegative real","units":"thousands of vehicles/hour"}},"variables":{"flow[i,j]":{"index":"A","type":"nonnegative continuous"},"total_flow":{"type":"nonnegative continuous"}},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = total_flow if i=0, -total_flow if i=5, and 0 otherwise, for every i in V"],"objective":{"sense":"maximize","expression":"total_flow","units":"thousands of vehicles/hour"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination and (origin, destination) != (0, 3)
    )

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(
        initialize=arcs,
        dimen=2,
        within=model.cities * model.cities,
        ordered=True,
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"capacity_{origin}_{destination}"]
            for origin, destination in arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def highway_capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.capacity[origin, destination]
        )

    model.highway_capacity = pyo.Constraint(
        model.arcs,
        rule=highway_capacity_rule,
    )

    def flow_balance_rule(instance, city):
        outgoing = sum(
            instance.flow[origin, destination]
            for origin, destination in arcs
            if origin == city
        )
        incoming = sum(
            instance.flow[origin, destination]
            for origin, destination in arcs
            if destination == city
        )

        if city == 0:
            return outgoing - incoming == instance.total_flow
        if city == 5:
            return outgoing - incoming == -instance.total_flow
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.cities,
        rule=flow_balance_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}