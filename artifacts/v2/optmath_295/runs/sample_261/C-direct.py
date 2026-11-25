import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_per_serving = params["cost_per_serving"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    volume_per_serving = params["volume_per_serving"]
    total_volume_capacity = params["total_volume_capacity"]

    # Nutrient content matrix: nutrient_content[i][j] = units of nutrient j per serving of food i
    # Derived from problem specification (structural data, not a named param)
    nutrient_content = [
        [62, 55, 47, 48, 43, 39, 44, 41, 42],  # Food_0
        [45, 64, 53, 54, 49, 45, 50, 47, 48],  # Food_1
        [50, 46, 62, 51, 46, 42, 47, 44, 45],  # Food_2
        [48, 54, 46, 63, 48, 44, 49, 46, 47],  # Food_3
        [44, 50, 54, 47, 61, 40, 45, 42, 43],  # Food_4
        [40, 46, 42, 50, 44, 58, 41, 38, 39],  # Food_5
        [45, 51, 47, 55, 49, 42, 62, 43, 44],  # Food_6
        [42, 48, 44, 52, 46, 39, 44, 60, 41],  # Food_7
        [43, 49, 45, 53, 47, 40, 45, 42, 61],  # Food_8
        [47, 43, 57, 44, 50, 46, 51, 48, 49],  # Food_9
        [46, 52, 48, 56, 50, 43, 48, 45, 46],  # Food_10
        [41, 47, 43, 51, 45, 61, 46, 43, 44],  # Food_11
        [55, 48, 51, 46, 52, 48, 53, 50, 51],  # Food_12
        [49, 55, 50, 58, 52, 45, 50, 47, 48],  # Food_13
        [51, 44, 56, 46, 53, 49, 54, 51, 52],  # Food_14
    ]

    num_foods = len(cost_per_serving)
    num_nutrients = len(nutrient_min)

    model = gp.Model("diet_plan")
    model.setParam('OutputFlag', 0)

    x = model.addVars(num_foods, lb=0.0, name="servings")

    model.setObjective(
        gp.quicksum(cost_per_serving[i] * x[i] for i in range(num_foods)),
        GRB.MINIMIZE
    )

    for j in range(num_nutrients):
        model.addConstr(
            gp.quicksum(nutrient_content[i][j] * x[i] for i in range(num_foods)) >= nutrient_min[j],
            name=f"nutrient_min_{j}"
        )
        model.addConstr(
            gp.quicksum(nutrient_content[i][j] * x[i] for i in range(num_foods)) <= nutrient_max[j],
            name=f"nutrient_max_{j}"
        )

    model.addConstr(
        gp.quicksum(volume_per_serving[i] * x[i] for i in range(num_foods)) <= total_volume_capacity,
        name="total_volume"
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}