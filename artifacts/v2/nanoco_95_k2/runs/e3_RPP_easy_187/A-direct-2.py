import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read numeric parameters from the params dict
    distance_matrix = params["distance_matrix"]
    required_edges = params["required_edges"]
    depot_node = params["depot_node"]
    num_nodes = params["num_nodes"]
    num_required_edges = params["num_required_edges"]

    nodes = list(range(num_nodes))

    # Build distance lookup from the flat row-major matrix
    def dist(u, v):
        return distance_matrix[u * num_nodes + v]

    # Arc set: all ordered pairs u != v (full connected network)
    arcs = [(u, v) for u in nodes for v in nodes if u != v]

    model = pyo.ConcreteModel()

    # Decision variables: traversal count on each directed arc (integer, >= 0)
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)

    # Flow-balance (continuity) constraints: arrivals == departures at each node
    def balance_rule(m, n):
        outflow = sum(m.x[n, j] for j in nodes if j != n)
        inflow = sum(m.x[i, n] for i in nodes if i != n)
        return outflow == inflow

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # Depot must be visited (route is non-empty closed loop)
    def depot_rule(m):
        return sum(m.x[depot_node, j] for j in nodes if j != depot_node) >= 1

    model.depot_visit = pyo.Constraint(rule=depot_rule)

    # Required-edge servicing constraints: each required edge traversed at least once
    # Each required edge is an ordered pair [u, v]; service counted as traversal u->v.
    model.req_index = pyo.Set(initialize=range(num_required_edges))

    def required_rule(m, k):
        u, v = required_edges[k][0], required_edges[k][1]
        return m.x[u, v] >= 1

    model.required_service = pyo.Constraint(model.req_index, rule=required_rule)

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(dist(u, v) * m.x[u, v] for (u, v) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve with HiGHS via appsi
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}