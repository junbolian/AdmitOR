import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build cost matrix from params
    n = 4
    cities = [1, 2, 3, 4]
    
    cost = {}
    cost[(1,2)] = params["travel_cost_c1_c2"]
    cost[(1,3)] = params["travel_cost_c1_c3"]
    cost[(1,4)] = params["travel_cost_c1_c4"]
    cost[(2,1)] = params["travel_cost_c2_c1"]
    cost[(2,3)] = params["travel_cost_c2_c3"]
    cost[(2,4)] = params["travel_cost_c2_c4"]
    cost[(3,1)] = params["travel_cost_c3_c1"]
    cost[(3,2)] = params["travel_cost_c3_c2"]
    cost[(3,4)] = params["travel_cost_c3_c4"]
    cost[(4,1)] = params["travel_cost_c4_c1"]
    cost[(4,2)] = params["travel_cost_c4_c2"]
    cost[(4,3)] = params["travel_cost_c4_c3"]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if arc (i->j) is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Auxiliary variables for MTZ subtour elimination: u[i] position in tour
    u = model.addVars(cities, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination constraints
    # Fix position of city 1 to break symmetry
    model.addConstr(u[1] == 0, name="u1_fix")
    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}