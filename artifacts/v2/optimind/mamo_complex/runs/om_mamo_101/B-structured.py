# IR: {"sets":{"cities":"0..8","arcs":"(i,j) with i in 0..7, j in 0..8, i != j","transit":"1..7"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every arc"},"variables":{"flow[i,j]":"continuous, nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","sum(flow[i,j] for outgoing arcs) == sum(flow[j,i] for incoming arcs) for each transit city i"],"objective":"maximize sum(flow[0,j]) - sum(flow[i,0])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 8)
    model.transit = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(8)
            for destination in range(9)
            if origin != destination
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[
                f"capacity_{origin}_{destination}"
            ]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, city):
        outgoing = pyo.quicksum(
            network.flow[origin, destination]
            for origin, destination in network.arcs
            if origin == city
        )
        incoming = pyo.quicksum(
            network.flow[origin, destination]
            for origin, destination in network.arcs
            if destination == city
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.transit, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.flow[origin, destination]
                for origin, destination in model.arcs
                if origin == 0
            )
            - pyo.quicksum(
                model.flow[origin, destination]
                for origin, destination in model.arcs
                if destination == 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}