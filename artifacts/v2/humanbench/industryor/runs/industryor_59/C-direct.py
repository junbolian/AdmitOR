import gurobipy as gp
from gurobipy import GRB

def solve(params):
    unit_processing_time = params["unit_processing_time"]
    equipment_available_time = params["equipment_available_time"]
    equipment_cost_full_load = params["equipment_cost_full_load"]
    raw_material_cost = params["raw_material_cost"]
    unit_price = params["unit_price"]

    # unit_processing_time order: A1:I,II,III; A2:I,II,III; B1:I,II,III; B2:I,II,III; B3:I,II,III
    # Index mapping: equipment 0=A1,1=A2,2=B1,3=B2,4=B3; product 0=I,1=II,2=III
    # equipment_available_time order: A1, A2, B1, B2, B3
    # equipment_cost_full_load order: A1, A2, B1, B2, B3

    t = {}
    for eq_idx in range(5):
        for prod_idx in range(3):
            t[(eq_idx, prod_idx)] = unit_processing_time[eq_idx * 3 + prod_idx]

    T = equipment_available_time  # list of 5
    C = equipment_cost_full_load  # list of 5
    rm = raw_material_cost        # list of 3: I, II, III
    price = unit_price            # list of 3: I, II, III

    # Decision variables:
    # x[eq_idx, prod_idx] = units of product prod_idx processed on equipment eq_idx
    # Feasibility constraints (from problem description):
    # Product I (0): can use A1(0), A2(1) for step A; B1(2), B2(3), B3(4) for step B
    # Product II (1): can use A1(0), A2(1) for step A; B1(2) only for step B
    # Product III (2): can use A2(1) only for step A; B2(3) only for step B
    # Also, unit_processing_time=0 means that combination is not allowed (from table, missing entries)

    # Valid (equipment, product) pairs based on problem description and table:
    # A1(0): I(0), II(1) — III not allowed on A1
    # A2(1): I(0), II(1), III(2)
    # B1(2): I(0), II(1) — III not allowed on B1
    # B2(3): I(0), III(2) — II not allowed on B2
    # B3(4): I(0) only — II and III not allowed on B3

    valid_pairs = []
    for eq_idx in range(5):
        for prod_idx in range(3):
            if t[(eq_idx, prod_idx)] > 0:
                valid_pairs.append((eq_idx, prod_idx))

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    x = {}
    for (eq_idx, prod_idx) in valid_pairs:
        x[(eq_idx, prod_idx)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                              name=f"x_{eq_idx}_{prod_idx}")

    # Equipment time constraints
    for eq_idx in range(5):
        pairs_for_eq = [(eq_idx, prod_idx) for (ei, prod_idx) in valid_pairs if ei == eq_idx]
        # rebuild correctly
        pairs_for_eq = [(ei, pi) for (ei, pi) in valid_pairs if ei == eq_idx]
        if pairs_for_eq:
            model.addConstr(
                gp.quicksum(t[(ei, pi)] * x[(ei, pi)] for (ei, pi) in pairs_for_eq) <= T[eq_idx],
                name=f"time_eq_{eq_idx}"
            )

    # Production consistency: total units of each product produced on A equipment
    # must equal total units processed on B equipment
    # Products and their valid A and B equipment:
    # Step A equipment: A1(0), A2(1)
    # Step B equipment: B1(2), B2(3), B3(4)
    A_equip = [0, 1]
    B_equip = [2, 3, 4]

    for prod_idx in range(3):
        a_pairs = [(ei, pi) for (ei, pi) in valid_pairs if ei in A_equip and pi == prod_idx]
        b_pairs = [(ei, pi) for (ei, pi) in valid_pairs if ei in B_equip and pi == prod_idx]
        if a_pairs and b_pairs:
            model.addConstr(
                gp.quicksum(x[(ei, pi)] for (ei, pi) in a_pairs) ==
                gp.quicksum(x[(ei, pi)] for (ei, pi) in b_pairs),
                name=f"balance_prod_{prod_idx}"
            )

    # Objective: maximize profit = revenue - raw material cost - equipment cost
    # Equipment cost per unit processed on equipment eq_idx for product prod_idx:
    #   cost_rate[eq_idx] = C[eq_idx] / T[eq_idx]  (cost per hour at full load)
    #   equipment cost for x[eq,prod] = cost_rate[eq] * t[eq,prod] * x[eq,prod]
    # Revenue and raw material cost are based on total units of each product (use A step as reference)

    profit_terms = []

    # Revenue and raw material cost: based on total production of each product
    # Total production of product prod_idx = sum of x over A equipment for that product
    for prod_idx in range(3):
        a_pairs = [(ei, pi) for (ei, pi) in valid_pairs if ei in A_equip and pi == prod_idx]
        for (ei, pi) in a_pairs:
            profit_terms.append((price[prod_idx] - rm[prod_idx]) * x[(ei, pi)])

    # Subtract equipment costs for all equipment usage
    for (eq_idx, prod_idx) in valid_pairs:
        cost_rate = C[eq_idx] / T[eq_idx]
        profit_terms.append(-cost_rate * t[(eq_idx, prod_idx)] * x[(eq_idx, prod_idx)])

    model.setObjective(gp.quicksum(profit_terms), GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}