# IR: {"sets":{"N":"nodes 0..6; depot 0","E":"fixed undirected edges [(0,1),(0,2),(1,3),(2,6),(3,4),(3,5),(3,6),(5,6)]","R":"both orientations of E","A":"all ordered pairs of distinct nodes"},"params":{"node_coords":"coordinate pairs; descriptive metadata only","num_graph_edges":"frozen size of E","num_required_edges":"frozen number of required edges, identical to E","service_costs":"nonnegative service costs in E order","travel_cost_matrix":"nonnegative directed deadhead costs on A"},"variables":{"service[R]":"Binary; chosen service orientation","deadhead[A]":"NonNegativeIntegers; nonproductive traversal counts","connection_flow[A]":"NonNegativeReals; auxiliary connectivity flow"},"constraints":["For each {i,j} in E: service[i,j]+service[j,i]=1; additional traversals are deadheading.","At every node: total incoming service and deadhead traversals equal total outgoing traversals.","For each (i,j) in A: connection_flow[i,j]<=(|N|-1)*(deadhead[i,j]+service[i,j] if (i,j) is in R, otherwise deadhead[i,j]).","Depot sends |N|-1 net units of connection flow; every other node receives one net unit."],"objective":"Minimize sum over E of service_cost[e]*(service[i,j]+service[j,i]) plus sum over A of travel_cost_matrix[i][j]*deadhead[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_coords = params["node_coords"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    service_costs = params["service_costs"]
    travel_cost_matrix = params["travel_cost_matrix"]

    nodes = tuple(range(7))
    depot = 0
    graph_edges = (
        (0, 1),
        (0, 2),
        (1, 3),
        (2, 6),
        (3, 4),
        (3, 5),
        (3, 6),
        (5, 6),
    )

    # These sizes are frozen by the problem's explicitly specified topology.
    if (
        num_graph_edges != len(graph_edges)
        or num_required_edges != len(graph_edges)
    ):
        return {"objective": None, "status": "invalid_structure"}

    if (
        len(node_coords) != len(nodes)
        or any(len(node_coords[node]) != 2 for node in nodes)
        or len(service_costs) != num_required_edges
        or len(travel_cost_matrix) != len(nodes)
        or any(
            len(travel_cost_matrix[node]) != len(nodes)
            for node in nodes
        )
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    service_arcs = tuple(
        arc
        for start, end in graph_edges
        for arc in ((start, end), (end, start))
    )
    service_arc_set = frozenset(service_arcs)
    travel_arcs = tuple(
        (start, end)
        for start in nodes
        for end in nodes
        if start != end
    )
    flow_capacity = len(nodes) - 1

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=graph_edges, ordered=True
    )
    model.service_arcs = pyo.Set(
        dimen=2, initialize=service_arcs, ordered=True
    )
    model.travel_arcs = pyo.Set(
        dimen=2, initialize=travel_arcs, ordered=True
    )

    # Coordinates describe the map; the supplied matrix determines travel cost.
    model.coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize={
            (node, axis): node_coords[node][axis]
            for node in nodes
            for axis in (0, 1)
        },
        within=pyo.Reals,
    )
    model.service_cost = pyo.Param(
        model.required_edges,
        initialize={
            edge: service_costs[position]
            for position, edge in enumerate(graph_edges)
        },
        within=pyo.NonNegativeReals,
    )
    model.travel_cost = pyo.Param(
        model.travel_arcs,
        initialize={
            (start, end): travel_cost_matrix[start][end]
            for start, end in travel_arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.service = pyo.Var(model.service_arcs, domain=pyo.Binary)
    model.deadhead = pyo.Var(
        model.travel_arcs, domain=pyo.NonNegativeIntegers
    )
    model.connection_flow = pyo.Var(
        model.travel_arcs, domain=pyo.NonNegativeReals
    )

    def traversal_count(start, end):
        count = model.deadhead[start, end]
        if (start, end) in service_arc_set:
            count = count + model.service[start, end]
        return count

    # Each segment needs one service traversal. Any later use is nonproductive.
    def service_requirement_rule(block, start, end):
        return (
            block.service[start, end] + block.service[end, start] == 1
        )

    model.service_requirement = pyo.Constraint(
        model.required_edges, rule=service_requirement_rule
    )

    def route_balance_rule(block, node):
        return sum(
            traversal_count(node, neighbor)
            for neighbor in nodes
            if neighbor != node
        ) == sum(
            traversal_count(neighbor, node)
            for neighbor in nodes
            if neighbor != node
        )

    model.route_balance = pyo.Constraint(
        model.nodes, rule=route_balance_rule
    )

    def connection_capacity_rule(block, start, end):
        return block.connection_flow[start, end] <= (
            flow_capacity * traversal_count(start, end)
        )

    model.connection_capacity = pyo.Constraint(
        model.travel_arcs, rule=connection_capacity_rule
    )

    def connection_balance_rule(block, node):
        outgoing = sum(
            block.connection_flow[node, neighbor]
            for neighbor in nodes
            if neighbor != node
        )
        incoming = sum(
            block.connection_flow[neighbor, node]
            for neighbor in nodes
            if neighbor != node
        )
        if node == depot:
            return outgoing - incoming == flow_capacity
        return incoming - outgoing == 1

    model.connection_balance = pyo.Constraint(
        model.nodes, rule=connection_balance_rule
    )

    # Connectivity and integer route balance ensure a single closed Euler tour.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.service_cost[start, end]
            * (model.service[start, end] + model.service[end, start])
            for start, end in graph_edges
        )
        + sum(
            model.travel_cost[start, end] * model.deadhead[start, end]
            for start, end in travel_arcs
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