# sample_52

certified: 196818.0
vault label: 255724.0
relative gap: 0.2303499084950963
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

You are tasked with managing the distribution of resources from a set of facilities to meet the demands of various customers while minimizing the total cost. The scenario involves four facilities (Facility 0, Facility 1, Facility 2, and Facility 3) and ten customers (Customer 0 through Customer 9). Each facility has a fixed cost associated with opening it, and each customer has a specific demand that must be met. Additionally, each facility has a limited capacity, and there are costs associated with serving each customer from a particular facility.

#### Decisions to Be Made:
1. **Facility Opening Decisions**: Determine whether to open each facility. Opening Facility 0 costs 95,800 units, Facility 1 costs 101,873 units, Facility 2 costs 99,294 units, and Facility 3 costs 99,542 units.
2. **Resource Allocation Decisions**: Decide how much of each customer's demand should be served from each facility. The cost of serving a customer from a facility varies based on the specific facility-customer pair. For example:
   - Serving Customer 0 from Facility 0 costs 34 units, from Facility 1 costs 26 units, from Facility 2 costs 32 units, and from Facility 3 costs 32 units.
   - Similar costs apply for all other customer-facility combinations, with costs ranging from 25 to 35 units per unit of demand served.

#### Objective:
The goal is to minimize the total cost, which includes the fixed costs of opening facilities and the variable costs of serving customers from those facilities.

#### Constraints:
1. **Demand Satisfaction**: Each customer's total demand must be fully met by the sum of resources allocated from all facilities. For example:
   - Customer 0 requires 217 units in total.
   - Customer 1 requires 197 units.
   - Customer 2 requires 194 units.
   - Customer 3 requires 216 units.
   - Customer 4 requires 200 units.
   - Customer 5 requires 192 units.
   - Customer 6 requires 181 units.
   - Customer 7 requires 209 units.
   - Customer 8 requires 192 units.
   - Customer 9 requires 220 units.

2. **Facility Capacity**: The total amount of resources allocated from a facility cannot exceed its capacity. The capacities are as follows:
   - Facility 0 has a capacity of 950 units.
   - Facility 1 has a capacity of 1,009 units.
   - Facility 2 has a capacity of 1,040 units.
   - Facility 3 has a capacity of 1,020 units.

3. **Logical Constraints**: If a facility is not opened, no resources can be allocated from it to any customer. For example:
   - If Facility 0 is not opened, no resources can be shipped from Facility 0 to any customer.
   - Similarly, if Facility 1 is not opened, no resources can be shipped from Facility 1 to any customer, and so on for the other facilities.

#### Summary:
Your task is to decide which facilities to open and how to allocate resources from these facilities to meet the demands of all customers at the lowest possible total cost. The total cost includes both the fixed costs of opening facilities and the variable costs of serving customers from those facilities. All customer demands must be fully satisfied, and the total resources allocated from each facility must not exceed its capacity. Additionally, resources can only be allocated from a facility if it is opened.

This problem requires careful balancing of fixed and variable costs while ensuring that all constraints are met. The solution will determine the optimal set of facilities to open and the optimal allocation of resources to minimize the total cost.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    fixed_costs = params["fixed_costs"]        # list of 4
    serving_costs = params["serving_costs"]    # 4x10 matrix
    demands = params["demands"]                # list of 10
    capacities = params["capacities"]          # list of 4

    # Model
    model = pyo.ConcreteModel()

    # Sets
    model.I = pyo.Set(initialize=range(4))      # facilities
    model.J = pyo.Set(initialize=range(10))     # customers

    # Parameters
    model.fixed_costs = pyo.Param(model.I, initialize=lambda m, i: fixed_costs[i])
    model.serving_costs = pyo.Param(model.I, model.J, initialize=lambda m, i, j: serving_costs[i][j])
    model.demands = pyo.Param(model.J, initialize=lambda m, j: demands[j])
    model.capacities = pyo.Param(model.I, initialize=lambda m, i: capacities[i])

    # Variables
    model.open = pyo.Var(model.I, domain=pyo.Binary)  # 1 if facility i is open
    model.alloc = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)  # amount shipped from i to j

    # Objective
    def total_cost_rule(m):
        fixed = sum(m.fixed_costs[i] * m.open[i] for i in m.I)
        variable = sum(m.serving_costs[i, j] * m.alloc[i, j] for i in m.I for j in m.J)
        return fixed + variable
    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    # Demand satisfaction
    def demand_satisfaction_rule(m, j):
        return sum(m.alloc[i, j] for i in m.I) == m.demands[j]
    model.demand_satisfaction = pyo.Constraint(model.J, rule=demand_satisfaction_rule)

    # Capacity constraints
    def capacity_rule(m, i):
        return sum(m.alloc[i, j] for j in m.J) <= m.capacities[i] * m.open[i]
    model.capacity = pyo.Constraint(model.I, rule=capacity_rule)

    # Solve
    solver = Highs()
    results = solver.solve(model)

    # Extract result
    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible or failed"}
```

## Clique member B-structured

```python
# {"sets":{"facilities":[0,1,2,3],"customers":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_costs":"fixed cost per facility i","serving_costs":"unit serving cost for facility i, customer j","demands":"demand of customer j","capacities":"capacity of facility i"},"variables":{"open_facility":{"type":"binary","index":"i"},"ship":{"type":"nonnegative","index":"(i,j)"}},"constraints":[{"demand_satisfaction":"for each customer j, sum_i ship[i,j] == demands[j]"},{"facility_capacity":"for each facility i, sum_j ship[i,j] <= capacities[i] * open_facility[i]"}],"objective":"minimize sum_i fixed_costs[i]*open_facility[i] + sum_(i,j) serving_costs[i][j]*ship[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = [0, 1, 2, 3]
    customers = list(range(10))

    fixed_costs = params["fixed_costs"]
    serving_costs = params["serving_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities)
    model.customers = pyo.Set(initialize=customers)

    model.open_facility = pyo.Var(model.facilities, domain=pyo.Binary)
    model.ship = pyo.Var(model.facilities, model.customers, domain=pyo.NonNegativeReals)

    def demand_satisfaction_rule(model, customer):
        return sum(model.ship[facility, customer] for facility in model.facilities) == demands[customer]

    model.demand_satisfaction = pyo.Constraint(model.customers, rule=demand_satisfaction_rule)

    def facility_capacity_rule(model, facility):
        return sum(model.ship[facility, customer] for customer in model.customers) <= capacities[facility] * model.open_facility[facility]

    model.facility_capacity = pyo.Constraint(model.facilities, rule=facility_capacity_rule)

    model.total_cost = pyo.Objective(
        expr=
        sum(fixed_costs[facility] * model.open_facility[facility] for facility in model.facilities)
        + sum(serving_costs[facility][customer] * model.ship[facility, customer]
              for facility in model.facilities for customer in model.customers),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    """
    Solve the facility location and allocation problem.
    
    Parameters:
        params (dict): Dictionary containing:
            - fixed_costs: list of fixed costs to open each facility
            - serving_costs: 2D list of costs to serve customer j from facility i
            - demands: list of demands for each customer
            - capacities: list of capacities for each facility
    
    Returns:
        dict: {"objective": float, "status": "optimal"} or 
              {"objective": None, "status": "<reason>"}
    """
    
    fixed_costs = params["fixed_costs"]
    serving_costs = params["serving_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    
    num_facilities = len(fixed_costs)
    num_customers = len(demands)
    
    # Create model
    model = gp.Model("facility_location")
    model.setParam('OutputFlag', 0)
    
    # Decision variables
    # y[i] = 1 if facility i is opened, 0 otherwise
    y = model.addVars(num_facilities, vtype=GRB.BINARY, name="y")
    
    # x[i,j] = amount of demand of customer j served from facility i
    x = model.addVars(num_facilities, num_customers, lb=0, vtype=GRB.CONTINUOUS, name="x")
    
    # Objective: minimize total cost (fixed costs + serving costs)
    fixed_cost_expr = gp.quicksum(fixed_costs[i] * y[i] for i in range(num_facilities))
    serving_cost_expr = gp.quicksum(
        serving_costs[i][j] * x[i, j] 
        for i in range(num_facilities) 
        for j in range(num_customers)
    )
    model.setObjective(fixed_cost_expr + serving_cost_expr, GRB.MINIMIZE)
    
    # Constraint 1: Demand satisfaction
    # Each customer's demand must be fully met
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}"
        )
    
    # Constraint 2: Facility capacity
    # Total allocation from a facility cannot exceed its capacity
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_customers)) <= capacities[i] * y[i],
            name=f"capacity_{i}"
        )
    
    # Solve the model
    model.optimize()
    
    # Extract results
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
            "status": f"status_code_{model.status}"
        }
```
