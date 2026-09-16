# sample_292

certified: 1334786.128712871
vault label: 1333742.601993409
relative gap: 0.0007824048792491697
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

Imagine you are managing a production facility that manufactures 25 different types of items. Each item has a specific profit margin associated with it, and your goal is to maximize the total profit generated from producing these items. However, there are constraints on the resources available for production, as well as limits on how much of each item can be produced.

#### Profit Margins:
Each item contributes a certain amount to the total profit. The profit per unit for each item is as follows:
- Item 0: \$265  
- Item 1: \$287  
- Item 2: \$184  
- Item 3: \$264  
- Item 4: \$252  
- Item 5: \$285  
- Item 6: \$251  
- Item 7: \$185  
- Item 8: \$247  
- Item 9: \$161  
- Item 10: \$231  
- Item 11: \$151  
- Item 12: \$205  
- Item 13: \$251  
- Item 14: \$179  
- Item 15: \$276  
- Item 16: \$200  
- Item 17: \$154  
- Item 18: \$255  
- Item 19: \$165  
- Item 20: \$173  
- Item 21: \$271  
- Item 22: \$207  
- Item 23: \$182  
- Item 24: \$267  

#### Resource Constraints:
The production process requires a shared resource, and the total consumption of this resource across all items cannot exceed 106 units. Each item consumes a specific amount of this resource per unit produced:
- Item 0: 0.0303 units  
- Item 1: 0.0303 units  
- Item 2: 0.02 units  
- Item 3: 0.0222 units  
- Item 4: 0.0278 units  
- Item 5: 0.0192 units  
- Item 6: 0.0227 units  
- Item 7: 0.0256 units  
- Item 8: 0.0175 units  
- Item 9: 0.0294 units  
- Item 10: 0.0175 units  
- Item 11: 0.0244 units  
- Item 12: 0.0208 units  
- Item 13: 0.0182 units  
- Item 14: 0.0204 units  
- Item 15: 0.0182 units  
- Item 16: 0.0233 units  
- Item 17: 0.0175 units  
- Item 18: 0.0222 units  
- Item 19: 0.025 units  
- Item 20: 0.025 units  
- Item 21: 0.0213 units  
- Item 22: 0.0263 units  
- Item 23: 0.0270 units  
- Item 24: 0.0217 units  

#### Production Limits:
There are upper limits on how many units of each item can be produced due to capacity constraints:
- Item 0: Up to 581 units  
- Item 1: Up to 432 units  
- Item 2: Up to 546 units  
- Item 3: Up to 510 units  
- Item 4: Up to 322 units  
- Item 5: Up to 563 units  
- Item 6: Up to 529 units  
- Item 7: Up to 491 units  
- Item 8: Up to 582 units  
- Item 9: Up to 397 units  
- Item 10: Up to 441 units  
- Item 11: Up to 466 units  
- Item 12: Up to 591 units  
- Item 13: Up to 428 units  
- Item 14: Up to 363 units  
- Item 15: Up to 449 units  
- Item 16: Up to 394 units  
- Item 17: Up to 499 units  
- Item 18: Up to 341 units  
- Item 19: Up to 544 units  
- Item 20: Up to 474 units  
- Item 21: Up to 313 units  
- Item 22: Up to 336 units  
- Item 23: Up to 565 units  
- Item 24: Up to 462 units  

#### Objective:
Your task is to determine the optimal number of units to produce for each item, ensuring that:
1. The total resource consumption does not exceed 106 units.  
2. The production of each item does not exceed its respective upper limit.  
3. The total profit is maximized.  

By carefully balancing the production quantities of each item, you aim to achieve the highest possible profit while staying within the resource and production constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract data from params dict
    profit = params["profit"]                     # list of 25 floats
    resource_consumption = params["resource_consumption"]  # list of 25 floats
    resource_capacity = params["resource_capacity"]        # float
    production_limits = params["production_limits"]       # list of 25 floats
    
    N = 25  # number of items
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Index set
    model.I = pyo.RangeSet(0, N-1)
    
    # Decision variables: units produced for each item
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    
    # Objective: maximize total profit
    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.I),
        sense=pyo.maximize
    )
    
    # Resource constraint: total consumption <= capacity
    model.resource_constr = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.x[i] for i in model.I) <= resource_capacity
    )
    
    # Production limits for each item
    def production_limit_rule(model, i):
        return model.x[i] <= production_limits[i]
    model.prod_limit_constr = pyo.Constraint(model.I, rule=production_limit_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution is available by trying to access objective value
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible or failed'}
```

## Clique member B-structured

```python
# IR: {"sets":{"ITEMS":"range(25)"},"params":{"profit":"profit[i] for i in ITEMS","resource_consumption":"resource_consumption[i] for i in ITEMS","resource_capacity":"scalar","production_limits":"production_limits[i] for i in ITEMS"},"variables":{"produce[i]":"NonNegativeReals"},"constraints":["resource_capacity: sum(resource_consumption[i]*produce[i] for i in ITEMS) <= resource_capacity","production_limit[i]: produce[i] <= production_limits[i] for i in ITEMS"],"objective":"maximize sum(profit[i]*produce[i] for i in ITEMS)"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]

    model = pyo.ConcreteModel()
    model.ITEMS = pyo.RangeSet(0, 24)

    model.produce = pyo.Var(model.ITEMS, domain=pyo.NonNegativeReals)

    def resource_capacity_rule(model):
        return sum(
            resource_consumption[item] * model.produce[item]
            for item in model.ITEMS
        ) <= resource_capacity

    model.resource_capacity_con = pyo.Constraint(rule=resource_capacity_rule)

    def production_limit_rule(model, item):
        return model.produce[item] <= production_limits[item]

    model.production_limit_con = pyo.Constraint(model.ITEMS, rule=production_limit_rule)

    model.total_profit = pyo.Objective(
        expr=sum(profit[item] * model.produce[item] for item in model.ITEMS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_profit))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]
    
    n_items = len(profit)
    
    # Create model
    model = gp.Model("production_optimization")
    model.Params.OutputFlag = 0
    
    # Decision variables: production quantity for each item
    x = model.addVars(n_items, lb=0, vtype=GRB.CONTINUOUS, name="production")
    
    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )
    
    # Constraint: total resource consumption cannot exceed capacity
    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n_items)) <= resource_capacity,
        name="resource_constraint"
    )
    
    # Constraints: production limits for each item
    for i in range(n_items):
        model.addConstr(x[i] <= production_limits[i], name=f"limit_{i}")
    
    # Solve the model
    model.optimize()
    
    # Return results
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
