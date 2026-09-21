# sample_269

certified: 74276.52852852854
vault label: 74265.5
relative gap: 0.0001485013704685943
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

Imagine you are managing a production facility that manufactures 15 different types of items, each with its own profit margin and resource consumption. Your goal is to determine the optimal quantity of each item to produce in order to maximize total profit, while adhering to resource limitations and production capacity constraints.

#### Key Details:
1. **Items and Profit Margins**:  
   Each item contributes a specific profit per unit produced. The profit margins for the items are as follows:  
   - Item 0: \$49 per unit  
   - Item 1: \$49 per unit  
   - Item 2: \$43 per unit  
   - Item 3: \$35 per unit  
   - Item 4: \$20 per unit  
   - Item 5: \$28 per unit  
   - Item 6: \$40 per unit  
   - Item 7: \$34 per unit  
   - Item 8: \$47 per unit  
   - Item 9: \$43 per unit  
   - Item 10: \$49 per unit  
   - Item 11: \$33 per unit  
   - Item 12: \$29 per unit  
   - Item 13: \$25 per unit  
   - Item 14: \$44 per unit  

2. **Resource Consumption**:  
   Producing each item consumes a specific amount of a shared resource. The resource consumption rates are:  
   - Item 0: 0.2 units of resource per unit produced  
   - Item 1: 0.5 units of resource per unit produced  
   - Item 2: 0.2 units of resource per unit produced  
   - Item 3: 1 unit of resource per unit produced  
   - Item 4: 0.2 units of resource per unit produced  
   - Item 5: 0.2 units of resource per unit produced  
   - Item 6: 0.2 units of resource per unit produced  
   - Item 7: 0.2 units of resource per unit produced  
   - Item 8: 0.2 units of resource per unit produced  
   - Item 9: 0.2 units of resource per unit produced  
   - Item 10: 0.333 units of resource per unit produced  
   - Item 11: 0.5 units of resource per unit produced  
   - Item 12: 0.2 units of resource per unit produced  
   - Item 13: 0.333 units of resource per unit produced  
   - Item 14: 0.333 units of resource per unit produced  

   The total available resource for production is **471 units**.

3. **Production Capacity Constraints**:  
   Each item has a maximum production limit due to factors such as machine capacity or material availability. The upper limits for each item are:  
   - Item 0: 170 units  
   - Item 1: 101 units  
   - Item 2: 124 units  
   - Item 3: 194 units  
   - Item 4: 167 units  
   - Item 5: 131 units  
   - Item 6: 194 units  
   - Item 7: 167 units  
   - Item 8: 185 units  
   - Item 9: 120 units  
   - Item 10: 141 units  
   - Item 11: 190 units  
   - Item 12: 110 units  
   - Item 13: 177 units  
   - Item 14: 198 units  

#### Objective:
Your task is to determine the optimal production quantities for each item to **maximize total profit**, while ensuring that:  
1. The total resource consumption across all items does not exceed **471 units**.  
2. The production quantity for each item does not exceed its respective upper limit.  
3. The production quantity for each item is non-negative (i.e., no negative production is allowed).  

By carefully balancing resource allocation and production quantities, you aim to achieve the highest possible profit for the facility.

## Clique member A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract data from params dict
    profit_margins = params["profit_margins"]          # list of 15 floats
    resource_consumption = params["resource_consumption"]  # list of 15 floats
    resource_capacity = params["resource_capacity"]    # float
    production_limits = params["production_limits"]     # list of 15 floats
    
    n_items = 15  # structural constant
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Index set
    model.I = pyo.RangeSet(0, n_items - 1)
    
    # Decision variables: production quantity for each item
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    
    # Objective: maximize total profit
    def obj_rule(m):
        return sum(profit_margins[i] * m.x[i] for i in m.I)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
    
    # Resource capacity constraint
    def resource_rule(m):
        return sum(resource_consumption[i] * m.x[i] for i in m.I) <= resource_capacity
    model.resource_constraint = pyo.Constraint(rule=resource_rule)
    
    # Production limit constraints
    def limit_rule(m, i):
        return m.x[i] <= production_limits[i]
    model.production_limits = pyo.Constraint(model.I, rule=limit_rule)
    
    # Solve with HiGHS
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        results = solver.solve(model)
    except Exception as e:
        return {"objective": None, "status": f"solver error: {e}"}
    
    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.objective))
        return {"objective": obj_val, "status": "optimal"}
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible or no solution"}
```

## Clique member B-structured

```python
# {"sets":{"ITEMS":"range(15)"},"params":{"profit_margins":"profit per unit for each item","resource_consumption":"resource units consumed per unit produced for each item","resource_capacity":"total available resource units","production_limits":"maximum production quantity for each item"},"decision_variables":{"produce[i]":"NonNegativeReals for i in ITEMS"},"constraints":["resource_capacity: sum(resource_consumption[i]*produce[i] for i in ITEMS) <= resource_capacity","production_limit[i]: produce[i] <= production_limits[i] for i in ITEMS"],"objective":"maximize sum(profit_margins[i]*produce[i] for i in ITEMS)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.ITEMS = pyo.RangeSet(0, 14)

    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]

    model.produce = pyo.Var(model.ITEMS, domain=pyo.NonNegativeReals)

    model.resource_capacity_con = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.produce[i] for i in model.ITEMS) <= resource_capacity
    )

    model.production_limit_con = pyo.Constraint(
        model.ITEMS,
        rule=lambda model, i: model.produce[i] <= production_limits[i],
    )

    model.total_profit = pyo.Objective(
        expr=sum(profit_margins[i] * model.produce[i] for i in model.ITEMS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_profit))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]
    
    num_items = len(profit_margins)
    
    try:
        model = gp.Model("production_optimization")
        model.Params.OutputFlag = 0
        
        # Decision variables: production quantity for each item
        x = model.addVars(num_items, lb=0, name="production")
        
        # Objective: maximize total profit
        model.setObjective(
            gp.quicksum(profit_margins[i] * x[i] for i in range(num_items)),
            GRB.MAXIMIZE
        )
        
        # Constraint: total resource consumption <= resource capacity
        model.addConstr(
            gp.quicksum(resource_consumption[i] * x[i] for i in range(num_items)) <= resource_capacity,
            name="resource_limit"
        )
        
        # Constraints: production quantity <= production limit for each item
        for i in range(num_items):
            model.addConstr(x[i] <= production_limits[i], name=f"prod_limit_{i}")
        
        # Solve the model
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
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }
```
