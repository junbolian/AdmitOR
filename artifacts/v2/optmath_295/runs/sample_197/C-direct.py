import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {}
    cost[(0,1)] = params["cost_0_1"]
    cost[(0,2)] = params["cost_0_2"]
    cost[(0,3)] = params["cost_0_3"]
    cost[(1,0)] = params["cost_1_0"]
    cost[(1,2)] = params["cost_1_2"]
    cost[(1,3)] = params["cost_1_3"]
    cost[(2,0)] = params["cost_2_0"]
    cost[(2,1)] = params["cost_2_1"]
    cost[(2,3)] = params["cost_2_3"]
    cost[(3,0)] = params["cost_3_0"]
    cost[(3,1)] = params["cost_3_1"]
    cost[(3,2)] = params["cost_3_2"]

    n = int(params["num_cities"])
    city0_pos = params["city0_position"]
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]

    cities = list(range(n))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Position variables for MTZ subtour elimination
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # Objective
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    # Each city has exactly one outgoing route
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"out_{i}")

    # Each city has exactly one incoming route
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"in_{j}")

    # Fix City 0 position
    model.addConstr(u[0] == city0_pos, name="pos_city0")

    # Bounds on positions of Cities 1, 2, 3
    for i in range(1, n):
        model.addConstr(u[i] >= pos_lb, name=f"pos_lb_{i}")
        model.addConstr(u[i] <= pos_ub, name=f"pos_ub_{i}")

    # MTZ subtour elimination: if x[i,j]=1 and j != 0, then u[i] < u[j]
    big_m = n
    for i in cities:
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + big_m * x[i, j] <= big_m - 1,
                                name=f"mtz_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}