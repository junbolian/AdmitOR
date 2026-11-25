# IR: {"sets":{"V":"range(params['num_nodes'])","A":"{(i,j) in V*V:i!=j}","R":"params['required_edges']","T":"endpoints(R) minus {depot}"},"params":{"c":"params['distance_matrix'], row-major","depot":"params['depot_node']","n":"params['num_nodes']","r":"params['num_required_edges']","K":"|T|"},"variables":{"x[i,j]":"nonnegative integer traversal count on A","f[i,j]":"nonnegative continuous connectivity flow on A"},"constraints":["For each (u,v) in R: x[u,v]+x[v,u]>=1.","For each v in V: sum_j x[v,j]=sum_i x[i,v].","For each v in V: sum_i f[i,v]-sum_j f[v,j]=(-K if v=depot else 1 if v in T else 0).","For each (i,j) in A: f[i,j]<=K*x[i,j]."],"objective":"minimize sum_(i,j) in A c[i,j]*x[i,j]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_nodes"])
    required_count = int(params["num_required_edges"])
    depot = int(params["depot_node"])
    flat_costs = list(params["distance_matrix"])
    required_edges = [tuple(edge) for edge in params["required_edges"]]

    if n <= 0:
        raise ValueError("num_nodes must be positive.")
    if not 0 <= depot < n:
        raise ValueError("depot_node is outside the node set.")
    if len(flat_costs) != n * n:
        raise ValueError("distance_matrix must contain num_nodes squared entries.")
    if len(required_edges) != required_count:
        raise ValueError("required_edges cardinality differs from num_required_edges.")

    for edge in required_edges:
        if len(edge) != 2:
            raise ValueError("Each required edge must contain two node indices.")
        u, v = edge
        if u not in range(n) or v not in range(n) or u == v:
            raise ValueError("Required edges must join two distinct valid nodes.")

    costs = {}
    for i in range(n):
        for j in range(n):
            cost = float(flat_costs[i * n + j])
            if not math.isfinite(cost) or cost < 0:
                raise ValueError("Travel costs must be finite and nonnegative.")
            costs[i, j] = cost

    required_nodes = {node for edge in required_edges for node in edge}
    demand_nodes = required_nodes - {depot}
    flow_amount = len(demand_nodes)

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=range(n), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
        ordered=True,
    )
    model.R = pyo.Set(
        initialize=range(required_count),
        ordered=True,
    )
    model.travel_cost = pyo.Param(
        model.A,
        initialize={(i, j): costs[i, j] for i, j in model.A},
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def service_rule(current, edge_id):
        u, v = required_edges[edge_id]
        return current.x[u, v] + current.x[v, u] >= 1

    model.required_service = pyo.Constraint(model.R, rule=service_rule)

    def balance_rule(current, node):
        return (
            pyo.quicksum(current.x[node, j] for j in current.V if j != node)
            == pyo.quicksum(current.x[i, node] for i in current.V if i != node)
        )

    model.route_balance = pyo.Constraint(model.V, rule=balance_rule)

    def connectivity_rule(current, node):
        net_demand = (
            -flow_amount
            if node == depot
            else (1 if node in demand_nodes else 0)
        )
        return (
            pyo.quicksum(current.f[i, node] for i in current.V if i != node)
            - pyo.quicksum(current.f[node, j] for j in current.V if j != node)
            == net_demand
        )

    model.connectivity_balance = pyo.Constraint(
        model.V, rule=connectivity_rule
    )

    def capacity_rule(current, i, j):
        return current.f[i, j] <= flow_amount * current.x[i, j]

    model.connectivity_capacity = pyo.Constraint(
        model.A, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.travel_cost[i, j] * model.x[i, j] for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    # Flow connects every required endpoint to the depot. Balanced integer
    # traversals in that component admit a closed Euler tour. Any disconnected
    # component contains only optional travel and can be discarded without
    # increasing cost because all travel costs are nonnegative.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}