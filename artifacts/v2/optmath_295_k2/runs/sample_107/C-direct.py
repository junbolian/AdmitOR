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
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]
    num_cities = params["num_cities"]

    n = int(num_cities)
    cities = list(range(n))

    cost = {}
    cost[(0, 1)] = cost_0_1
    cost[(0, 2)] = cost_0_2
    cost[(0, 3)] = cost_0_3
    cost[(1, 0)] = cost_1_0
    cost[(1, 2)] = cost_1_2
    cost[(1, 3)] = cost_1_3
    cost[(2, 0)] = cost_2_0
    cost[(2, 1)] = cost_2_1
    cost[(2, 3)] = cost_2_3
    cost[(3, 0)] = cost_3_0
    cost[(3, 1)] = cost_3_1
    cost[(3, 2)] = cost_3_2

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # Binary route variables x[i,j] = 1 if route from i to j is taken
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables for MTZ subtour elimination
    # City 0 is fixed; cities 1,2,3 have bounded positions
    pos = {}
    pos[0] = model.addVar(lb=position_city_0, ub=position_city_0, vtype=GRB.CONTINUOUS, name="pos_0")
    for i in [1, 2, 3]:
        pos[i] = model.addVar(lb=position_lower_bound, ub=position_upper_bound, vtype=GRB.CONTINUOUS, name=f"pos_{i}")

    model.update()

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints for pairs excluding city 0
    big_m = position_upper_bound - position_lower_bound + 1
    for i in [1, 2, 3]:
        for j in [1, 2, 3]:
            if i != j:
                model.addConstr(
                    pos[j] >= pos[i] + 1 - big_m * (1 - x[(i, j)]),
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