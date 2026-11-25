import gurobipy as gp
from gurobipy import GRB
from itertools import combinations


def solve(params):
    available_edges = params["available_edges"]
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    num_nodes = len(coords)
    edges = [(min(a, b), max(a, b)) for a, b in available_edges]
    edges = list(dict.fromkeys(edges))

    model = gp.Model("irrigation_spanning_tree")
    model.Params.OutputFlag = 0

    x = {}
    for e in edges:
        x[e] = model.addVar(vtype=GRB.BINARY, name=f"x_{e[0]}_{e[1]}")

    y = {}
    for i in range(num_nodes):
        y[i] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}")

    model.update()

    incident_edges = {i: [] for i in range(num_nodes)}
    for e in edges:
        incident_edges[e[0]].append(x[e])
        incident_edges[e[1]].append(x[e])

    for i in range(num_nodes):
        d_i = gp.quicksum(incident_edges[i])
        # If y_i = 1 then degree of i is at most 1 (i.e., leaf).
        model.addConstr(d_i <= 1 + (num_nodes - 1) * (1 - y[i]), name=f"leaf_link_{i}")

    # Spanning tree: exactly num_nodes - 1 edges.
    model.addConstr(gp.quicksum(x[e] for e in edges) == num_nodes - 1, name="edge_count")

    # Subtour (acyclicity) constraints: for every proper nonempty subset S,
    # the number of selected edges fully inside S is at most |S| - 1.
    nodes = list(range(num_nodes))
    for r in range(2, num_nodes):
        for S in combinations(nodes, r):
            Sset = set(S)
            inner = [x[e] for e in edges if e[0] in Sset and e[1] in Sset]
            if inner:
                model.addConstr(
                    gp.quicksum(inner) <= len(S) - 1,
                    name=f"sub_{'_'.join(map(str, S))}",
                )

    model.setObjective(gp.quicksum(y[i] for i in range(num_nodes)), GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}