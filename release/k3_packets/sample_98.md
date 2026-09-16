# sample_98

certified: 75679.0
vault label: 75312.0
relative gap: 0.004873061397917994
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 6


## Problem text

The manufacturing facility produces three distinct products over a six-month planning horizon. The goal is to minimize total costs, including production costs, setup costs, and inventory holding costs, while meeting monthly demand and respecting production capacity limits. Each product has specific monthly demands: Product 0 has demands of 79, 76, 93, 96, 91, and 81 units for months 1 through 6, respectively; Product 1 has demands of 86, 81, 85, 54, 80, and 87 units; and Product 2 has demands of 95, 69, 51, 76, 55, and 83 units. Production costs vary by product and month: Product 0 costs \$48, \$41, \$50, \$46, \$44, and \$40 per unit; Product 1 costs \$43, \$47, \$47, \$40, \$44, and \$45 per unit; and Product 2 costs \$45, \$43, \$44, \$47, \$43, and \$45 per unit. Setup costs also vary: Product 0 costs \$1,095, \$1,071, \$1,391, \$1,222, \$1,313, and \$1,101; Product 1 costs \$1,449, \$1,196, \$1,003, \$1,297, \$1,113, and \$1,140; and Product 2 costs \$1,048, \$1,433, \$1,094, \$1,497, \$1,423, and \$1,070. Inventory holding costs are \$5 per unit per month for Products 0 and 1, and \$4 per unit per month for Product 2. The facility has monthly production capacities of 1,090, 1,009, 1,106, 1,048, 1,098, and 1,016 units of resource capacity for months 1 through 6. Each unit of Product 0 consumes 1.877 units of capacity, Product 1 consumes 1.884 units, and Product 2 consumes 1.622 units. Production of a product in a given month can only occur if the setup variable for that product and month is active, and the maximum production quantity for each product in a month is limited by the cumulative demand from that month onward. The inventory balance constraints ensure that cumulative production plus inventory equals cumulative demand for each product and month. Inventory levels must be non-negative, and there are no explicit constraints forcing initial or final inventory to be zero. The objective is to minimize the total cost, which includes production costs, setup costs, and inventory holding costs, while ensuring all demand is met and production capacity is not exceeded.

## Clique member A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract parameters from the input dict
    demand = params["demand"]  # shape (3,6)
    production_cost = params["production_cost"]  # shape (3,6)
    setup_cost = params["setup_cost"]  # shape (3,6)
    holding_cost = params["holding_cost"]  # shape (3,)
    capacity = params["capacity"]  # shape (6,)
    resource_consumption = params["resource_consumption"]  # shape (3,)
    
    # Define sets
    products = range(3)  # 0,1,2
    months = range(6)    # 0..5 (representing months 1..6)
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Variables
    model.x = pyo.Var(products, months, within=pyo.NonNegativeReals)
    model.y = pyo.Var(products, months, within=pyo.Binary)
    model.i = pyo.Var(products, months, within=pyo.NonNegativeReals)
    
    # Objective: minimize total cost
    production_terms = sum(production_cost[p][m] * model.x[p,m] 
                          for p in products for m in months)
    setup_terms = sum(setup_cost[p][m] * model.y[p,m] 
                     for p in products for m in months)
    holding_terms = sum(holding_cost[p] * model.i[p,m] 
                       for p in products for m in months)
    model.obj = pyo.Objective(expr=production_terms + setup_terms + holding_terms, 
                             sense=pyo.minimize)
    
    # Capacity constraints
    def capacity_rule(model, m):
        return sum(resource_consumption[p] * model.x[p,m] for p in products) <= capacity[m]
    model.capacity_con = pyo.Constraint(months, rule=capacity_rule)
    
    # Setup forcing constraints
    def setup_rule(model, p, m):
        # Upper bound: cumulative demand from month m onward
        cum_demand = sum(demand[p][k] for k in range(m, 6))
        return model.x[p,m] <= cum_demand * model.y[p,m]
    model.setup_con = pyo.Constraint(products, months, rule=setup_rule)
    
    # Inventory balance constraints
    def inventory_balance_rule(model, p, m):
        if m == 0:
            return model.x[p,0] - model.i[p,0] == demand[p][0]
        else:
            return model.i[p,m-1] + model.x[p,m] - model.i[p,m] == demand[p][m]
    model.inventory_con = pyo.Constraint(products, months, rule=inventory_balance_rule)
    
    # Solve
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        results = solver.solve(model)
        
        # Check if solution is available
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception as e:
        # If objective cannot be evaluated, assume infeasible/failed
        return {'objective': None, 'status': str(e)}
```

## Clique member B-structured

```python
# {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"demand":"P x T","production_cost":"P x T","setup_cost":"P x T","holding_cost":"P","capacity":"T","resource_consumption":"P"},"vars":{"x":"nonnegative continuous, P x T","y":"binary, P x T","inv":"nonnegative continuous, P x T"},"constraints":["inventory balance: inv[p,t] = sum_{k<=t} x[p,k] - sum_{k<=t} demand[p,k]","capacity: sum_p resource_consumption[p]*x[p,t] <= capacity[t]","setup linkage: x[p,t] <= sum_{k=t..T-1} demand[p,k] * y[p,t]"],"objective":"min sum_{p,t} production_cost[p,t]*x[p,t] + setup_cost[p,t]*y[p,t] + holding_cost[p]*inv[p,t]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = range(3)
    months = range(6)

    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    resource_consumption = params["resource_consumption"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=months)

    model.x = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(model):
        return sum(
            production_cost[p][t] * model.x[p, t]
            + setup_cost[p][t] * model.y[p, t]
            + holding_cost[p] * model.inv[p, t]
            for p in model.P
            for t in model.T
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def inv_balance_rule(model, p, t):
        return model.inv[p, t] == sum(model.x[p, k] for k in model.T if k <= t) - sum(
            demand[p][k] for k in model.T if k <= t
        )

    model.inventory_balance = pyo.Constraint(model.P, model.T, rule=inv_balance_rule)

    def capacity_rule(model, t):
        return sum(resource_consumption[p] * model.x[p, t] for p in model.P) <= capacity[t]

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    def setup_link_rule(model, p, t):
        max_prod = sum(demand[p][k] for k in model.T if k >= t)
        return model.x[p, t] <= max_prod * model.y[p, t]

    model.setup_link = pyo.Constraint(model.P, model.T, rule=setup_link_rule)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    resource_consumption = params["resource_consumption"]
    
    # Structural constants
    num_products = 3
    num_months = 6
    products = range(num_products)
    months = range(num_months)
    
    # Create model
    model = gp.Model("manufacturing_planning")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # Production quantity for each product in each month
    production = model.addVars(products, months, lb=0, vtype=GRB.CONTINUOUS, name="production")
    
    # Setup binary variable for each product in each month
    setup = model.addVars(products, months, vtype=GRB.BINARY, name="setup")
    
    # Inventory level for each product at the end of each month
    inventory = model.addVars(products, months, lb=0, vtype=GRB.CONTINUOUS, name="inventory")
    
    # Constraints
    
    # Inventory balance constraints
    for p in products:
        for t in months:
            if t == 0:
                # First month: inventory = production - demand (assuming zero initial inventory)
                model.addConstr(
                    inventory[p, t] == production[p, t] - demand[p][t],
                    name=f"inventory_balance_{p}_{t}"
                )
            else:
                # Subsequent months: inventory = previous_inventory + production - demand
                model.addConstr(
                    inventory[p, t] == inventory[p, t-1] + production[p, t] - demand[p][t],
                    name=f"inventory_balance_{p}_{t}"
                )
    
    # Production capacity constraints
    for t in months:
        model.addConstr(
            gp.quicksum(resource_consumption[p] * production[p, t] for p in products) <= capacity[t],
            name=f"capacity_{t}"
        )
    
    # Setup constraints: production can only occur if setup is active
    # Maximum production is limited by cumulative demand from month t onward
    for p in products:
        for t in months:
            cumulative_demand = sum(demand[p][month] for month in range(t, num_months))
            model.addConstr(
                production[p, t] <= cumulative_demand * setup[p, t],
                name=f"setup_{p}_{t}"
            )
    
    # Objective: minimize total cost
    production_costs = gp.quicksum(
        production_cost[p][t] * production[p, t]
        for p in products
        for t in months
    )
    
    setup_costs = gp.quicksum(
        setup_cost[p][t] * setup[p, t]
        for p in products
        for t in months
    )
    
    holding_costs = gp.quicksum(
        holding_cost[p] * inventory[p, t]
        for p in products
        for t in months
    )
    
    total_cost = production_costs + setup_costs + holding_costs
    model.setObjective(total_cost, GRB.MINIMIZE)
    
    # Solve
    model.optimize()
    
    # Return results
    if model.status == GRB.OPTIMAL:
        return {
            "objective": model.ObjVal,
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
