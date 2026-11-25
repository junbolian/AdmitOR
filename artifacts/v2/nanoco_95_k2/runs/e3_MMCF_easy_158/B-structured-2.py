# IR: {"sets":{"N":"range(num_nodes)","K":"range(num_commodities)","A":"range(len(arcs))"},"params":{"num_nodes":"params['num_nodes']","num_commodities":"params['num_commodities']","node_coords_x":"params['node_coords_x'][i]; geometry only","node_coords_y":"params['node_coords_y'][i]; geometry only","arcs":"params['arcs'][a]=(tail[a],head[a]); preserve order","arc_capacity":"params['arc_capacity'][a]","arc_cost":"params['arc_cost'][a]; unused in objective","commodity_demand":"params['commodity_demand'][k]","commodity_source":"params['commodity_source'][k]","commodity_sink":"params['commodity_sink'][k]"},"variables":{"flow[k,a]":"continuous, nonnegative","peak_utilization":"continuous, nonnegative"},"constraints":["For every k,i: sum(flow[k,a] for outgoing arcs a)-sum(flow[k,a] for incoming arcs a)=commodity_demand[k]*(1{i=commodity_source[k]}-1{i=commodity_sink[k]}).","For every a: sum_k flow[k,a] <= arc_capacity[a].","For every a: sum_k flow[k,a] <= arc_capacity[a]*peak_utilization."],"objective":"Minimize peak_utilization."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]
    arcs = tuple(tuple(arc) for arc in params["arcs"])
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.K = pyo.Set(initialize=range(num_commodities), ordered=True)
    model.A = pyo.Set(initialize=range(len(arcs)), ordered=True)

    model.node_coords_x = pyo.Param(
        model.N,
        initialize={i: node_coords_x[i] for i in model.N},
        within=pyo.Reals,
    )
    model.node_coords_y = pyo.Param(
        model.N,
        initialize={i: node_coords_y[i] for i in model.N},
        within=pyo.Reals,
    )
    model.arc_tail = pyo.Param(
        model.A,
        initialize={a: arcs[a][0] for a in model.A},
        within=model.N,
    )
    model.arc_head = pyo.Param(
        model.A,
        initialize={a: arcs[a][1] for a in model.A},
        within=model.N,
    )
    model.arc_capacity = pyo.Param(
        model.A,
        initialize={a: arc_capacity[a] for a in model.A},
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.A,
        initialize={a: arc_cost[a] for a in model.A},
        within=pyo.Reals,
    )
    model.commodity_demand = pyo.Param(
        model.K,
        initialize={k: commodity_demand[k] for k in model.K},
        within=pyo.NonNegativeReals,
    )
    model.commodity_source = pyo.Param(
        model.K,
        initialize={k: commodity_source[k] for k in model.K},
        within=model.N,
    )
    model.commodity_sink = pyo.Param(
        model.K,
        initialize={k: commodity_sink[k] for k in model.K},
        within=model.N,
    )

    outgoing = {i: [] for i in model.N}
    incoming = {i: [] for i in model.N}
    for a, (tail, head) in enumerate(arcs):
        outgoing[tail].append(a)
        incoming[head].append(a)

    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)
    model.peak_utilization = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(network, k, i):
        net_outflow = (
            pyo.quicksum(network.flow[k, a] for a in outgoing[i])
            - pyo.quicksum(network.flow[k, a] for a in incoming[i])
        )
        supply = network.commodity_demand[k] * (
            int(i == pyo.value(network.commodity_source[k]))
            - int(i == pyo.value(network.commodity_sink[k]))
        )
        return supply, net_outflow, supply

    model.flow_balance = pyo.Constraint(model.K, model.N, rule=balance_rule)

    def capacity_rule(network, a):
        return (
            pyo.quicksum(network.flow[k, a] for k in network.K)
            <= network.arc_capacity[a]
        )

    model.capacity_limit = pyo.Constraint(model.A, rule=capacity_rule)

    def utilization_rule(network, a):
        return (
            pyo.quicksum(network.flow[k, a] for k in network.K)
            <= network.arc_capacity[a] * network.peak_utilization
        )

    model.utilization_limit = pyo.Constraint(model.A, rule=utilization_rule)

    model.utilization_objective = pyo.Objective(
        expr=model.peak_utilization,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.utilization_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}