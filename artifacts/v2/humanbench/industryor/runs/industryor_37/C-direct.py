import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    unit_cost = params["unit_cost"]
    p1 = params["full_satisfaction_target_customer4"]
    p5_target = params["balance_satisfaction_target_customers1and3"]
    p2 = params["remaining_customers_min_satisfaction_rate"]
    p3 = params["factory3_to_customer1_min"]
    p4_weight = params["factory2_to_customer4_penalty_weight"]
    num_factories = params["num_factories"]
    num_customers = params["num_customers"]

    I = range(num_factories)
    J = range(num_customers)

    model = gp.Model("goal_programming_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: shipment from factory i to customer j
    x = model.addVars(I, J, lb=0.0, name="x")

    # --- Goal deviation variables ---

    # p1: Customer 4 (j=3) fully satisfied
    # sum_i x[i,3] + d1_neg - d1_pos = demand[3]
    # We want d1_neg = 0 (do not under-satisfy customer 4)
    d1_neg = model.addVar(lb=0.0, name="d1_neg")
    d1_pos = model.addVar(lb=0.0, name="d1_pos")

    # p2: satisfaction rate for customers 1,2,3 (j=0,1,2) >= p2
    # For each j in {0,1,2}: sum_i x[i,j] >= p2 * demand[j]
    # Deviation: sum_i x[i,j] + d2_neg[j] - d2_pos[j] = p2 * demand[j]
    d2_neg = model.addVars([0, 1, 2], lb=0.0, name="d2_neg")
    d2_pos = model.addVars([0, 1, 2], lb=0.0, name="d2_pos")

    # p3: x[2,0] >= p3 (factory 3 to customer 1)
    # x[2,0] + d3_neg - d3_pos = p3; want d3_neg = 0
    d3_neg = model.addVar(lb=0.0, name="d3_neg")
    d3_pos = model.addVar(lb=0.0, name="d3_pos")

    # p4: discourage x[1,3] (factory 2 to customer 4)
    # penalty on x[1,3]; model as deviation from 0
    # d4_pos = x[1,3] (over-allocation to this route)
    d4_pos = model.addVar(lb=0.0, name="d4_pos")

    # p5: balance satisfaction of customer 1 (j=0) and customer 3 (j=2)
    # sat_rate_1 = sum_i x[i,0] / demand[0]
    # sat_rate_3 = sum_i x[i,2] / demand[2]
    # |sat_rate_1 - sat_rate_3| -> 0
    # Equivalently: sum_i x[i,0]/demand[0] - sum_i x[i,2]/demand[2] = d5_pos - d5_neg
    d5_neg = model.addVar(lb=0.0, name="d5_neg")
    d5_pos = model.addVar(lb=0.0, name="d5_pos")

    # p6: total transportation cost (soft goal, deviations from 0)
    # minimize cost = sum_i sum_j unit_cost[i][j] * x[i][j]
    # We handle p6 directly in the objective

    # --- Hard constraints: supply limits ---
    for i in I:
        model.addConstr(
            gp.quicksum(x[i, j] for j in J) <= supply[i],
            name=f"supply_{i}"
        )

    # --- Goal constraints ---

    # p1: customer 4 fully satisfied
    model.addConstr(
        gp.quicksum(x[i, 3] for i in I) + d1_neg - d1_pos == demand[3],
        name="goal_p1"
    )

    # p2: customers 1,2,3 satisfaction >= p2 * demand[j]
    for j in [0, 1, 2]:
        model.addConstr(
            gp.quicksum(x[i, j] for i in I) + d2_neg[j] - d2_pos[j] == p2 * demand[j],
            name=f"goal_p2_{j}"
        )

    # p3: factory 3 to customer 1 >= p3
    model.addConstr(
        x[2, 0] + d3_neg - d3_pos == p3,
        name="goal_p3"
    )

    # p4: x[1,3] deviation from 0
    model.addConstr(
        x[1, 3] - d4_pos == 0,
        name="goal_p4"
    )

    # p5: balance satisfaction rates of customers 1 and 3
    model.addConstr(
        gp.quicksum(x[i, 0] for i in I) / demand[0]
        - gp.quicksum(x[i, 2] for i in I) / demand[2]
        - d5_pos + d5_neg == 0,
        name="goal_p5"
    )

    # Total transportation cost expression
    total_cost = gp.quicksum(unit_cost[i][j] * x[i, j] for i in I for j in J)

    # --- Weighted objective (preemptive priority approximation via large weights) ---
    # Priority: p1 >> p2 >> p3 >> p4 >> p5 >> p6
    # Use hierarchical weights: W1 >> W2 >> ... >> W6
    W1 = 1e10
    W2 = 1e8
    W3 = 1e6
    W4 = p4_weight * 1e4
    W5 = 1e2
    W6 = 1.0

    obj = (
        W1 * d1_neg                              # p1: minimize under-satisfaction of customer 4
        + W2 * (d2_neg[0] + d2_neg[1] + d2_neg[2])  # p2: minimize under-satisfaction of customers 1,2,3
        + W3 * d3_neg                            # p3: minimize shortage from factory3->customer1
        + W4 * d4_pos                            # p4: discourage factory2->customer4
        + W5 * (d5_pos + d5_neg)                 # p5: balance satisfaction rates
        + W6 * total_cost                        # p6: minimize total cost
    )

    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}