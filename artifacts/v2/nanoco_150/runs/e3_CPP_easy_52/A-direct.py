import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    depot = int(params["depot"])
    dist = params["distance_matrix"]
    num_required = int(params["num_required_edges"])
    edge_costs = params["edge_costs"]

    nodes = list(range(num_nodes))
    req_idx = list(range(num_required))

    # Directed copies of each required edge: (u,v) and (v,u)
    req_arcs = []
    for e in req_idx:
        u, v, c = int(edge_costs[e][0]), int(edge_costs[e][1]), float(edge_costs[e][2])
        req_arcs.append((e, u, v, c))
        req_arcs.append((e, v, u, c))

    # Feasibility check: degree parity for undirected required graph + connectivity
    deg = {i: 0 for i in nodes}
    adj = {i: set() for i in nodes}
    for e in req_idx:
        u, v = int(edge_costs[e][0]), int(edge_costs[e][1])
        deg[u] += 1
        deg[v] += 1
        adj[u].add(v)
        adj[v].add(u)

    # Connectivity among nodes touched by required edges
    touched = [i for i in nodes if deg[i] > 0]
    if touched:
        import collections
        seen = {touched[0]}
        dq = collections.deque([touched[0]])
        while dq:
            x = dq.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    dq.append(y)
        if len(seen) != len(touched):
            return {"objective": None, "status": "required_edges_disconnected"}

    odd = [i for i in nodes if deg[i] % 2 == 1]
    if len(odd) % 2 != 0:
        return {"objective": None, "status": "infeasible_parity"}

    model = pyo.ConcreteModel()

    # Variables: service arcs (0/1) for directed copies, deadhead integer on all directed node pairs
    model.x = pyo.Var([(e, u, v) for (e, u, v, c) in req_arcs], domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var([(i, j) for i in nodes for j in nodes if i != j], domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(c * m.x[(e, u, v)] for (e, u, v, c) in req_arcs) \
             + sum(float(dist[i][j]) * m.y[(i, j)] for i in nodes for j in nodes if i != j)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each required (undirected) edge serviced at least once total across both directions
    def service_rule(m, e):
        u, v = int(edge_costs[e][0]), int(edge_costs[e][1])
        return m.x[(e, u, v)] + m.x[(e, v, u)] >= 1
    model.service = pyo.Constraint(req_idx, rule=service_rule)

    # Flow conservation: total out = total in at each node
    def flow_rule(m, i):
        out_expr = sum(m.y[(i, j)] for j in nodes if j != i)
        in_expr = sum(m.y[(j, i)] for j in nodes if j != i)
        for (e, u, v, c) in req_arcs:
            if u == i:
                out_expr += m.x[(e, u, v)]
            if v == i:
                in_expr += m.x[(e, u, v)]
        return out_expr == in_expr
    model.flow = pyo.Constraint(nodes, rule=flow_rule)

    # At depot require at least one departure (closed route must be non-trivial if required edges exist)
    if num_required > 0:
        def depot_out_rule(m):
            expr = sum(m.y[(depot, j)] for j in nodes if j != depot)
            for (e, u, v, c) in req_arcs:
                if u == depot:
                    expr += m.x[(e, u, v)]
            return expr >= 1
        model.depot_out = pyo.Constraint(rule=depot_out_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}