# sample_30

certified: 10835935.256097559
vault label: 10834440.371982582
relative gap: 0.000137975203485607
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

Production Planning for a Manufacturing Facility

You are the production manager at a manufacturing facility that produces **45 distinct products** (labeled as item_0 to item_44). Your goal is to maximize the total profit generated from producing these products while adhering to resource constraints and production limits.

#### **Objective:**
Maximize the total profit from producing the 45 products. Each product contributes a specific profit per unit, as follows:
- Item_0: \$306 per unit  
- Item_1: \$354 per unit  
- Item_2: \$386 per unit  
- Item_3: \$363 per unit  
- Item_4: \$325 per unit  
- Item_5: \$374 per unit  
- Item_6: \$361 per unit  
- Item_7: \$385 per unit  
- Item_8: \$360 per unit  
- Item_9: \$365 per unit  
- Item_10: \$340 per unit  
- Item_11: \$343 per unit  
- Item_12: \$335 per unit  
- Item_13: \$382 per unit  
- Item_14: \$352 per unit  
- Item_15: \$359 per unit  
- Item_16: \$327 per unit  
- Item_17: \$359 per unit  
- Item_18: \$383 per unit  
- Item_19: \$329 per unit  
- Item_20: \$332 per unit  
- Item_21: \$395 per unit  
- Item_22: \$399 per unit  
- Item_23: \$356 per unit  
- Item_24: \$315 per unit  
- Item_25: \$348 per unit  
- Item_26: \$367 per unit  
- Item_27: \$364 per unit  
- Item_28: \$347 per unit  
- Item_29: \$341 per unit  
- Item_30: \$398 per unit  
- Item_31: \$393 per unit  
- Item_32: \$308 per unit  
- Item_33: \$377 per unit  
- Item_34: \$303 per unit  
- Item_35: \$324 per unit  
- Item_36: \$337 per unit  
- Item_37: \$377 per unit  
- Item_38: \$395 per unit  
- Item_39: \$338 per unit  
- Item_40: \$384 per unit  
- Item_41: \$349 per unit  
- Item_42: \$313 per unit  
- Item_43: \$308 per unit  
- Item_44: \$360 per unit  

#### **Constraints:**
1. **Resource Constraint:**  
   The facility has a limited resource (e.g., raw material, machine hours, or labor) with a total availability of **408 units**. Each product consumes a specific amount of this resource per unit produced, as follows:  
   - Item_0: 0.0123 units per unit produced  
   - Item_1: 0.0167 units per unit produced  
   - Item_2: 0.0147 units per unit produced  
   - Item_3: 0.0145 units per unit produced  
   - Item_4: 0.0122 units per unit produced  
   - Item_5: 0.0130 units per unit produced  
   - Item_6: 0.0145 units per unit produced  
   - Item_7: 0.0112 units per unit produced  
   - Item_8: 0.0112 units per unit produced  
   - Item_9: 0.0156 units per unit produced  
   - Item_10: 0.0115 units per unit produced  
   - Item_11: 0.0123 units per unit produced  
   - Item_12: 0.0123 units per unit produced  
   - Item_13: 0.0149 units per unit produced  
   - Item_14: 0.0120 units per unit produced  
   - Item_15: 0.0152 units per unit produced  
   - Item_16: 0.0139 units per unit produced  
   - Item_17: 0.0164 units per unit produced  
   - Item_18: 0.0135 units per unit produced  
   - Item_19: 0.0164 units per unit produced  
   - Item_20: 0.0114 units per unit produced  
   - Item_21: 0.0118 units per unit produced  
   - Item_22: 0.0145 units per unit produced  
   - Item_23: 0.0114 units per unit produced  
   - Item_24: 0.0154 units per unit produced  
   - Item_25: 0.0119 units per unit produced  
   - Item_26: 0.0119 units per unit produced  
   - Item_27: 0.0164 units per unit produced  
   - Item_28: 0.0164 units per unit produced  
   - Item_29: 0.0119 units per unit produced  
   - Item_30: 0.0145 units per unit produced  
   - Item_31: 0.0115 units per unit produced  
   - Item_32: 0.0147 units per unit produced  
   - Item_33: 0.0120 units per unit produced  
   - Item_34: 0.0112 units per unit produced  
   - Item_35: 0.0164 units per unit produced  
   - Item_36: 0.0132 units per unit produced  
   - Item_37: 0.0112 units per unit produced  
   - Item_38: 0.0128 units per unit produced  
   - Item_39: 0.0116 units per unit produced  
   - Item_40: 0.0127 units per unit produced  
   - Item_41: 0.0167 units per unit produced  
   - Item_42: 0.0152 units per unit produced  
   - Item_43: 0.0137 units per unit produced  
   - Item_44: 0.0123 units per unit produced  

   The total resource consumption across all products must not exceed **408 units**.

2. **Production Limits:**  
   Each product has a maximum production limit due to capacity or demand constraints. These limits are as follows:  
   - Item_0: Up to 667 units  
   - Item_1: Up to 603 units  
   - Item_2: Up to 800 units  
   - Item_3: Up to 689 units  
   - Item_4: Up to 780 units  
   - Item_5: Up to 713 units  
   - Item_6: Up to 778 units  
   - Item_7: Up to 632 units  
   - Item_8: Up to 739 units  
   - Item_9: Up to 771 units  
   - Item_10: Up to 759 units  
   - Item_11: Up to 666 units  
   - Item_12: Up to 798 units  
   - Item_13: Up to 746 units  
   - Item_14: Up to 710 units  
   - Item_15: Up to 738 units  
   - Item_16: Up to 693 units  
   - Item_17: Up to 627 units  
   - Item_18: Up to 721 units  
   - Item_19: Up to 683 units  
   - Item_20: Up to 773 units  
   - Item_21: Up to 687 units  
   - Item_22: Up to 693 units  
   - Item_23: Up to 766 units  
   - Item_24: Up to 751 units  
   - Item_25: Up to 636 units  
   - Item_26: Up to 642 units  
   - Item_27: Up to 726 units  
   - Item_28: Up to 771 units  
   - Item_29: Up to 694 units  
   - Item_30: Up to 628 units  
   - Item_31: Up to 711 units  
   - Item_32: Up to 729 units  
   - Item_33: Up to 664 units  
   - Item_34: Up to 618 units  
   - Item_35: Up to 693 units  
   - Item_36: Up to 642 units  
   - Item_37: Up to 754 units  
   - Item_38: Up to 762 units  
   - Item_39: Up to 751 units  
   - Item_40: Up to 649 units  
   - Item_41: Up to 736 units  
   - Item_42: Up to 638 units  
   - Item_43: Up to 772 units  
   - Item_44: Up to 684 units  

#### **Decision to Make:**
Determine the optimal number of units to produce for each of the 45 products to maximize total profit while staying within the resource limit and respecting the production limits for each product.

#### **Key Considerations:**
- The facility must balance the production of high-profit items with their resource consumption.  
- Some products may be more resource-intensive but offer higher profits, while others may be less resource-intensive but contribute less to the overall profit.  
- The production plan must ensure that no product exceeds its maximum production limit.  

Your task is to determine the optimal production quantities for all 45 products to achieve the highest possible profit while adhering to all constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters from the input dict
    profit_per_unit = params["profit_per_unit"]               # list of 45 floats
    resource_consumption_per_unit = params["resource_consumption_per_unit"]  # list of 45 floats
    resource_availability = params["resource_availability"]   # float
    production_limit = params["production_limit"]             # list of 45 floats

    # Create model
    model = pyo.ConcreteModel()

    # Index set for products
    N = 45
    model.I = pyo.RangeSet(0, N-1)

    # Decision variables: production quantity for each product
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    # Objective: maximize total profit
    model.obj = pyo.Objective(
        expr=sum(profit_per_unit[i] * model.x[i] for i in model.I),
        sense=pyo.maximize
    )

    # Resource constraint
    def resource_rule(model):
        return sum(resource_consumption_per_unit[i] * model.x[i] for i in model.I) <= resource_availability
    model.resource_con = pyo.Constraint(rule=resource_rule)

    # Production limit constraints
    def limit_rule(model, i):
        return model.x[i] <= production_limit[i]
    model.limit_con = pyo.Constraint(model.I, rule=limit_rule)

    # Solve using HiGHS
    solver = Highs()
    results = solver.solve(model)

    # Determine success by checking if objective value is retrievable
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible or solve failed'}
```

## Clique member B-structured

```python
# IR: {"sets":{"ITEMS":"0..44"},"params":{"profit_per_unit[ITEMS]":"unit profit","resource_consumption_per_unit[ITEMS]":"resource per unit","resource_availability":"total available resource","production_limit[ITEMS]":"upper bound per item"},"decision_variables":{"produce[ITEMS]":"NonNegativeReals"},"constraints":["resource_limit: sum(resource_consumption_per_unit[i]*produce[i] for i in ITEMS) <= resource_availability","production_cap[i]: produce[i] <= production_limit[i] for all i in ITEMS"],"objective":"maximize sum(profit_per_unit[i]*produce[i] for i in ITEMS)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    items = list(range(45))

    profit_per_unit = params["profit_per_unit"]
    resource_consumption_per_unit = params["resource_consumption_per_unit"]
    resource_availability = params["resource_availability"]
    production_limit = params["production_limit"]

    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=items, ordered=True)

    model.profit_per_unit = pyo.Param(
        model.ITEMS,
        initialize={idx: profit_per_unit[idx] for idx in items},
        within=pyo.Reals,
    )
    model.resource_consumption_per_unit = pyo.Param(
        model.ITEMS,
        initialize={idx: resource_consumption_per_unit[idx] for idx in items},
        within=pyo.NonNegativeReals,
    )
    model.production_limit = pyo.Param(
        model.ITEMS,
        initialize={idx: production_limit[idx] for idx in items},
        within=pyo.NonNegativeReals,
    )
    model.resource_availability = pyo.Param(
        initialize=resource_availability,
        within=pyo.NonNegativeReals,
    )

    model.produce = pyo.Var(model.ITEMS, domain=pyo.NonNegativeReals)

    def production_cap_rule(model, item_idx):
        return model.produce[item_idx] <= model.production_limit[item_idx]

    model.production_cap = pyo.Constraint(model.ITEMS, rule=production_cap_rule)

    def resource_limit_rule(model):
        return sum(
            model.resource_consumption_per_unit[item_idx] * model.produce[item_idx]
            for item_idx in model.ITEMS
        ) <= model.resource_availability

    model.resource_limit = pyo.Constraint(rule=resource_limit_rule)

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[item_idx] * model.produce[item_idx]
            for item_idx in model.ITEMS
        ),
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
    profit_per_unit = params["profit_per_unit"]
    resource_consumption_per_unit = params["resource_consumption_per_unit"]
    resource_availability = params["resource_availability"]
    production_limit = params["production_limit"]
    
    n_products = 45
    
    model = gp.Model("ProductionPlanning")
    model.Params.LogToConsole = 0
    
    x = model.addVars(n_products, lb=0, name="production")
    
    for i in range(n_products):
        x[i].UB = production_limit[i]
    
    model.setObjective(
        gp.quicksum(profit_per_unit[i] * x[i] for i in range(n_products)),
        GRB.MAXIMIZE
    )
    
    model.addConstr(
        gp.quicksum(resource_consumption_per_unit[i] * x[i] for i in range(n_products)) <= resource_availability,
        name="resource_constraint"
    )
    
    model.optimize()
    
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
