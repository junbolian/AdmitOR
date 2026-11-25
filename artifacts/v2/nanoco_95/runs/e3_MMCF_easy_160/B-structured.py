# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"K":[0,1],"A":[[0,1],[1,0],[0,3],[3,0],[0,5],[5,0],[1,2],[2,1],[1,7],[7,1],[2,3],[3,2],[2,6],[6,2],[2,7],[7,2],[3,4],[4,3],[4,5],[5,4],[4,6],[6,4],[5,6],[6,5],[6,7],[7,6],[7,8],[8,7]]},"params":{"arc_capacities":"nonnegative vector indexed by A in listed order","arc_unit_costs":"real vector indexed by A in listed order; metadata only","commodity_supplies":"nonnegative vector indexed by K","node_coordinates_x":"real vector indexed by N; metadata only","node_coordinates_y":"real vector indexed by N; metadata only","source":{"0":3,"1":6},"sink":{"0":2,"1":1}},"variables":{"flow[k,i,j]":"nonnegative continuous","max_utilization":"nonnegative continuous"},"constraints":["For each k,n: sum outgoing flow[k,n,j] - sum incoming flow[k,i,n] = commodity_supplies[k] * (1[n=source[k]] - 1[n=sink[k]])","For each (i,j): sum_k flow[k,i,j] <= arc_capacities[i,j]","For each (i,j): sum_k flow[k,i,j] <= arc_capacities[i,j] * max_utilization"],"objective":"minimize max_utilization"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (1, 0),
        (0, 3), (3, 0),
        (0, 5), (5, 0),
        (1, 2), (2, 1),
        (1, 7), (7, 1),
        (2, 3), (3, 2),
        (2, 6), (6, 2),
        (2, 7), (7, 2),
        (3, 4), (4, 3),
        (4, 5), (5, 4),
        (4, 6), (6, 4),
        (5, 6), (6, 5),
        (6, 7), (7, 6),
        (7, 8), (8, 7),
    )
    nodes = tuple(range(9))
    commodities = tuple(range(2))

    capacities = params["arc_capacities"]
    costs = params["arc_unit_costs"]
    supplies = params["commodity_supplies"]
    coordinates_x = params["node_coordinates_x"]
    coordinates_y = params["node_coordinates_y"]

    outgoing = {
        node: tuple(head for tail, head in arcs if tail == node)
        for node in nodes
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.K = pyo.Set(initialize=commodities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_capacities = pyo.Param(
        model.A,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_unit_costs = pyo.Param(
        model.A,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.commodity_supplies = pyo.Param(
        model.K,
        initialize={key: supplies[key] for key in commodities},
        within=pyo.NonNegativeReals,
    )
    model.node_coordinates_x = pyo.Param(
        model.N,
        initialize={node: coordinates_x[node] for node in nodes},
        within=pyo.Reals,
    )
    model.node_coordinates_y = pyo.Param(
        model.N,
        initialize={node: coordinates_y[node] for node in nodes},
        within=pyo.Reals,
    )
    model.source = pyo.Param(
        model.K, initialize={0: 3, 1: 6}, within=model.N
    )
    model.sink = pyo.Param(
        model.K, initialize={0: 2, 1: 1}, within=model.N
    )

    model.flow = pyo.Var(
        model.K, model.A, domain=pyo.NonNegativeReals
    )
    model.max_utilization = pyo.Var(domain=pyo.NonNegativeReals)

    def conservation_rule(network, commodity, node):
        net_supply = network.commodity_supplies[commodity] * (
            int(node == pyo.value(network.source[commodity]))
            - int(node == pyo.value(network.sink[commodity]))
        )
        return (
            sum(
                network.flow[commodity, node, head]
                for head in outgoing[node]
            )
            - sum(
                network.flow[commodity, tail, node]
                for tail in incoming[node]
            )
            == net_supply
        )

    model.flow_conservation = pyo.Constraint(
        model.K, model.N, rule=conservation_rule
    )

    def capacity_rule(network, tail, head):
        return (
            sum(
                network.flow[commodity, tail, head]
                for commodity in network.K
            )
            <= network.arc_capacities[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.A, rule=capacity_rule
    )

    def utilization_rule(network, tail, head):
        return (
            sum(
                network.flow[commodity, tail, head]
                for commodity in network.K
            )
            <= network.arc_capacities[tail, head]
            * network.max_utilization
        )

    model.utilization_limits = pyo.Constraint(
        model.A, rule=utilization_rule
    )

    model.objective = pyo.Objective(
        expr=model.max_utilization,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}