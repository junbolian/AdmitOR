# IR: {"sets":{"N":"range(params['num_nodes'])","E":[[0,1],[0,3],[0,5],[1,2],[1,7],[2,3],[2,6],[2,7],[3,4],[4,5],[4,6],[5,6],[6,7],[7,8]],"A":"for each (i,j) in E, append (i,j), then (j,i), preserving order","K":"range(params['num_commodities'])","D":[0,1]},"params":{"num_nodes":"params['num_nodes']","node_coordinates":"params['node_coordinates'][n][d], metadata only","num_edges":"params['num_edges']","num_arcs":"params['num_arcs']","num_commodities":"params['num_commodities']","arc_capacities":"params['arc_capacities'][a] in listed arc order","arc_unit_costs":"params['arc_unit_costs'][a], metadata only","commodity_supply":"params['commodity_supply'][k]","commodity_source":"params['commodity_source'][k]","commodity_sink":"params['commodity_sink'][k]"},"variables":{"flow[k,a]":"nonnegative continuous","max_utilization":"continuous in [0,1]"},"constraints":["For every k,n: sum(flow[k,a] for arcs leaving n)-sum(flow[k,a] for arcs entering n)=commodity_supply[k]*(1[n=commodity_source[k]]-1[n=commodity_sink[k]]).","For every a: sum(flow[k,a] for k in K)<=arc_capacities[a].","For every a: sum(flow[k,a] for k in K)<=arc_capacities[a]*max_utilization."],"objective":"minimize max_utilization"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    node_coordinates = params["node_coordinates"]
    num_edges = params["num_edges"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supply = params["commodity_supply"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    edges = [
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7),
        (2, 3), (2, 6), (2, 7), (3, 4), (4, 5),
        (4, 6), (5, 6), (6, 7), (7, 8),
    ]
    arcs = [
        directed_arc
        for tail, head in edges
        for directed_arc in ((tail, head), (head, tail))
    ]

    if (
        num_nodes != 1 + max(endpoint for edge in edges for endpoint in edge)
        or num_edges != len(edges)
        or num_arcs != len(arcs)
    ):
        return {"objective": None, "status": "invalid_network_dimensions"}

    nodes = range(num_nodes)
    arc_indices = range(num_arcs)
    commodities = range(num_commodities)

    outgoing = {
        node: [a for a, (tail, head) in enumerate(arcs) if tail == node]
        for node in nodes
    }
    incoming = {
        node: [a for a, (tail, head) in enumerate(arcs) if head == node]
        for node in nodes
    }

    if any(
        commodity_source[k] not in nodes or commodity_sink[k] not in nodes
        for k in commodities
    ):
        return {"objective": None, "status": "invalid_commodity_endpoint"}

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(initialize=arc_indices, ordered=True)
    model.K = pyo.Set(initialize=commodities, ordered=True)
    model.D = pyo.Set(initialize=(0, 1), ordered=True)

    # Coordinates and costs are retained as input metadata. Neither enters
    # the stated objective or constraints.
    model.node_coordinates = pyo.Param(
        model.N,
        model.D,
        initialize=lambda mdl, node, dim: node_coordinates[node][dim],
        within=pyo.Reals,
    )
    model.arc_capacities = pyo.Param(
        model.A,
        initialize=lambda mdl, a: arc_capacities[a],
        within=pyo.NonNegativeReals,
    )
    model.arc_unit_costs = pyo.Param(
        model.A,
        initialize=lambda mdl, a: arc_unit_costs[a],
        within=pyo.Reals,
    )
    model.commodity_supply = pyo.Param(
        model.K,
        initialize=lambda mdl, k: commodity_supply[k],
        within=pyo.NonNegativeReals,
    )
    model.commodity_source = pyo.Param(
        model.K,
        initialize=lambda mdl, k: commodity_source[k],
        within=model.N,
    )
    model.commodity_sink = pyo.Param(
        model.K,
        initialize=lambda mdl, k: commodity_sink[k],
        within=model.N,
    )

    # Commodity indices follow the zero-based order of the input arrays.
    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)
    model.max_utilization = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 1))

    def flow_conservation_rule(mdl, k, node):
        source = pyo.value(mdl.commodity_source[k])
        sink = pyo.value(mdl.commodity_sink[k])
        net_supply = mdl.commodity_supply[k] * (
            int(node == source) - int(node == sink)
        )
        return (
            sum(mdl.flow[k, a] for a in outgoing[node])
            - sum(mdl.flow[k, a] for a in incoming[node])
            == net_supply
        )

    model.flow_conservation = pyo.Constraint(
        model.K, model.N, rule=flow_conservation_rule
    )

    def capacity_rule(mdl, a):
        return (
            sum(mdl.flow[k, a] for k in mdl.K)
            <= mdl.arc_capacities[a]
        )

    model.arc_capacity_limits = pyo.Constraint(model.A, rule=capacity_rule)

    def utilization_rule(mdl, a):
        return (
            sum(mdl.flow[k, a] for k in mdl.K)
            <= mdl.arc_capacities[a] * mdl.max_utilization
        )

    model.utilization_limits = pyo.Constraint(model.A, rule=utilization_rule)

    model.objective = pyo.Objective(
        expr=model.max_utilization,
        sense=pyo.minimize,
    )

    # Appsi raises RuntimeError when it cannot load a feasible solution.
    # The exception handler is scoped solely to the solver invocation.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}