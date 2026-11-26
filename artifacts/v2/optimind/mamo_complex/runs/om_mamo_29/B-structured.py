# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N : i != j}","T":"N \\ {0,8}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_to_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0,"indices":"A"}},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,k] for i in N if i != k) = sum(flow[k,j] for j in N if j != k) for every k in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j in N if j != 0) - sum(flow[i,0] for i in N if i != 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.stations = pyo.RangeSet(0, 8)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.stations
            for j in model.stations
            if i != j
        ],
    )
    model.transit_stations = pyo.Set(initialize=range(1, 8))

    model.pipeline_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_to_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(model, i, j):
        return model.flow[i, j] <= model.pipeline_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(model, k):
        return (
            sum(
                model.flow[i, k]
                for i in model.stations
                if i != k
            )
            == sum(
                model.flow[k, j]
                for j in model.stations
                if j != k
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_stations, rule=conservation_rule
    )

    model.max_flow_objective = pyo.Objective(
        expr=(
            sum(
                model.flow[0, j]
                for j in model.stations
                if j != 0
            )
            - sum(
                model.flow[i, 0]
                for i in model.stations
                if i != 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Unexpected solver errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}