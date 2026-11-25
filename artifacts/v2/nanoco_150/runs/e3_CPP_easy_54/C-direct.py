import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_costs_raw = params["edge_costs"]
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]

    num_nodes = 8
    depot = 0

    graph_edges = [(0,1),(0,3),(0,6),(1,3),(1,5),(1,6),(2,3),(2,4),(5,7)]
    required_edges = [(0,1),(0,3),(0,6),(1,3),(1,5),(1,6),(2,3),(2,4),(5,7)]

    # edge_costs may be a flat list of costs (one per edge in order) or a list of [u,v,c] triples
    edge_cost = {}
    if len(edge_costs_raw) == len(graph_edges) and not hasattr(edge_costs_raw[0], '__len__'):
        # flat list of costs in edge order
        for idx, (u, v) in enumerate(graph_edges):
            c = float(edge_costs_raw[idx])
            edge_cost[(u, v)] = c
            edge_cost[(v, u)] = c
    else:
        for entry in edge_costs_raw:
            u, v, c = int(entry[0]), int(entry[1]), float(entry[2])
            edge_cost[(u, v)] = c
            edge_cost[(v, u)] = c

    total_required_cost = sum(edge_cost[(u, v)] for (u, v) in required_edges)

    # Compute degree of each node in required_edges
    degree = [0] * num_nodes
    for (u, v) in required_edges:
        degree[u] += 1
        degree[v] += 1

    odd_nodes = [i for i in range(num_nodes) if degree[i] % 2 == 1]

    if len(odd_nodes) == 0:
        return {"objective": float(total_required_cost), "status": "optimal"}

    # Use distance_matrix directly as deadhead costs (per problem statement)
    def deadhead_cost(i, j):
        return float(distance_matrix[i][j])

    n_odd = len(odd_nodes)

    model = gp.Model("chinese_postman_matching")
    model.setParam("OutputFlag", 0)

    pairs = []
    for idx_a in range(n_odd):
        for idx_b in range(idx_a + 1, n_odd):
            pairs.append((idx_a, idx_b))

    x = {}
    for (idx_a, idx_b) in pairs:
        u = odd_nodes[idx_a]
        v = odd_nodes[idx_b]
        x[(idx_a, idx_b)] = model.addVar(
            vtype=GRB.BINARY,
            obj=deadhead_cost(u, v),
            name=f"x_{idx_a}_{idx_b}"
        )

    model.ModelSense = GRB.MINIMIZE

    for idx_a in range(n_odd):
        partners = []
        for idx_b in range(n_odd):
            if idx_a < idx_b:
                partners.append(x[(idx_a, idx_b)])
            elif idx_b < idx_a:
                partners.append(x[(idx_b, idx_a)])
        model.addConstr(gp.quicksum(partners) == 1, name=f"match_{idx_a}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        matching_cost = model.ObjVal
        total_cost = total_required_cost + matching_cost
        return {"objective": float(total_cost), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}