import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_per_serving = params["cost_per_serving"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    volume_capacity = params["volume_capacity"]
    volume_per_serving = params["volume_per_serving"]

    n_foods = 15
    n_nutrients = 9

    # Helper to index into params values that may be list or dict
    def get_food(d, i):
        if isinstance(d, dict):
            return d[f"food_{i}"]
        return d[i]

    def get_nutrient(d, j):
        if isinstance(d, dict):
            return d[f"nutrient_{j}"]
        return d[j]

    nutrient_content = [
        [62, 55, 47, 51, 48, 43, 58, 52, 49],  # food_0
        [45, 64, 53, 56, 42, 38, 61, 44, 57],  # food_1
        [53, 48, 62, 44, 59, 51, 46, 63, 55],  # food_2
        [41, 57, 49, 63, 55, 47, 52, 48, 61],  # food_3
        [67, 43, 58, 52, 46, 61, 49, 55, 44],  # food_4
        [49, 61, 44, 57, 53, 48, 63, 46, 52],  # food_5
        [55, 46, 63, 48, 61, 54, 44, 57, 50],  # food_6
        [43, 59, 51, 46, 58, 44, 55, 61, 48],  # food_7
        [58, 44, 57, 61, 43, 55, 48, 46, 63],  # food_8
        [46, 62, 55, 49, 57, 63, 51, 44, 58],  # food_9
        [61, 50, 44, 58, 52, 46, 57, 63, 47],  # food_10
        [48, 56, 61, 43, 49, 57, 44, 52, 65],  # food_11
        [54, 47, 50, 65, 44, 52, 61, 49, 46],  # food_12
        [44, 63, 48, 54, 61, 49, 46, 58, 53],  # food_13
        [57, 51, 46, 48, 63, 55, 59, 44, 61],  # food_14
    ]

    model = gp.Model("diet_plan")
    model.setParam("OutputFlag", 0)

    servings = model.addVars(n_foods, lb=0.0, name="servings")

    model.setObjective(
        gp.quicksum(get_food(cost_per_serving, i) * servings[i] for i in range(n_foods)),
        GRB.MINIMIZE
    )

    for j in range(n_nutrients):
        nutrient_total = gp.quicksum(nutrient_content[i][j] * servings[i] for i in range(n_foods))
        model.addConstr(nutrient_total >= get_nutrient(nutrient_min, j), name=f"nutrient_min_{j}")
        model.addConstr(nutrient_total <= get_nutrient(nutrient_max, j), name=f"nutrient_max_{j}")

    model.addConstr(
        gp.quicksum(get_food(volume_per_serving, i) * servings[i] for i in range(n_foods)) <= volume_capacity,
        name="volume"
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