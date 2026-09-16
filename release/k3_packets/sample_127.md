# sample_127

certified: 1285.0
vault label: 11584.0
relative gap: 0.8890711325966851
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

You are managing the inventory and ordering process for a retail store over a 14-period planning horizon. The goal is to minimize the total cost associated with ordering and holding inventory while ensuring that customer demand is met in each period. The costs include fixed ordering costs, variable ordering costs, and inventory holding costs. 

#### Key Decisions:
1. **Order Placement**: In each period, you must decide whether to place an order (a binary decision: yes or no). Placing an order incurs a fixed cost, which varies by period. For example, placing an order in period 1 costs 97 units, while in period 2, it costs 147 units, and so on.
2. **Order Quantity**: If an order is placed, you must determine the quantity to order. The variable cost per unit ordered also varies by period. For instance, ordering in period 1 costs 8 units per item, while in period 2, it costs 15 units per item, and so on.
3. **Inventory Levels**: You must decide how much inventory to carry over from one period to the next. Holding inventory incurs a cost, which varies by period. For example, holding inventory at the end of period 1 costs 5 units per item, while in period 2, it costs 7 units per item, and so on.

#### Objective:
Minimize the total cost, which includes:
- Fixed ordering costs (if an order is placed in a period),
- Variable ordering costs (based on the quantity ordered),
- Inventory holding costs (based on the amount of inventory carried over).

#### Constraints:
1. **Demand Fulfillment**: In each period, the sum of the inventory carried over from the previous period and the quantity ordered in the current period must equal the sum of the inventory carried over to the next period and the demand for that period. For example:
   - In period 1, the quantity ordered (51 units) must satisfy the demand of 51 units, with no inventory carried over from the previous period.
   - In period 2, the quantity ordered plus the inventory from period 1 must satisfy the demand of 66 units and the inventory carried over to period 3, and so on.

2. **Order Quantity Limits**: If an order is placed in a period, the quantity ordered cannot exceed a maximum limit of 878 units. This ensures that orders are within a feasible range.

3. **Starting and Ending Inventory**: 
   - At the start of the planning horizon (period 1), there is no initial inventory.
   - At the end of the planning horizon (period 14), there should be no remaining inventory.

#### Numerical Parameters:
- **Fixed Ordering Costs**: Vary by period, ranging from 92 units in period 11 to 147 units in periods 2 and 9.
- **Variable Ordering Costs**: Vary by period, ranging from 5 units in period 14 to 15 units in periods 2 and 8.
- **Inventory Holding Costs**: Vary by period, ranging from 5 units in period 1 to 10 units in periods 3, 6, and 11.
- **Demand**: Varies by period, with values such as 51 units in period 1, 66 units in period 2, and so on, up to 63 units in period 14.

#### Goal:
Determine the optimal ordering and inventory strategy over the 14-period horizon to minimize total costs while ensuring all customer demands are met and all constraints are satisfied.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    T = 14  # number of periods
    
    # Extract parameters
    fixed_ordering_cost = params["fixed_ordering_cost"]  # list length T
    variable_ordering_cost = params["variable_ordering_cost"]  # list length T
    holding_cost = params["holding_cost"]  # list length T
    demand = params["demand"]  # list length T
    max_order_quantity = params["max_order_quantity"]  # scalar
    
    # Validate lengths
    if not (len(fixed_ordering_cost) == len(variable_ordering_cost) == 
            len(holding_cost) == len(demand) == T):
        return {"objective": None, "status": "parameter length mismatch"}
    
    model = pyo.ConcreteModel()
    
    # Sets
    model.T = pyo.RangeSet(0, T)  # 0 for initial period, T for final inventory
    model.T_periods = pyo.RangeSet(1, T)  # ordering periods
    
    # Variables
    model.order_quantity = pyo.Var(model.T_periods, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.order_placed = pyo.Var(model.T_periods, domain=pyo.Binary)
    
    # Objective
    def total_cost_rule(m):
        fixed = sum(fixed_ordering_cost[t-1] * m.order_placed[t] for t in m.T_periods)
        variable = sum(variable_ordering_cost[t-1] * m.order_quantity[t] for t in m.T_periods)
        holding = sum(holding_cost[t-1] * m.inventory[t] for t in m.T_periods)
        return fixed + variable + holding
    
    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
    
    # Constraints
    
    # Inventory balance
    def inventory_balance_rule(m, t):
        if t == -1:
            return pyo.Constraint.Skip
        if t == 1:
            return m.inventory[0] + m.order_quantity[t] == demand[t-1] + m.inventory[t]
        return m.inventory[t-1] + m.order_quantity[t] == demand[t-1] + m.inventory[t]
    
    model.inventory_balance = pyo.Constraint(model.T_periods, rule=inventory_balance_rule)
    
    # Order quantity limits
    def order_limit_rule(m, t):
        return m.order_quantity[t] <= max_order_quantity * m.order_placed[t]
    
    model.order_limit = pyo.Constraint(model.T_periods, rule=order_limit_rule)
    
    # Initial inventory
    def initial_inventory_rule(m):
        return m.inventory[0] == 0
    
    model.initial_inventory = pyo.Constraint(rule=initial_inventory_rule)
    
    # Final inventory
    def final_inventory_rule(m):
        return m.inventory[T] == 0
    
    model.final_inventory = pyo.Constraint(rule=final_inventory_rule)
    
    # Solve
    solver = Highs()
    results = solver.solve(model)
    
    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible or no solution"}
```

## Clique member B-structured

```python
# {"sets":{"T":"periods 1..14"},"params":{"fixed_ordering_cost":"dict/list indexed by t","variable_ordering_cost":"dict/list indexed by t","holding_cost":"dict/list indexed by t","demand":"dict/list indexed by t","max_order_quantity":"scalar"},"decision_variables":{"order_qty":{"type":"NonNegativeReals","index":"T"},"inventory":{"type":"NonNegativeReals","index":"T"},"place_order":{"type":"Binary","index":"T"}},"constraints":["inventory_balance[t]: prev_inventory + order_qty[t] = demand[t] + inventory[t], with prev_inventory=0 for t=1","order_limit[t]: order_qty[t] <= max_order_quantity * place_order[t]","ending_inventory: inventory[14] = 0"],"objective":"min sum_t fixed_ordering_cost[t]*place_order[t] + variable_ordering_cost[t]*order_qty[t] + holding_cost[t]*inventory[t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    periods = list(range(1, 15))
    model.T = pyo.Set(initialize=periods, ordered=True)

    def _get_series(name):
        data = params[name]
        if isinstance(data, dict):
            return {period: float(data[period]) for period in periods}
        return {period: float(data[period - 1]) for period in periods}

    fixed_ordering_cost = _get_series("fixed_ordering_cost")
    variable_ordering_cost = _get_series("variable_ordering_cost")
    holding_cost = _get_series("holding_cost")
    demand = _get_series("demand")
    max_order_quantity = float(params["max_order_quantity"])

    model.order_qty = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.place_order = pyo.Var(model.T, domain=pyo.Binary)

    def inventory_balance_rule(model, period):
        prev_inventory = 0.0 if period == 1 else model.inventory[period - 1]
        return prev_inventory + model.order_qty[period] == demand[period] + model.inventory[period]

    model.inventory_balance = pyo.Constraint(model.T, rule=inventory_balance_rule)

    def order_limit_rule(model, period):
        return model.order_qty[period] <= max_order_quantity * model.place_order[period]

    model.order_limit = pyo.Constraint(model.T, rule=order_limit_rule)
    model.ending_inventory = pyo.Constraint(expr=model.inventory[14] == 0)

    model.total_cost = pyo.Objective(
        expr=sum(
            fixed_ordering_cost[period] * model.place_order[period]
            + variable_ordering_cost[period] * model.order_qty[period]
            + holding_cost[period] * model.inventory[period]
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read parameters
    fixed_ordering_cost = params["fixed_ordering_cost"]
    variable_ordering_cost = params["variable_ordering_cost"]
    holding_cost = params["holding_cost"]
    demand = params["demand"]
    max_order_quantity = params["max_order_quantity"]
    
    # Problem structure
    num_periods = 14
    periods = range(num_periods)
    
    # Create model
    model = gp.Model("inventory_optimization")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # Binary variable: whether to place an order in period t
    order_placed = model.addVars(periods, vtype=GRB.BINARY, name="order_placed")
    
    # Continuous variable: quantity ordered in period t
    order_quantity = model.addVars(periods, lb=0, vtype=GRB.CONTINUOUS, name="order_quantity")
    
    # Continuous variable: inventory at end of period t
    inventory = model.addVars(periods, lb=0, vtype=GRB.CONTINUOUS, name="inventory")
    
    # Objective: minimize total cost
    fixed_cost = gp.quicksum(fixed_ordering_cost[t] * order_placed[t] for t in periods)
    variable_cost = gp.quicksum(variable_ordering_cost[t] * order_quantity[t] for t in periods)
    holding_cost_total = gp.quicksum(holding_cost[t] * inventory[t] for t in periods)
    
    model.setObjective(fixed_cost + variable_cost + holding_cost_total, GRB.MINIMIZE)
    
    # Constraints
    # Demand fulfillment: inventory balance equation
    for t in periods:
        if t == 0:
            # Period 0: no initial inventory
            model.addConstr(
                order_quantity[t] == demand[t] + inventory[t],
                name=f"demand_fulfillment_{t}"
            )
        else:
            # Other periods: inventory from previous period + order = demand + ending inventory
            model.addConstr(
                inventory[t-1] + order_quantity[t] == demand[t] + inventory[t],
                name=f"demand_fulfillment_{t}"
            )
    
    # Ending inventory constraint: no inventory at end of planning horizon
    model.addConstr(inventory[num_periods - 1] == 0, name="ending_inventory")
    
    # Order quantity limits: can only order if order is placed, and cannot exceed max
    for t in periods:
        model.addConstr(
            order_quantity[t] <= max_order_quantity * order_placed[t],
            name=f"order_limit_{t}"
        )
    
    # Solve
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
            "status": "failed"
        }
```
