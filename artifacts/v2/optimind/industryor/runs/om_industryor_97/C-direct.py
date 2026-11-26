import gurobipy as gp
from gurobipy import GRB

def solve(params):
    rel1 = params["reliability_component1"]  # list of length 6, index = number of spares
    rel2 = params["reliability_component2"]
    rel3 = params["reliability_component3"]
    unit_price = params["unit_price"]        # list of 3
    unit_weight = params["unit_weight"]      # list of 3
    total_budget = params["total_budget"]
    total_weight_limit = params["total_weight_limit"]

    spares_range = range(6)  # 0..5
    components = range(3)

    reliability = [rel1, rel2, rel3]

    model = gp.Model("spare_parts")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i, s] = 1 if component i has exactly s spares installed
    x = model.addVars(
        [(i, s) for i in components for s in spares_range],
        vtype=GRB.BINARY,
        name="x"
    )

    # Each component must have exactly one spare count selected
    for i in components:
        model.addConstr(
            gp.quicksum(x[i, s] for s in spares_range) == 1,
            name=f"one_spare_count_{i}"
        )

    # Budget constraint: sum over components and spares of (price * spares * x[i,s])
    model.addConstr(
        gp.quicksum(unit_price[i] * s * x[i, s] for i in components for s in spares_range)
        <= total_budget,
        name="budget"
    )

    # Weight constraint
    model.addConstr(
        gp.quicksum(unit_weight[i] * s * x[i, s] for i in components for s in spares_range)
        <= total_weight_limit,
        name="weight"
    )

    # The objective is to maximize the product of component reliabilities.
    # Since reliability values are positive and we can enumerate all combinations,
    # we linearize by introducing auxiliary variables for the product.
    # With only 3 components each having 6 options, there are 6^3 = 216 combinations.
    # We model this by introducing a variable for each combination and linking it.

    combos = [(s0, s1, s2) for s0 in spares_range for s1 in spares_range for s2 in spares_range]

    # y[s0,s1,s2] = x[0,s0] * x[1,s1] * x[2,s2]
    y = model.addVars(
        combos,
        vtype=GRB.BINARY,
        name="y"
    )

    # Linearization of triple product: y = x0 * x1 * x2
    # y <= x[0,s0], y <= x[1,s1], y <= x[2,s2], y >= x[0,s0]+x[1,s1]+x[2,s2]-2
    for (s0, s1, s2) in combos:
        model.addConstr(y[s0, s1, s2] <= x[0, s0], name=f"y_ub0_{s0}_{s1}_{s2}")
        model.addConstr(y[s0, s1, s2] <= x[1, s1], name=f"y_ub1_{s0}_{s1}_{s2}")
        model.addConstr(y[s0, s1, s2] <= x[2, s2], name=f"y_ub2_{s0}_{s1}_{s2}")
        model.addConstr(
            y[s0, s1, s2] >= x[0, s0] + x[1, s1] + x[2, s2] - 2,
            name=f"y_lb_{s0}_{s1}_{s2}"
        )

    # Exactly one combo must be selected (redundant but reinforces model)
    model.addConstr(
        gp.quicksum(y[s0, s1, s2] for (s0, s1, s2) in combos) == 1,
        name="one_combo"
    )

    # Objective: maximize system reliability = product of component reliabilities
    obj = gp.quicksum(
        rel1[s0] * rel2[s1] * rel3[s2] * y[s0, s1, s2]
        for (s0, s1, s2) in combos
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}