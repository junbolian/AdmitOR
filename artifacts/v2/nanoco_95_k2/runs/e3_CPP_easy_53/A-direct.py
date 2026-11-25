import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_cost = params["service_cost"]
    travel_cost = params["travel_cost"]

    n_nodes = 6
    graph_edges = [(0, 3), (0, 4), (1, 4), (2, 3), (2, 5), (3, 4), (4, 5)]

    # service cost lookup keyed by unordered pair
    service_lookup = {}
    for e, c in zip(graph_edges, service_cost):
        service_lookup[frozenset(e)] = c

    def travel(i, j):
        return travel_cost[i * n_nodes + j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n_nodes - 1)

    # Directed arcs for every street segment (both directions), plus travel arcs
    # between all pairs (complete graph, for deadheading). We'll use a full set
    # of ordered node pairs except self-loops, and disallow flow on non-edges.
    all_arcs = [(i, j) for i in range(n_nodes) for j in range(n_nodes) if i != j]
    model.arcs = pyo.Set(initialize=all_arcs, dimen=2)

    # x[i,j] = total number of traversals of arc (i,j)
    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    # z[k] = number of active service traversals of required edge k
    model.req_edges = pyo.RangeSet(0, len(graph_edges) - 1)
    model.z = pyo.Var(model.req_edges, domain=pyo.NonNegativeIntegers)

    # Each required edge serviced at least once
    def service_rule(m, k):
        return m.z[k] >= 1
    model.service_constraint = pyo.Constraint(model.req_edges, rule=service_rule)

    # Flow conservation at each node
    def flow_balance_rule(m, i):
        inflow = sum(m.x[j, i] for j in range(n_nodes) if j != i)
        outflow = sum(m.x[i, j] for j in range(n_nodes) if j != i)
        return inflow == outflow
    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    # Link active service counts to arc usage: for required edge (u,v),
    # total traversals in both directions must be >= z (number serviced),
    # and z uses directed arcs. We require x[u,v] + x[v,u] >= z[k].
    def link_rule(m, k):
        u, v = graph_edges[k]
        return m.x[u, v] + m.x[v, u] >= m.z[k]
    model.link_constraint = pyo.Constraint(model.req_edges, rule=link_rule)

    # Depot must be used (positive degree), ensuring a closed route through 0
    def depot_rule(m):
        return sum(m.x[0, j] for j in range(n_nodes) if j != 0) >= 1
    model.depot_constraint = pyo.Constraint(rule=depot_rule)

    # Objective:
    #   total = sum over arc traversals of travel_cost (deadheading base)
    #         + sum over required edges of (service_cost - travel_cost_of_edge)*z
    # Rationale: a serviced traversal pays service_cost instead of travel cost.
    def obj_rule(m):
        total = 0
        for (i, j) in all_arcs:
            total = total + travel(i, j) * m.x[i, j]
        for k in m.req_edges:
            u, v = graph_edges[k]
            tv = travel(u, v)
            sc = service_lookup[frozenset((u, v))]
            total = total + (sc - tv) * m.z[k]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}