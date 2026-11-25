import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_0_1 = params["cost_0_1"]
    cost_0_2 = params["cost_0_2"]
    cost_0_3 = params["cost_0_3"]
    cost_1_0 = params["cost_1_0"]
    cost_1_2 = params["cost_1_2"]
    cost_1_3 = params["cost_1_3"]
    cost_2_0 = params["cost_2_0"]
    cost_2_1 = params["cost_2_1"]
    cost_2_3 = params["cost_2_3"]
    cost_3_0 = params["cost_3_0"]
    cost_3_1 = params["cost_3_1"]
    cost_3_2 = params["cost_3_2"]
    position_city_0 = params["position_city_0"]
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]
    n = int(params["num_cities"])

    cities = list(range(n))

    cost = {
        (0, 1): cost_0_1, (0, 2): cost_0_2, (0, 3): cost_0_3,
        (1, 0): cost_1_0, (1, 2): cost_1_2, (1, 3): cost_1_3,
        (2, 0): cost_2_0, (2, 1): cost_2_1, (2, 3): cost_2_3,
        (3, 0): cost_3_0, (3, 1): cost_3_1, (3, 2): cost_3_2,
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Position variables for cities 1, 2, 3
    u = model.addVars([1, 2, 3], lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name="u")

    # Objective
    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"depart_{i}")

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"arrive_{j}")

    # Subtour elimination (MTZ): for i, j in {1,2,3}, i != j
    # if x[i,j] = 1 then u[j] >= u[i] + 1
    # Using big-M form: u[j] >= u[i] + 1 - n*(1 - x[i,j])
    for i in [1, 2, 3]:
        for j in [1, 2, 3]:
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - n * (1 - x[i, j]),
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