import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Expected params keys (as specified):
    #   processing_time: indexed by (machine, product) where
    #       machines: A1, A2, B1, B2, B3  products: I, II, III
    #   effective_hours: indexed by machine
    #   machine_fee: indexed by machine
    #   raw_material_cost: indexed by product
    #   selling_price: indexed by product
    #
    # To be robust, we also accept flat list/array forms where the
    # data is laid out in table order (rows=machines, cols=products).

    machines = ["A1", "A2", "B1", "B2", "B3"]
    products = ["I", "II", "III"]

    # --- Normalize processing_time ---
    raw_pt = params["processing_time"]
    if isinstance(raw_pt, dict):
        pt = raw_pt
    else:
        # Assume it's a 2D list/array: rows=machines (A1,A2,B1,B2,B3), cols=products (I,II,III)
        # Entries that don't apply may be 0 or None
        pt = {}
        for i, mach in enumerate(machines):
            for j, prod in enumerate(products):
                pt[(mach, prod)] = float(raw_pt[i][j])

    # --- Normalize effective_hours ---
    raw_eh = params["effective_hours"]
    if isinstance(raw_eh, dict):
        eh = raw_eh
    else:
        eh = {mach: float(raw_eh[i]) for i, mach in enumerate(machines)}

    # --- Normalize machine_fee ---
    raw_mf = params["machine_fee"]
    if isinstance(raw_mf, dict):
        mf = raw_mf
    else:
        mf = {mach: float(raw_mf[i]) for i, mach in enumerate(machines)}

    # --- Normalize raw_material_cost ---
    raw_rm = params["raw_material_cost"]
    if isinstance(raw_rm, dict):
        rm = raw_rm
    else:
        rm = {prod: float(raw_rm[j]) for j, prod in enumerate(products)}

    # --- Normalize selling_price ---
    raw_sp = params["selling_price"]
    if isinstance(raw_sp, dict):
        sp = raw_sp
    else:
        sp = {prod: float(raw_sp[j]) for j, prod in enumerate(products)}

    model = gp.Model("hongsheng")
    model.setParam("OutputFlag", 0)

    # -------------------------------------------------------------------------
    # Decision variables: units routed through each machine for each product
    # Step A routing:
    #   Product I  : A1 or A2
    #   Product II : A1 or A2  (problem says "any type of A machine")
    #   Product III: A2 only
    # Step B routing:
    #   Product I  : B1, B2, or B3
    #   Product II : B2 only
    #   Product III: B2 only
    # -------------------------------------------------------------------------

    x1_a1 = model.addVar(lb=0, name="x1_a1")  # P-I units on A1
    x1_a2 = model.addVar(lb=0, name="x1_a2")  # P-I units on A2
    x2_a1 = model.addVar(lb=0, name="x2_a1")  # P-II units on A1
    x2_a2 = model.addVar(lb=0, name="x2_a2")  # P-II units on A2
    x3_a2 = model.addVar(lb=0, name="x3_a2")  # P-III units on A2

    x1_b1 = model.addVar(lb=0, name="x1_b1")  # P-I units on B1
    x1_b2 = model.addVar(lb=0, name="x1_b2")  # P-I units on B2
    x1_b3 = model.addVar(lb=0, name="x1_b3")  # P-I units on B3
    x2_b2 = model.addVar(lb=0, name="x2_b2")  # P-II units on B2
    x3_b2 = model.addVar(lb=0, name="x3_b2")  # P-III units on B2

    # -------------------------------------------------------------------------
    # Flow balance: total units through step A == total units through step B
    # -------------------------------------------------------------------------
    model.addConstr(x1_a1 + x1_a2 == x1_b1 + x1_b2 + x1_b3, "balance_p1")
    model.addConstr(x2_a1 + x2_a2 == x2_b2,                  "balance_p2")
    model.addConstr(x3_a2          == x3_b2,                  "balance_p3")

    # -------------------------------------------------------------------------
    # Machine capacity constraints
    # -------------------------------------------------------------------------
    model.addConstr(
        pt[("A1","I")] * x1_a1 + pt[("A1","II")] * x2_a1
        <= eh["A1"], "cap_A1"
    )
    model.addConstr(
        pt[("A2","I")] * x1_a2 + pt[("A2","II")] * x2_a2 + pt[("A2","III")] * x3_a2
        <= eh["A2"], "cap_A2"
    )
    model.addConstr(
        pt[("B1","I")] * x1_b1
        <= eh["B1"], "cap_B1"
    )
    model.addConstr(
        pt[("B2","I")] * x1_b2 + pt[("B2","II")] * x2_b2 + pt[("B2","III")] * x3_b2
        <= eh["B2"], "cap_B2"
    )
    model.addConstr(
        pt[("B3","I")] * x1_b3
        <= eh["B3"], "cap_B3"
    )

    # -------------------------------------------------------------------------
    # Objective: maximize profit = revenue - raw material cost - machine fees
    # -------------------------------------------------------------------------
    prod1 = x1_a1 + x1_a2        # total P-I produced
    prod2 = x2_a1 + x2_a2        # total P-II produced
    prod3 = x3_a2                 # total P-III produced

    revenue = sp["I"] * prod1 + sp["II"] * prod2 + sp["III"] * prod3

    mat_cost = rm["I"] * prod1 + rm["II"] * prod2 + rm["III"] * prod3

    machine_cost = (
        mf["A1"] * (pt[("A1","I")] * x1_a1 + pt[("A1","II")] * x2_a1) +
        mf["A2"] * (pt[("A2","I")] * x1_a2 + pt[("A2","II")] * x2_a2 + pt[("A2","III")] * x3_a2) +
        mf["B1"] * (pt[("B1","I")] * x1_b1) +
        mf["B2"] * (pt[("B2","I")] * x1_b2 + pt[("B2","II")] * x2_b2 + pt[("B2","III")] * x3_b2) +
        mf["B3"] * (pt[("B3","I")] * x1_b3)
    )

    profit = revenue - mat_cost - machine_cost
    model.setObjective(profit, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}