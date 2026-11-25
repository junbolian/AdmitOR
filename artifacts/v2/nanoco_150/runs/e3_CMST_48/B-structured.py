# IR: {"sets":{"V":"{0,...,11}","S":"{1,...,11}","A":"{(i,j): i in V, j in S, i != j}"},"params":{"distance_i_j":"params['distance_i_j'] for 0 <= i < j <= 11; symmetric arc costs","C":"params['max_route_nodes']"},"variables":{"x[i,j]":"Binary for (i,j) in A; parent-to-child arc selected","f[i,j]":"NonNegativeReals for (i,j) in A; number of pickup stops supplied through arc"},"constraints":["sum(i:(i,j) in A) x[i,j] = 1 for j in S","sum(i:(i,j) in A) f[i,j] - sum(k:(j,k) in A) f[j,k] = 1 for j in S","f[i,j] <= C*x[i,j] for (i,j) in A"],"objective":"minimize sum((i,j) in A) distance[min(i,j),max(i,j)]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.vertices = pyo.RangeSet(0, 11)
    model.stops = pyo.RangeSet(1, 11)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(12)
            for destination in range(1, 12)
            if origin != destination
        ],
    )

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[
                f"distance_{min(origin, destination)}_{max(origin, destination)}"
            ]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )
    model.subtree_capacity = pyo.Param(
        initialize=params["max_route_nodes"],
        within=pyo.NonNegativeReals,
    )

    model.selected_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.stop_flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def parent_rule(instance, stop):
        return sum(
            instance.selected_arc[origin, stop]
            for origin in instance.vertices
            if origin != stop
        ) == 1

    model.one_parent = pyo.Constraint(model.stops, rule=parent_rule)

    def flow_balance_rule(instance, stop):
        incoming = sum(
            instance.stop_flow[origin, stop]
            for origin in instance.vertices
            if origin != stop
        )
        outgoing = sum(
            instance.stop_flow[stop, destination]
            for destination in instance.stops
            if destination != stop
        )
        return incoming - outgoing == 1

    model.stop_flow_balance = pyo.Constraint(
        model.stops, rule=flow_balance_rule
    )

    def capacity_rule(instance, origin, destination):
        return (
            instance.stop_flow[origin, destination]
            <= instance.subtree_capacity
            * instance.selected_arc[origin, destination]
        )

    model.arc_capacity = pyo.Constraint(model.arcs, rule=capacity_rule)

    # Unit consumption and one parent per stop enforce a rooted tree.
    # Flow on each depot arc equals its entire downstream subtree size.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[origin, destination]
            * model.selected_arc[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}