import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_limit = params["resource_limit"]

    profits = [
        381, 336, 352, 358, 370, 362, 345, 375, 368, 355,
        342, 378, 365, 349, 372, 360, 338, 382, 356, 371,
        347, 363, 374, 341, 369, 358, 376, 353, 367, 344,
        373, 361, 350, 379, 364, 346, 370, 357, 343, 377,
        366, 352, 371, 348, 381
    ]

    resource_consumption = [
        0.012048, 0.012821, 0.012500, 0.012346, 0.012658,
        0.012500, 0.012987, 0.012195, 0.012346, 0.012658,
        0.012821, 0.012048, 0.012346, 0.012658, 0.012195,
        0.012500, 0.012987, 0.012048, 0.012500, 0.012195,
        0.012821, 0.012346, 0.012195, 0.012987, 0.012346,
        0.012500, 0.012048, 0.012658, 0.012346, 0.012821,
        0.012195, 0.012500, 0.012658, 0.012048, 0.012346,
        0.012821, 0.012195, 0.012500, 0.012987, 0.012048,
        0.012346, 0.012658, 0.012195, 0.012821, 0.012821
    ]

    upper_bounds = [
        716, 606, 635, 652, 621, 643, 598, 708, 631, 614,
        589, 724, 627, 603, 715, 638, 592, 731, 619, 711,
        601, 648, 712, 585, 629, 643, 718, 609, 633, 594,
        714, 641, 605, 727, 625, 597, 710, 616, 587, 722,
        628, 635, 713, 599, 618
    ]

    n_items = 45

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, ub=[upper_bounds[i] for i in range(n_items)], name="x")

    model.setObjective(
        gp.quicksum(profits[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n_items)) <= resource_limit,
        name="resource"
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