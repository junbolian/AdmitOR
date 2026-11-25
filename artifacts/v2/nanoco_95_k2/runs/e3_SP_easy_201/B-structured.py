# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"D":[0,1],"A":[[0,1],[0,7],[1,2],[1,7],[2,3],[2,6],[3,4],[3,5],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},"params":{"arc_costs":"real[A], supplied in listed arc order","arc_capacities":"nonnegative real[A], supplied in listed arc order","node_supplies":"real[N]","node_coordinates":"real[N,D], descriptive metadata"},"variables":{"flow":"nonnegative continuous[A]"},"constraints":["flow[i,j] <= arc_capacities[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = node_supplies[i] for i in N"],"objective":"minimize sum(arc_costs[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supplies = params["node_supplies"]
    node_coordinates = params["node_coordinates"]

    nodes = tuple(range(10))
    dimensions = (0, 1)
    arcs = (
        (0, 1),
        (0, 7),
        (1, 2),
        (1, 7),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 5),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 8),
        (5, 6),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    )

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
    model.dimensions = pyo.Set(initialize=dimensions, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_costs = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.arc_capacities = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.node_supplies = pyo.Param(
        model.nodes,
        initialize={node: node_supplies[node] for node in nodes},
        within=pyo.Reals,
    )
    model.node_coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize={
            (node, dimension): node_coordinates[node][dimension]
            for node in nodes
            for dimension in dimensions
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(current_model, origin, destination):
        return (
            current_model.flow[origin, destination]
            <= current_model.arc_capacities[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(current_model, node):
        return (
            sum(current_model.flow[arc] for arc in outgoing[node])
            - sum(current_model.flow[arc] for arc in incoming[node])
            == current_model.node_supplies[node]
        )

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_costs[arc] * model.flow[arc]
            for arc in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Appsi raises RuntimeError when it cannot load a feasible solution.
    # Assess success solely by whether the objective can be evaluated.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}