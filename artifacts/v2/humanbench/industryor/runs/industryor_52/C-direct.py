import gurobipy as gp
from gurobipy import GRB

def solve(params):
    normal_hours = params["normal_hours"]          # list of 6 values
    max_overtime_hours = params["max_overtime_hours"]  # list of 6 values
    overtime_cost_premium = params["overtime_cost_premium"]  # list of 5 values (one per product)
    penalty_p3 = params["penalty_p3"]
    penalty_p4 = params["penalty_p4"]

    # Fixed problem data (structural constants from problem statement)
    # Products indexed 0..4 (products 1..5)
    # Months indexed 0..5 (Jan..Jun)
    n_products = 5
    n_months = 6

    # Order quantities (units)
    D = [2000, 4000, 5000, 1000, 10000]

    # Unit selling prices (yuan)
    S = [3200, 2400, 2800, 2000, 1600]

    # Unit costs during normal hours (yuan)
    C = [2560, 1920, 2240, 1600, 1280]

    # Production hours per unit
    a = [3, 2, 2.5, 2, 1]

    # Production availability constraints:
    # Product 1 (index 0): can only be produced in months 3-6 (March=index 2 to June=index 5)
    # Product 4 (index 3): can only be produced in months 2-6 (Feb=index 1 to June=index 5)
    # Products 2,3,5 (indices 1,2,4): can be produced in any month 1-6

    # Delivery deadlines (index of last allowed month, inclusive):
    # Product 3 (index 2): end of April => month index 3
    # Product 4 (index 3): end of May => month index 4
    # All others: end of June => month index 5
    # With penalty for products 3 and 4 if delivered late (up to end of June)

    # Decision variables:
    # x[i][t] = units of product i produced during normal hours in month t
    # y[i][t] = units of product i produced during overtime hours in month t
    # For products 3 and 4, we allow late delivery with penalty
    # delay_3 = months of delay for product 3 (0,1, or 2 since all must be done by June)
    # delay_4 = months of delay for product 4 (0 or 1)

    model = gp.Model("xuri_production")
    model.setParam("OutputFlag", 0)

    # Normal production variables
    x = {}
    for i in range(n_products):
        for t in range(n_months):
            x[i, t] = model.addVar(lb=0, name=f"x_{i}_{t}")

    # Overtime production variables
    y = {}
    for i in range(n_products):
        for t in range(n_months):
            y[i, t] = model.addVar(lb=0, name=f"y_{i}_{t}")

    # Delay variables for products 3 and 4 (integer months of delay)
    delay3 = model.addVar(lb=0, ub=2, vtype=GRB.INTEGER, name="delay3")
    delay4 = model.addVar(lb=0, ub=1, vtype=GRB.INTEGER, name="delay4")

    model.update()

    # Production availability constraints
    # Product 1 (index 0): only producible March-June (months 2-5)
    for t in range(2):  # Jan, Feb (indices 0,1)
        model.addConstr(x[0, t] == 0, name=f"avail_x_p1_m{t}")
        model.addConstr(y[0, t] == 0, name=f"avail_y_p1_m{t}")

    # Product 4 (index 3): only producible Feb-June (months 1-5)
    model.addConstr(x[3, 0] == 0, name="avail_x_p4_m0")
    model.addConstr(y[3, 0] == 0, name="avail_y_p4_m0")

    # Normal hours capacity constraints
    for t in range(n_months):
        model.addConstr(
            gp.quicksum(a[i] * x[i, t] for i in range(n_products)) <= normal_hours[t],
            name=f"normal_cap_m{t}"
        )

    # Overtime hours capacity constraints
    for t in range(n_months):
        model.addConstr(
            gp.quicksum(a[i] * y[i, t] for i in range(n_products)) <= max_overtime_hours[t],
            name=f"overtime_cap_m{t}"
        )

    # Demand fulfillment constraints
    # For product 3 (index 2): must deliver D[2] units by end of April + delay3 months
    # Cumulative production through month (3 + delay3) must be >= D[2]
    # We model this by: sum over all months <= deadline of production >= D[2]
    # Since delay3 is integer, we use a linearization approach.
    # Actually, simpler: total production of each product must equal demand (exact delivery)
    # and we track when cumulative production reaches demand.

    # Total production must equal demand for each product
    for i in range(n_products):
        model.addConstr(
            gp.quicksum(x[i, t] + y[i, t] for t in range(n_months)) == D[i],
            name=f"demand_{i}"
        )

    # For product 3: delivery by end of April (month index 3), or with delay
    # Cumulative production by month (3 + delay3) >= D[2]
    # We model: for each possible deadline month td in {3,4,5}:
    #   if delay3 = td - 3, then sum_{t=0}^{td} prod >= D[2]
    # Binary variables for which deadline applies
    # Use big-M: sum_{t=0}^{3} (x+y) + delay3 * (additional production in months 4,5) >= D[2]
    # Cleaner: introduce binary b3[k] = 1 if delay = k, for k=0,1,2
    b3 = model.addVars(3, vtype=GRB.BINARY, name="b3")
    model.addConstr(gp.quicksum(b3[k] for k in range(3)) == 1, name="b3_sum")
    model.addConstr(delay3 == gp.quicksum(k * b3[k] for k in range(3)), name="delay3_link")

    # Cumulative production through month (3+k) must be >= D[2] if b3[k]=1
    # i.e., if delay=0: sum through month 3 >= D[2]
    #        if delay=1: sum through month 4 >= D[2]
    #        if delay=2: sum through month 5 >= D[2]
    # Since total = D[2], this means all production happens by that month.
    # We enforce: sum_{t=0}^{3+k} prod[2,t] >= D[2] * b3[k]  for each k
    # But since total = D[2], this means production after month 3+k must be 0 when b3[k]=1.
    # Equivalently: sum_{t=3+k+1}^{5} prod[2,t] <= D[2] * (1 - b3[k])
    for k in range(3):
        deadline = 3 + k
        if deadline < n_months - 1:
            model.addConstr(
                gp.quicksum(x[2, t] + y[2, t] for t in range(deadline + 1, n_months))
                <= D[2] * (1 - b3[k]),
                name=f"p3_deadline_k{k}"
            )

    # For product 4: delivery by end of May (month index 4), or with delay of 1 month (June)
    b4 = model.addVars(2, vtype=GRB.BINARY, name="b4")
    model.addConstr(gp.quicksum(b4[k] for k in range(2)) == 1, name="b4_sum")
    model.addConstr(delay4 == gp.quicksum(k * b4[k] for k in range(2)), name="delay4_link")

    # If delay=0: all production by end of month 4; if delay=1: all production by end of month 5
    for k in range(2):
        deadline = 4 + k
        if deadline < n_months - 1:
            model.addConstr(
                gp.quicksum(x[3, t] + y[3, t] for t in range(deadline + 1, n_months))
                <= D[3] * (1 - b4[k]),
                name=f"p4_deadline_k{k}"
            )

    # Objective: maximize profit
    # Revenue - normal cost - overtime cost - penalty
    revenue = gp.quicksum(S[i] * D[i] for i in range(n_products))

    normal_cost = gp.quicksum(
        C[i] * x[i, t] for i in range(n_products) for t in range(n_months)
    )

    overtime_cost = gp.quicksum(
        (C[i] + overtime_cost_premium[i]) * y[i, t]
        for i in range(n_products) for t in range(n_months)
    )

    penalty = penalty_p3 * delay3 + penalty_p4 * delay4

    model.setObjective(revenue - normal_cost - overtime_cost - penalty, GRB.MAXIMIZE)

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