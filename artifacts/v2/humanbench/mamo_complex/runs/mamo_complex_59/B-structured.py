# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j}","T":"{1,...,7}"},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","bounds":"0 <= flow[i,j] <= capacity[i,j]"}},"constraints":["For each k in T: sum(flow[i,k] for i in N if i != k) = sum(flow[k,j] for j in N if j != k)."],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j in N if j != 0) - sum(flow[i,0] for i in N if i != 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.stations = pyo.RangeSet(0, 8)
    model.transit_stations = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(9)
            for j in range(9)
            if i != j
        ],
    )

    model.pipeline_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    def flow_bounds(network, i, j):
        return 0, network.pipeline_capacity[i, j]

    model.flow = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=flow_bounds,
    )

    def conservation_rule(network, station):
        return (
            sum(
                network.flow[i, station]
                for i in network.stations
                if i != station
            )
            == sum(
                network.flow[station, j]
                for j in network.stations
                if j != station
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.stations if j != 0)
            - sum(model.flow[i, 0] for i in model.stations if i != 0)
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}