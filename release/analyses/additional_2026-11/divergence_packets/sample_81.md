# sample_81

Decision: ACCEPT, clique ['A-direct', 'C-direct'], informative [0, 1, 2, 3, 4, 5], label 4.0

## Problem text

You are tasked with organizing a shipment of **10 identical crates** to be transported using a fleet of **10 available trucks**. Each crate has a **weight of 28 units**, and each truck has a **maximum capacity of 100 units**. The goal is to minimize the number of trucks used while ensuring that all crates are shipped and no truck exceeds its capacity.

#### Key Details:
1. **Crates and Trucks**: There are 10 crates, each weighing 28 units, and 10 trucks, each with a capacity of 100 units.
2. **Objective**: Minimize the total number of trucks used to transport all the crates.
3. **Constraints**:
   - Each crate must be assigned to exactly one truck.
   - The total weight of crates assigned to any truck cannot exceed its capacity of 100 units.
   - A truck is considered "used" if it carries at least one crate.

#### Decision to Make:
- Determine which crates are assigned to which trucks, ensuring that the total weight on each truck does not exceed 100 units.
- Decide which trucks will be used (i.e., carry at least one crate) to minimize the total number of trucks in operation.

#### Numerical Parameters:
- **Crate Weight**: Each crate weighs 28 units.
- **Truck Capacity**: Each truck can carry up to 100 units.
- **Number of Crates**: 10.
- **Number of Trucks**: 10.

#### Logical Conditions:
- If a truck is used (i.e., assigned at least one crate), it must not exceed its capacity of 100 units.
- Each crate must be assigned to exactly one truck, ensuring no crate is left unshipped.

#### Objective in Context:
Your task is to find the most efficient way to assign the 10 crates to the 10 trucks such that the fewest number of trucks are used, while ensuring that no truck is overloaded and all crates are shipped. This will help reduce transportation costs and optimize resource utilization.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 4.0 (optimal) | 5.0 (optimal) | 4.0 (optimal) | 3.0 (optimal) | 1.0 (optimal) | 1.0 (optimal) |
| B-structured | 4.0 (optimal) | 5.0 (optimal) | 4.0 (optimal) | 3.0 (optimal) | 0.0 (optimal) | 1.0 (optimal) |
| C-direct | 4.0 (optimal) | 5.0 (optimal) | 4.0 (optimal) | 3.0 (optimal) | 1.0 (optimal) | 1.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"crate_weight": 28, "truck_capacity": 100, "num_crates": 10, "num_trucks": 10}`
instance 1: `{"crate_weight": 28.365607907473027, "truck_capacity": 71.50064531336001, "num_crates": 10, "num_trucks": 10}`
instance 2: `{"crate_weight": 34.18827284984074, "truck_capacity": 110.60196924537469, "num_crates": 10, "num_trucks": 10}`
instance 3: `{"crate_weight": 15.315309181116227, "truck_capacity": 71.78783316628422, "num_crates": 10, "num_trucks": 10}`
instance 4: `{"crate_weight": -8.407841818968183, "truck_capacity": 81.93025904119891, "num_crates": 10, "num_trucks": 10}`
instance 5: `{"crate_weight": 3.226437322441802, "truck_capacity": 105.35594103255453, "num_crates": 10, "num_trucks": 10}`

## Extracted specification

```json
{
 "crate_weight": {
  "base": 28,
  "perturb": {
   "mode": "abs",
   "lo": -10.0,
   "hi": 50.0,
   "integer": false
  }
 },
 "truck_capacity": {
  "base": 100,
  "perturb": {
   "mode": "rel",
   "r": 0.3
  }
 },
 "num_crates": {
  "base": 10,
  "perturb": {
   "mode": "abs",
   "lo": 10.0,
   "hi": 10.0,
   "integer": true
  }
 },
 "num_trucks": {
  "base": 10,
  "perturb": {
   "mode": "abs",
   "lo": 10.0,
   "hi": 10.0,
   "integer": true
  }
 }
}
```

## Program A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]
    num_crates = params["num_crates"]
    num_trucks = params["num_trucks"]

    # Create model
    model = pyo.ConcreteModel()

    # Sets
    model.C = pyo.RangeSet(1, num_crates)
    model.T = pyo.RangeSet(1, num_trucks)

    # Variables
    model.x = pyo.Var(model.C, model.T, within=pyo.Binary)  # 1 if crate c assigned to truck t
    model.y = pyo.Var(model.T, within=pyo.Binary)           # 1 if truck t is used

    # Objective: minimize number of trucks used
    model.obj = pyo.Objective(expr=sum(model.y[t] for t in model.T), sense=pyo.minimize)

    # Constraints
    # Each crate assigned to exactly one truck
    def assign_rule(model, c):
        return sum(model.x[c, t] for t in model.T) == 1
    model.assign = pyo.Constraint(model.C, rule=assign_rule)

    # Capacity constraint per truck
    def capacity_rule(model, t):
        return sum(crate_weight * model.x[c, t] for c in model.C) <= truck_capacity * model.y[t]
    model.capacity = pyo.Constraint(model.T, rule=capacity_rule)

    # Linking constraint: if any crate assigned to truck t, y[t] must be 1
    def link_rule(model, c, t):
        return model.x[c, t] <= model.y[t]
    model.link = pyo.Constraint(model.C, model.T, rule=link_rule)

    # Solve
    solver = Highs()
    result = solver.solve(model)

    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible or no solution"}
```

## Program B-structured

```python
# {"sets":{"CRATES":"range(params['num_crates'])","TRUCKS":"range(params['num_trucks'])"},"params":["crate_weight","truck_capacity","num_crates","num_trucks"],"vars":{"assign[i,j]":"Binary","used[j]":"Binary"},"constraints":["each crate i assigned to exactly one truck: sum_j assign[i,j] == 1","truck capacity/use link for each j: crate_weight * sum_i assign[i,j] <= truck_capacity * used[j]"],"objective":"minimize sum_j used[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    num_crates = params["num_crates"]
    num_trucks = params["num_trucks"]
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]

    model.CRATES = pyo.RangeSet(0, num_crates - 1)
    model.TRUCKS = pyo.RangeSet(0, num_trucks - 1)

    model.assign = pyo.Var(model.CRATES, model.TRUCKS, domain=pyo.Binary)
    model.used = pyo.Var(model.TRUCKS, domain=pyo.Binary)

    def one_truck_per_crate_rule(model, crate_idx):
        return sum(model.assign[crate_idx, truck_idx] for truck_idx in model.TRUCKS) == 1

    model.one_truck_per_crate = pyo.Constraint(model.CRATES, rule=one_truck_per_crate_rule)

    def capacity_rule(model, truck_idx):
        return crate_weight * sum(model.assign[crate_idx, truck_idx] for crate_idx in model.CRATES) <= truck_capacity * model.used[truck_idx]

    model.capacity = pyo.Constraint(model.TRUCKS, rule=capacity_rule)

    model.total_trucks_used = pyo.Objective(
        expr=sum(model.used[truck_idx] for truck_idx in model.TRUCKS),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_trucks_used))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]
    num_crates = params["num_crates"]
    num_trucks = params["num_trucks"]
    
    model = gp.Model("crate_shipping")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # x[i,j] = 1 if crate i is assigned to truck j
    x = model.addVars(num_crates, num_trucks, vtype=GRB.BINARY, name="x")
    
    # y[j] = 1 if truck j is used
    y = model.addVars(num_trucks, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in range(num_trucks)), GRB.MINIMIZE)
    
    # Constraint: each crate must be assigned to exactly one truck
    for i in range(num_crates):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_trucks)) == 1,
            name=f"crate_{i}_assigned"
        )
    
    # Constraint: truck capacity cannot be exceeded
    for j in range(num_trucks):
        model.addConstr(
            gp.quicksum(crate_weight * x[i, j] for i in range(num_crates)) <= truck_capacity,
            name=f"truck_{j}_capacity"
        )
    
    # Constraint: truck j is used if at least one crate is assigned to it
    for j in range(num_trucks):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_crates)) <= num_crates * y[j],
            name=f"truck_{j}_used"
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
            "status": "failed"
        }
```
