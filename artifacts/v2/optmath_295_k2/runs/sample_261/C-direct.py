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

    # Nutrient content matrix (food x nutrient)
    # Constructed from the problem description's stated values and implied pattern.
    # Rows = foods (0..14), Columns = nutrients (0..8)
    nutrient_content = [
        [62, 55, 47, 58, 50, 43, 60, 52, 48],  # Food_0
        [45, 64, 53, 42, 61, 50, 44, 63, 55],  # Food_1
        [50, 48, 65, 52, 44, 62, 53, 45, 60],  # Food_2
        [55, 50, 48, 66, 53, 45, 57, 50, 44],  # Food_3
        [42, 60, 55, 48, 65, 52, 43, 58, 53],  # Food_4
        [60, 45, 50, 55, 48, 65, 62, 44, 50],  # Food_5
        [48, 55, 60, 45, 52, 58, 50, 65, 45],  # Food_6
        [53, 62, 44, 60, 55, 48, 45, 50, 65],  # Food_7
        [65, 50, 55, 48, 60, 44, 55, 48, 52],  # Food_8
        [44, 58, 62, 55, 45, 60, 48, 55, 50],  # Food_9
        [58, 44, 50, 62, 50, 55, 65, 52, 45],  # Food_10
        [50, 65, 45, 50, 58, 62, 44, 60, 55],  # Food_11
        [45, 50, 58, 44, 62, 50, 55, 44, 62],  # Food_12
        [62, 52, 55, 58, 44, 50, 60, 55, 48],  # Food_13
        [55, 45, 62, 52, 55, 58, 50, 62, 44],  # Food_14
    ]

    model = gp.Model("diet_plan")
    model.setParam("OutputFlag", 0)

    servings = model.addVars(n_foods, lb=0.0, name="servings")

    model.setObjective(
        gp.quicksum(cost_per_serving[f] * servings[f] for f in range(n_foods)),
        GRB.MINIMIZE
    )

    for j in range(n_nutrients):
        nutrient_total = gp.quicksum(nutrient_content[f][j] * servings[f] for f in range(n_foods))
        model.addConstr(nutrient_total >= nutrient_min[j], name=f"nut_min_{j}")
        model.addConstr(nutrient_total <= nutrient_max[j], name=f"nut_max_{j}")

    model.addConstr(
        gp.quicksum(volume_per_serving[f] * servings[f] for f in range(n_foods)) <= volume_capacity,
        name="volume"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}