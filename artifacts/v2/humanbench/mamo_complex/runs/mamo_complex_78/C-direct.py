import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_AB = params["cost_AB"]
    cost_AC = params["cost_AC"]
    cost_AD = params["cost_AD"]
    cost_AE = params["cost_AE"]
    cost_AF = params["cost_AF"]
    cost_BC = params["cost_BC"]
    cost_BD = params["cost_BD"]
    cost_BE = params["cost_BE"]
    cost_BF = params["cost_BF"]
    cost_CD = params["cost_CD"]
    cost_CE = params["cost_CE"]
    cost_CF = params["cost_CF"]
    cost_DE = params["cost_DE"]
    cost_DF = params["cost_DF"]
    cost_EF = params["cost_EF"]

    nodes = [0, 1, 2, 3, 4, 5]  # A=0, B=1, C=2, D=3, E=4, F=5
    n = len(nodes)

    # Build symmetric cost matrix
    cost = {}
    raw = {
        (0, 1): cost_AB, (0, 2): cost_AC, (0, 3): cost_AD,
        (0, 4): cost_AE, (0, 5): cost_AF,
        (1, 2): cost_BC, (1, 3): cost_BD, (1, 4): cost_BE, (1, 5): cost_BF,
        (2, 3): cost_CD, (2, 4): cost_CE, (2, 5): cost_CF,
        (3, 4): cost_DE, (3, 5): cost_DF,
        (4, 5): cost_EF,
    }
    for (i, j), c in raw.items():
        cost[i, j] = c
        cost[j, i] = c

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if arc i->j is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each node has exactly one outgoing arc
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"out_{i}")

    # Each node has exactly one incoming arc
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"in_{j}")

    # Subtour elimination via callback (lazy constraints)
    model.Params.lazyConstraints = 1

    def subtour_elim(model, where):
        if where == GRB.Callback.MIPSOL:
            x_val = model.cbGetSolution(model._x)
            # Build adjacency list from solution
            adj = {i: [] for i in nodes}
            for (i, j) in arcs:
                if x_val[i, j] > 0.5:
                    adj[i].append(j)
            # Find all tours/subtours
            visited = set()
            tours = []
            for start in nodes:
                if start not in visited:
                    tour = []
                    cur = start
                    while cur not in visited:
                        visited.add(cur)
                        tour.append(cur)
                        if adj[cur]:
                            cur = adj[cur][0]
                        else:
                            break
                    tours.append(tour)
            # Add subtour elimination constraints for subtours
            for tour in tours:
                if len(tour) < n:
                    s = set(tour)
                    model.cbLazy(
                        gp.quicksum(model._x[i, j] for i in s for j in s if i != j)
                        <= len(s) - 1
                    )

    model._x = x
    model.optimize(subtour_elim)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}