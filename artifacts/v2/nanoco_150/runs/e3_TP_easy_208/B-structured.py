# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":[[0,3],[0,4],[0,5],[0,6],[1,3],[1,4],[1,5],[1,6],[2,3],[2,4],[2,5],[2,6]]},"params":{"supply":"real[N]","capacity":"nonnegative_real[A]","unit_cost":"real[A]","coords_x":"real[N], descriptive only","coords_y":"real[N], descriptive only"},"variables":{"shipped":"nonnegative_real[A]"},"constraints":["shipped[i,j] <= capacity[i,j] for each (i,j) in A","sum(shipped[n,j] for outgoing arcs) - sum(shipped[i,n] for incoming arcs) == supply[n] for each n in N"],"objective":"minimize sum(unit_cost[i,j] * shipped[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the capacitated minimum-cost transportation problem.

    Node data must be sequences indexed 0 through 6 or mappings keyed by
    those integers. Arc data must be sequences in the IR's arc order or
    mappings keyed by (origin, destination) tuples.
    """
    nodes = tuple(range(7))
    arcs = tuple(
        (origin, destination)
        for origin in range(3)
        for destination in range(3, 7)
    )

    supply_data = params["supply"]
    capacity_data = params["capacity"]
    unit_cost_data = params["unit_cost"]
    coords_x_data = params["coords_x"]
    coords_y_data = params["coords_y"]

    def arc_values(data):
        if isinstance(data, Mapping):
            return {arc: data[arc] for arc in arcs}
        if len(data) != len(arcs):
            raise ValueError("Arc sequences must contain exactly 12 values.")
        return {arc: data[position] for position, arc in enumerate(arcs)}

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.supply = pyo.Param(
        model.nodes,
        initialize={node: supply_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=arc_values(capacity_data),
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=arc_values(unit_cost_data),
        within=pyo.Reals,
    )
    model.coords_x = pyo.Param(
        model.nodes,
        initialize={node: coords_x_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.coords_y = pyo.Param(
        model.nodes,
        initialize={node: coords_y_data[node] for node in nodes},
        within=pyo.Reals,
    )

    model.shipped = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.shipped[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, node):
        return (
            sum(network.shipped[arc] for arc in outgoing[node])
            - sum(network.shipped[arc] for arc in incoming[node])
            == network.supply[node]
        )

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[arc] * model.shipped[arc]
            for arc in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}