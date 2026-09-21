# sample_142

certified: 220688.0
vault label: 264305.8997975709
relative gap: 0.16502809748468492
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 6

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

You have 4 distribution centers (facility_0, facility_1, facility_2, facility_3) that can be opened or closed. Each distribution center has a fixed operating cost if opened: facility_0 costs 102,701 units, facility_1 costs 104,150 units, facility_2 costs 103,985 units, and facility_3 costs 101,826 units. There are 10 retail stores (customer_0 to customer_9) with specific demands: customer_0 requires 192 units, customer_1 requires 200 units, customer_2 requires 192 units, customer_3 requires 213 units, customer_4 requires 217 units, customer_5 requires 205 units, customer_6 requires 218 units, customer_7 requires 181 units, customer_8 requires 211 units, and customer_9 requires 203 units. Each distribution center has a limited capacity: facility_0 can handle up to 964 units, facility_1 can handle up to 1,047 units, facility_2 can handle up to 977 units, and facility_3 can handle up to 988 units. The shipping costs from each distribution center to each retail store are as follows: facility_0 to customer_0 costs 30 units, to customer_1 costs 30 units, to customer_2 costs 26 units, and so on; facility_1 to customer_0 costs 31 units, to customer_1 costs 32 units, to customer_2 costs 25 units, and so on; facility_2 to customer_0 costs 29 units, to customer_1 costs 32 units, to customer_2 costs 26 units, and so on; facility_3 to customer_0 costs 30 units, to customer_1 costs 28 units, to customer_2 costs 29 units, and so on. The goal is to minimize the total cost, which includes the fixed costs of opening distribution centers and the variable shipping costs. Each retail store's demand must be fully met by the total shipments from all open distribution centers. A distribution center can only ship products to a retail store if it is open. The total amount shipped from each distribution center cannot exceed its capacity.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    fixed_cost = params["fixed_cost"]  # list of 4 floats
    demand = params["demand"]          # list of 10 floats
    capacity = params["capacity"]      # list of 4 floats
    shipping_cost = params["shipping_cost"]  # list of 4 lists, each of length 10
    
    # Model
    model = pyo.ConcreteModel()
    
    # Sets
    model.I = pyo.Set(initialize=range(4))          # facilities
    model.J = pyo.Set(initialize=range(10))         # customers
    
    # Parameters
    model.f = pyo.Param(model.I, initialize=lambda m, i: fixed_cost[i])
    model.d = pyo.Param(model.J, initialize=lambda m, j: demand[j])
    model.cap = pyo.Param(model.I, initialize=lambda m, i: capacity[i])
    model.c = pyo.Param(model.I, model.J, initialize=lambda m, i, j: shipping_cost[i][j])
    
    # Variables
    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)  # shipment
    model.y = pyo.Var(model.I, domain=pyo.Binary)                     # open facility
    
    # Objective
    def total_cost_rule(m):
        fixed = sum(m.f[i] * m.y[i] for i in m.I)
        variable = sum(m.c[i, j] * m.x[i, j] for i in m.I for j in m.J)
        return fixed + variable
    model.obj = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
    
    # Demand satisfaction
    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == m.d[j]
    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)
    
    # Capacity and linking
    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= m.cap[i] * m.y[i]
    model.capacity_con = pyo.Constraint(model.I, rule=capacity_rule)
    
    # Solve
    solver = Highs()
    results = solver.solve(model)
    
    # Extract objective value if possible
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "solve_failed"}
```

## Clique member B-structured

```python
# {"sets":{"F":["facility_0","facility_1","facility_2","facility_3"],"C":["customer_0","customer_1","customer_2","customer_3","customer_4","customer_5","customer_6","customer_7","customer_8","customer_9"]},"params":{"fixed_cost":"fixed_cost[f]","demand":"demand[c]","capacity":"capacity[f]","shipping_cost":"shipping_cost[f,c]"},"vars":{"open_facility":{"type":"Binary","index":"F"},"ship":{"type":"NonNegativeReals","index":["F","C"]}},"constraints":["sum_f ship[f,c] == demand[c] for all c","sum_c ship[f,c] <= capacity[f] * open_facility[f] for all f","ship[f,c] <= demand[c] * open_facility[f] for all f,c"],"objective":"min sum_f fixed_cost[f]*open_facility[f] + sum_f sum_c shipping_cost[f,c]*ship[f,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = ["facility_0", "facility_1", "facility_2", "facility_3"]
    customers = [f"customer_{idx}" for idx in range(10)]

    def normalize_1d_dict(data, valid_keys):
        if isinstance(data, dict):
            normalized = {}
            for key in valid_keys:
                if key in data:
                    normalized[key] = data[key]
                else:
                    suffix = key.split("_", 1)[1]
                    int_key = int(suffix)
                    str_int_key = str(int_key)
                    if int_key in data:
                        normalized[key] = data[int_key]
                    elif str_int_key in data:
                        normalized[key] = data[str_int_key]
                    else:
                        raise KeyError(f"Missing key {key}")
            return normalized
        return {key: data[pos] for pos, key in enumerate(valid_keys)}

    def normalize_2d_dict(data, row_keys, col_keys):
        normalized = {}
        for row_key in row_keys:
            row_suffix = row_key.split("_", 1)[1]
            row_int = int(row_suffix)
            row_str_int = str(row_int)

            for col_key in col_keys:
                col_suffix = col_key.split("_", 1)[1]
                col_int = int(col_suffix)
                col_str_int = str(col_int)

                found = False
                candidate_keys = [
                    (row_key, col_key),
                    (row_int, col_int),
                    (row_str_int, col_str_int),
                    (row_key, col_int),
                    (row_key, col_str_int),
                    (row_int, col_key),
                    (row_str_int, col_key),
                ]
                if isinstance(data, dict):
                    for candidate in candidate_keys:
                        if candidate in data:
                            normalized[(row_key, col_key)] = data[candidate]
                            found = True
                            break
                    if not found and row_key in data and isinstance(data[row_key], dict):
                        row_data = data[row_key]
                        if col_key in row_data:
                            normalized[(row_key, col_key)] = row_data[col_key]
                            found = True
                        elif col_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_int]
                            found = True
                        elif col_str_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_str_int]
                            found = True
                    if not found and row_int in data and isinstance(data[row_int], dict):
                        row_data = data[row_int]
                        if col_key in row_data:
                            normalized[(row_key, col_key)] = row_data[col_key]
                            found = True
                        elif col_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_int]
                            found = True
                        elif col_str_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_str_int]
                            found = True
                    if not found and row_str_int in data and isinstance(data[row_str_int], dict):
                        row_data = data[row_str_int]
                        if col_key in row_data:
                            normalized[(row_key, col_key)] = row_data[col_key]
                            found = True
                        elif col_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_int]
                            found = True
                        elif col_str_int in row_data:
                            normalized[(row_key, col_key)] = row_data[col_str_int]
                            found = True
                else:
                    normalized[(row_key, col_key)] = data[row_int][col_int]
                    found = True

                if not found:
                    raise KeyError(f"Missing key ({row_key}, {col_key})")
        return normalized

    fixed_cost_data = normalize_1d_dict(params["fixed_cost"], facilities)
    demand_data = normalize_1d_dict(params["demand"], customers)
    capacity_data = normalize_1d_dict(params["capacity"], facilities)
    shipping_cost_data = normalize_2d_dict(params["shipping_cost"], facilities, customers)

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(model.F, initialize=fixed_cost_data)
    model.demand = pyo.Param(model.C, initialize=demand_data)
    model.capacity = pyo.Param(model.F, initialize=capacity_data)
    model.shipping_cost = pyo.Param(model.F, model.C, initialize=shipping_cost_data)

    model.open_facility = pyo.Var(model.F, domain=pyo.Binary)
    model.ship = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(model, customer):
        return sum(model.ship[facility, customer] for facility in model.F) == model.demand[customer]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(model, facility):
        return sum(model.ship[facility, customer] for customer in model.C) <= model.capacity[facility] * model.open_facility[facility]

    model.capacity_con = pyo.Constraint(model.F, rule=capacity_rule)

    def linking_rule(model, facility, customer):
        return model.ship[facility, customer] <= model.demand[customer] * model.open_facility[facility]

    model.link_con = pyo.Constraint(model.F, model.C, rule=linking_rule)

    model.total_cost = pyo.Objective(
        expr=
        sum(model.fixed_cost[facility] * model.open_facility[facility] for facility in model.F)
        + sum(model.shipping_cost[facility, customer] * model.ship[facility, customer] for facility in model.F for customer in model.C),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "failed"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost = params["shipping_cost"]
    
    num_facilities = len(fixed_cost)
    num_customers = len(demand)
    
    model = gp.Model("facility_location")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # y[i] = 1 if facility i is opened
    y = model.addVars(num_facilities, vtype=GRB.BINARY, name="y")
    
    # x[i,j] = amount shipped from facility i to customer j
    x = model.addVars(num_facilities, num_customers, vtype=GRB.CONTINUOUS, lb=0, name="x")
    
    # Objective: minimize total fixed + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in range(num_facilities)) +
        gp.quicksum(shipping_cost[i][j] * x[i, j] 
                    for i in range(num_facilities) 
                    for j in range(num_customers)),
        GRB.MINIMIZE
    )
    
    # Constraints
    # 1. Demand satisfaction: each customer's demand must be met
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demand[j],
            name=f"demand_{j}"
        )
    
    # 2. Capacity constraints: total shipments from facility i cannot exceed capacity
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_customers)) <= capacity[i] * y[i],
            name=f"capacity_{i}"
        )
    
    # Solve
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        return {
            "objective": model.objVal,
            "status": "optimal"
        }
    elif model.status == GRB.INFEASIBLE:
        return {
            "objective": None,
            "status": "infeasible"
        }
    elif model.status == GRB.UNBOUNDED:
        return {
            "objective": None,
            "status": "unbounded"
        }
    else:
        return {
            "objective": None,
            "status": f"status_{model.status}"
        }
```
