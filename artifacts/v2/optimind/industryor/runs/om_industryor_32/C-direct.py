import math
from gurobipy import Model, GRB, quicksum


def solve(params):
    goods = ["A", "B", "C", "D", "E"]

    qty = {g: params["quantity_{}".format(g)] for g in goods}
    wt = {g: params["weight_{}".format(g)] for g in goods}
    cap = params["container_capacity"]
    min_load = params["container_min_load"]
    min_d = params["min_D_per_container"]
    ratio = params["A_requires_C_ratio"]

    total_weight = sum(qty[g] * wt[g] for g in goods)

    # Hard upper bound on the number of used containers: each used
    # container needs at least min_d units of D.
    if min_d <= 0:
        n_containers = 100  # fallback generous pool
    else:
        n_containers = int(qty["D"] // min_d)

    # Sanity: enough containers by capacity to carry the whole batch?
    min_needed = int(math.ceil(total_weight / cap)) if cap > 0 else 10**9
    if n_containers < min_needed:
        return {"objective": None, "status": "infeasible"}

    containers = list(range(n_containers))

    model = Model("container_packing")

    # Units of good g packed into container i
    x = model.addVars(containers, goods, vtype=GRB.INTEGER, lb=0,
                      ub={ (i, g): qty[g] for i in containers for g in goods },
                      name="x")
    # Container usage
    y = model.addVars(containers, vtype=GRB.BINARY, name="y")

    # All goods must be shipped
    model.addConstrs(
        (quicksum(x[i, g] for i in containers) == qty[g] for g in goods),
        name="ship_all")

    # No packing into unused containers
    model.addConstrs(
        (x[i, g] <= qty[g] * y[i] for i in containers for g in goods),
        name="link_xy")

    # Weight limits per container
    model.addConstrs(
        (quicksum(wt[g] * x[i, g] for g in goods) <= cap * y[i]
         for i in containers),
        name="max_weight")
    model.addConstrs(
        (quicksum(wt[g] * x[i, g] for g in goods) >= min_load * y[i]
         for i in containers),
        name="min_weight")

    # Minimum units of D in every used container
    model.addConstrs(
        (x[i, "D"] >= min_d * y[i] for i in containers),
        name="min_D")

    # Every unit of A requires at least `ratio` units of C in the same container
    model.addConstrs(
        (x[i, "C"] >= ratio * x[i, "A"] for i in containers),
        name="A_needs_C")

    model.setObjective(quicksum(y[i] for i in containers), GRB.MINIMIZE)

    model.setParam("OutputFlag", 0)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD, GRB.UNBOUNDED):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "not_solved"}