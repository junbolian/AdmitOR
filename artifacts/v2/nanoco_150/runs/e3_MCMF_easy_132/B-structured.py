# IR: {"sets":{"nodes":"0..9","transit":"1..8","arcs":[[0,1],[0,6],[0,8],[1,2],[2,3],[2,7],[3,4],[4,5],[4,7],[4,8],[5,6],[6,7],[6,8],[7,8],[8,9]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for every arc","cost[i,j]":"params['cost_i_j'] for every arc","coordinates[i]":"params['coord_node_i']; descriptive metadata"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","sum incoming flow = sum outgoing flow at every transit node","stage 2: throughput = optimal stage-1 throughput"],"objective":{"priority_1":"maximize throughput = total flow entering node 9","priority_2":"minimize sum(cost[i,j] * flow[i,j]) with throughput fixed","returned_objective":"maximum throughput"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(10))
    transit_nodes = tuple(range(1, 9))
    arcs = (
        (0, 1),
        (0, 6),
        (0, 8),
        (1, 2),
        (2, 3),
        (2, 7),
        (3, 4),
        (4, 5),
        (4, 7),
        (4, 8),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
        (8, 9),
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    coordinates = {
        node: tuple(params[f"coord_node_{node}"])
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.transit_nodes = pyo.Set(initialize=transit_nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(model.arcs, initialize=capacities)
    model.shipping_cost = pyo.Param(model.arcs, initialize=costs)
    model.coordinates = pyo.Param(
        model.nodes,
        initialize=coordinates,
        within=pyo.Any,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[arc] for arc in incoming[node])
            == sum(network.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes,
        rule=conservation_rule,
    )

    model.throughput = pyo.Expression(
        expr=sum(model.flow[arc] for arc in incoming[9])
    )
    model.total_shipping_cost = pyo.Expression(
        expr=sum(
            model.shipping_cost[arc] * model.flow[arc]
            for arc in model.arcs
        )
    )

    model.throughput_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )
    model.cost_objective = pyo.Objective(
        expr=model.total_shipping_cost,
        sense=pyo.minimize,
    )
    model.cost_objective.deactivate()

    # First priority: maximize throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        maximum_throughput = float(pyo.value(model.throughput_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    # Second priority: minimize cost without reducing maximum throughput.
    model.maximum_throughput_requirement = pyo.Constraint(
        expr=model.throughput == maximum_throughput
    )
    model.throughput_objective.deactivate()
    model.cost_objective.activate()

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        # Ensure the second-stage objective is also retrievable.
        pyo.value(model.cost_objective)
        obj_val = float(pyo.value(model.throughput_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}