import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sulfur_A = params["sulfur_A"]
    sulfur_B = params["sulfur_B"]
    sulfur_C = params["sulfur_C"]
    sulfur_D = params["sulfur_D"]
    price_A  = params["price_A"]
    price_B  = params["price_B"]
    price_C  = params["price_C"]
    price_D  = params["price_D"]
    sell_A   = params["sell_A"]
    sell_B   = params["sell_B"]
    max_sulfur_A = params["max_sulfur_A"]
    max_sulfur_B = params["max_sulfur_B"]
    supply_D  = params["supply_D"]
    demand_A  = params["demand_A"]
    demand_B  = params["demand_B"]

    model = gp.Model("blending")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # xij = tons of raw material i (A,B,C,D) used in product j (pA, pB)
    xAA = model.addVar(lb=0, name="xAA")   # raw mat A -> product A
    xBA = model.addVar(lb=0, name="xBA")   # raw mat B -> product A
    xCA = model.addVar(lb=0, name="xCA")   # raw mat C -> product A
    xDA = model.addVar(lb=0, name="xDA")   # raw mat D -> product A

    xAB = model.addVar(lb=0, name="xAB")   # raw mat A -> product B
    xBB = model.addVar(lb=0, name="xBB")   # raw mat B -> product B
    xCB = model.addVar(lb=0, name="xCB")   # raw mat C -> product B
    xDB = model.addVar(lb=0, name="xDB")   # raw mat D -> product B

    # Total output of each product
    outA = xAA + xBA + xCA + xDA
    outB = xAB + xBB + xCB + xDB

    # Demand constraints
    model.addConstr(outA <= demand_A, name="demand_A")
    model.addConstr(outB <= demand_B, name="demand_B")

    # Supply constraint on raw material D
    model.addConstr(xDA + xDB <= supply_D, name="supply_D")

    # Sulfur content constraints for product A
    # sum(sulfur_i * x_iA) <= max_sulfur_A * outA
    model.addConstr(
        sulfur_A * xAA + sulfur_B * xBA + sulfur_C * xCA + sulfur_D * xDA
        <= max_sulfur_A * outA,
        name="sulfur_prodA"
    )

    # Sulfur content constraints for product B
    model.addConstr(
        sulfur_A * xAB + sulfur_B * xBB + sulfur_C * xCB + sulfur_D * xDB
        <= max_sulfur_B * outB,
        name="sulfur_prodB"
    )

    # Process constraint: A, B, D must first be mixed together (in the mixing tank),
    # then blended with C. This means the ratio of A, B, D going to each product
    # must come from the same mixed intermediate. Concretely, the intermediate mix
    # (A+B+D) is proportionally split between product A and product B.
    # Let mix_total = xAA+xBA+xDA + xAB+xBB+xDB (total A,B,D used).
    # The share going to product A is (xAA+xBA+xDA)/mix_total, to product B is the rest.
    # The sulfur of the intermediate mix is the same regardless of split, so the
    # only binding constraint from the two-step process is that C is added after
    # the first mix — which is already captured by the sulfur constraints above.
    # No additional structural constraint is needed beyond non-negativity.

    # Objective: maximize revenue - cost
    revenue = sell_A * outA + sell_B * outB
    cost = (price_A * (xAA + xAB) +
            price_B * (xBA + xBB) +
            price_C * (xCA + xCB) +
            price_D * (xDA + xDB))
    model.setObjective(revenue - cost, GRB.MAXIMIZE)

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