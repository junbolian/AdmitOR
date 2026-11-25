import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_limit = params["resource_limit"]

    profits = [381, 336, 352, 329, 349, 362, 391, 378, 354, 350,
               363, 371, 345, 358, 374, 368, 355, 342, 376, 360,
               347, 383, 339, 365, 372, 356, 348, 370, 361, 344,
               375, 353, 367, 341, 359, 373, 346, 364, 380, 357,
               343, 369, 352, 338, 381]

    resource_consumption = [0.012048, 0.012821, 0.012821, 0.013333, 0.012500,
                            0.012500, 0.012195, 0.012346, 0.012821, 0.013333,
                            0.012500, 0.012048, 0.013333, 0.012821, 0.012195,
                            0.012346, 0.012821, 0.013333, 0.012048, 0.012500,
                            0.013333, 0.012048, 0.013333, 0.012346, 0.012195,
                            0.012821, 0.013333, 0.012195, 0.012500, 0.013333,
                            0.012048, 0.012821, 0.012346, 0.013333, 0.012821,
                            0.012195, 0.013333, 0.012346, 0.012048, 0.012821,
                            0.013333, 0.012195, 0.012821, 0.013333, 0.012821]

    upper_bounds = [716, 606, 635, 580, 612, 598, 724, 689, 621, 575,
                    603, 710, 567, 625, 718, 672, 614, 559, 708, 595,
                    571, 731, 548, 663, 715, 619, 562, 707, 588, 554,
                    722, 609, 668, 541, 627, 719, 558, 661, 726, 617,
                    545, 711, 635, 532, 618]

    n_items = 45

    model = gp.Model("production")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, ub=[upper_bounds[i] for i in range(n_items)], name="x")

    model.setObjective(gp.quicksum(profits[i] * x[i] for i in range(n_items)), GRB.MAXIMIZE)

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