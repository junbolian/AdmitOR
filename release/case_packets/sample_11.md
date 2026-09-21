# sample_11

certified: 10510918.0
vault label: 10622791.791367784
relative gap: 0.010531486784735271
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

You are managing a production facility that manufactures 45 different types of items. Each item has a specific profit margin associated with it, and your goal is to maximize the total profit from production while adhering to resource constraints and production limits.

#### Key Details:
1. **Profit Margins**: Each item generates a specific profit per unit produced. For example:
   - Item 0 yields a profit of 381 units per unit produced.
   - Item 1 yields 336 units, Item 2 yields 352 units, and so on, up to Item 44, which yields 381 units.

2. **Resource Constraint**: The production process relies on a critical resource that is limited to 404 units. Each item consumes a specific fraction of this resource per unit produced. For instance:
   - Producing one unit of Item 0 consumes 0.012048 units of the resource.
   - Producing one unit of Item 1 consumes 0.012821 units, and so on, up to Item 44, which consumes 0.012821 units per unit produced.
   - The total resource consumption across all items must not exceed 404 units.

3. **Production Limits**: Each item has a maximum production capacity due to operational constraints. For example:
   - Item 0 can be produced up to 716 units.
   - Item 1 can be produced up to 606 units, Item 2 up to 635 units, and so on, up to Item 44, which can be produced up to 618 units.
   - Additionally, production quantities cannot be negative; they must be zero or greater.

#### Objective:
Your task is to determine the optimal production quantity for each item to maximize total profit while ensuring that:
- The total resource consumption does not exceed 404 units.
- The production quantity for each item stays within its specified upper limit.
- All production quantities are non-negative.

#### Example:
- If you produce 100 units of Item 0, it would consume 1.2048 units of the resource and contribute 38,100 units to the total profit.
- If you produce 200 units of Item 1, it would consume 2.5642 units of the resource and contribute 67,200 units to the total profit.

By carefully balancing production quantities across all items, you aim to achieve the highest possible profit without violating any constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract parameters
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]
    
    # Number of items
    n_items = 45
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Index set for items
    model.I = pyo.RangeSet(0, n_items - 1)
    
    # Decision variables: production quantity for each item
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    
    # Objective: maximize total profit
    model.profit = pyo.Objective(
        expr=sum(profit_margins[i] * model.x[i] for i in model.I),
        sense=pyo.maximize
    )
    
    # Resource constraint: total resource consumption <= capacity
    def resource_rule(model):
        return sum(resource_coefficients[i] * model.x[i] for i in model.I) <= resource_capacity
    model.resource_constraint = pyo.Constraint(rule=resource_rule)
    
    # Production limits for each item
    def limit_rule(model, i):
        return model.x[i] <= production_limits[i]
    model.production_limits = pyo.Constraint(model.I, rule=limit_rule)
    
    # Solve using HiGHS
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        results = solver.solve(model)
        
        # Check if objective value is retrievable
        obj_val = float(pyo.value(model.profit))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError):
        # Infeasible or other failure
        return {'objective': None, 'status': 'infeasible or failed'}
```

## Clique member B-structured

```python
# IR: {"sets":{"I":"items 0..44"},"params":{"profit_margins":"dict I->float","resource_coefficients":"dict I->float","resource_capacity":"float","production_limits":"dict I->float"},"vars":{"x":"NonNegativeReals indexed by I"},"constraints":["sum(resource_coefficients[i]*x[i] for i in I) <= resource_capacity","x[i] <= production_limits[i] for all i"],"objective":"maximize sum(profit_margins[i]*x[i] for i in I)"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 44)

    model.profit_margins = pyo.Param(model.I, initialize=params["profit_margins"], mutable=False)
    model.resource_coefficients = pyo.Param(model.I, initialize=params["resource_coefficients"], mutable=False)
    model.production_limits = pyo.Param(model.I, initialize=params["production_limits"], mutable=False)
    model.resource_capacity = pyo.Param(initialize=params["resource_capacity"], mutable=False)

    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    def resource_rule(model):
        return sum(model.resource_coefficients[i] * model.x[i] for i in model.I) <= model.resource_capacity
    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def limit_rule(model, i):
        return model.x[i] <= model.production_limits[i]
    model.limit_constraint = pyo.Constraint(model.I, rule=limit_rule)

    model.objective = pyo.Objective(
        expr=sum(model.profit_margins[i] * model.x[i] for i in model.I),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    try:
        obj_val = float(pyo.value(model.objective))
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
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_limits = params["production_limits"]
    
    n_items = len(profit_margins)
    
    try:
        model = gp.Model("production_optimization")
        model.setParam('OutputFlag', 0)
        
        # Decision variables: production quantity for each item
        production = model.addVars(n_items, lb=0, ub=[production_limits[i] for i in range(n_items)], 
                                   vtype=GRB.CONTINUOUS, name="production")
        
        # Objective: maximize total profit
        model.setObjective(
            gp.quicksum(profit_margins[i] * production[i] for i in range(n_items)),
            GRB.MAXIMIZE
        )
        
        # Constraint: total resource consumption must not exceed capacity
        model.addConstr(
            gp.quicksum(resource_coefficients[i] * production[i] for i in range(n_items)) <= resource_capacity,
            name="resource_constraint"
        )
        
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
