import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    required_edges = params["required_edges"]
    depot_node = params["depot_node"]
    num_nodes = params["num_nodes"]
    num_required_edges = params["num_required_edges"]

    # Ensure d is a 2D list (handle both flat row-major and nested list inputs)
    if hasattr(distance_matrix[0], '__iter__'):
        d = [list(row) for row in distance_matrix]
    else:
        d = [list(distance_matrix[i * num_nodes:(i + 1) * num_nodes])
             for i in range(num_nodes)]

    model = gp.Model("rpp")
    model.Params.OutputFlag = 0

    nodes = list(range(num_nodes))

    # Variables: x[i, j] = number of times the truck traverses arc i -> j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total travel cost
    obj = gp.LinExpr()
    for i in nodes:
        for j in nodes:
            if i != j:
                obj += d[i][j] * x[i, j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow conservation: arrivals == departures at every node
    for k in nodes:
        arrivals = gp.LinExpr()
        departures = gp.LinExpr()
        for i in nodes:
            if i != k:
                arrivals += x[i, k]
                departures += x[k, i]
        model.addConstr(arrivals == departures, name=f"flow_{k}")

    # Required edges: service at least once in either direction
    for idx, edge in enumerate(required_edges):
        u, v = edge[0], edge[1]
        model.addConstr(x[u, v] + x[v, u] >= 1, name=f"req_{idx}")

    # Subtour elimination: every non-empty subset S of non-depot nodes
    # must have at least one arc leaving S (ensures single connected tour)
    non_depot = [n for n in nodes if n != depot_node]

    for r in range(1, len(non_depot) + 1):
        for subset in itertools.combinations(non_depot, r):
            S = set(subset)
            complement = set(nodes) - S
            cut = gp.LinExpr()
            for i in S:
                for j in complement:
                    cut += x[i, j]
            model.addConstr(cut >= 1)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}