# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j}","T":"{1,...,6}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,k] for i in N if i != k) = sum(flow[k,j] for j in N if j != k) for every k in T"],"objective":"maximize sum(flow[0,j] for j in N if j != 0) - sum(flow[i,0] for i in N if i != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 7)
    model.intermediate_cities = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.road_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i in range(8)
            for j in range(8)
            if i != j
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.road_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, city):
        incoming = sum(
            network.flow[i, city]
            for i in network.cities
            if i != city
        )
        outgoing = sum(
            network.flow[city, j]
            for j in network.cities
            if j != city
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate_cities, rule=conservation_rule
    )

    model.total_delivery = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.cities if j != 0)
            - sum(model.flow[i, 0] for i in model.cities if i != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}