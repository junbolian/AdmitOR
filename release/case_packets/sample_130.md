# sample_130

certified: 98563.99999999999
vault label: 126431.0
relative gap: 0.22041271523597863
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

You are managing a network of energy producers tasked with fulfilling a set of energy supply contracts. The goal is to allocate energy production across multiple producers to meet the demands of various contracts while minimizing the total production cost. Each producer has a limited capacity, and each contract has specific requirements that must be satisfied.

#### Key Details:
1. **Producers and Contracts**:
   - There are **4 producers** (Producer 0, Producer 1, Producer 2, Producer 3) and **5 contracts** (Contract 0, Contract 1, Contract 2, Contract 3, Contract 4).
   - Each producer has a maximum production capacity:
     - Producer 0: **1,524 units**
     - Producer 1: **1,541 units**
     - Producer 2: **1,553 units**
     - Producer 3: **1,505 units**
   - Each contract has a minimum energy requirement:
     - Contract 0: **841 units**
     - Contract 1: **812 units**
     - Contract 2: **837 units**
     - Contract 3: **850 units**
     - Contract 4: **818 units**

2. **Production Costs**:
   - The cost of producing energy varies by producer and contract. For example:
     - Producer 0 incurs a cost of **31 units** per unit of energy delivered to Contract 0, **31 units** for Contract 1, and so on.
     - Producer 1 has costs ranging from **30 to 32 units** depending on the contract.
     - Similar cost structures apply to Producers 2 and 3.

3. **Constraints**:
   - **Capacity Constraints**: The total energy allocated to all contracts by a single producer cannot exceed their capacity. For example:
     - Producer 0 cannot allocate more than **1,524 units** across all contracts.
   - **Contract Fulfillment**: The total energy allocated to each contract by all producers must meet or exceed the contract's minimum requirement. For example:
     - Contract 0 must receive at least **841 units** from the combined allocations of all producers.
   - **Minimum Contributors**: Each contract must be fulfilled by at least **2 producers**. This ensures diversification of supply sources.
   - **Minimum Delivery**: If a producer contributes to a contract, they must deliver at least a specified minimum amount:
     - Producer 0: **381 units** per contract
     - Producer 1: **385 units** per contract
     - Producer 2: **388 units** per contract
     - Producer 3: **376 units** per contract

4. **Objective**:
   - Minimize the **total production cost** across all producers and contracts while satisfying all constraints.

#### Summary:
Your task is to determine how much energy each producer should allocate to each contract to meet all requirements at the lowest possible cost. This involves balancing the producers' capacities, ensuring contracts are fulfilled by multiple sources, and adhering to minimum delivery thresholds. The solution must respect all constraints while optimizing the overall cost structure.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    producer_capacities = params["producer_capacities"]  # list of 4
    contract_demands = params["contract_demands"]        # list of 5
    cost_matrix = params["cost_matrix"]                  # 4x5 list of lists
    min_delivery_per_contract = params["min_delivery_per_contract"]  # list of 4

    # Sets
    I = range(4)  # producers
    J = range(5)  # contracts

    # Model
    model = pyo.ConcreteModel()

    # Variables
    model.x = pyo.Var(I, J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(I, J, domain=pyo.Binary)  # 1 if producer i supplies contract j

    # Objective: minimize total cost
    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for i in I for j in J),
        sense=pyo.minimize
    )

    # Capacity constraints
    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in J) <= producer_capacities[i]
    model.capacity_con = pyo.Constraint(I, rule=capacity_rule)

    # Contract demand constraints
    def demand_rule(model, j):
        return sum(model.x[i, j] for i in I) >= contract_demands[j]
    model.demand_con = pyo.Constraint(J, rule=demand_rule)

    # Minimum delivery if participating (big-M)
    M = max(producer_capacities)  # large enough upper bound
    def min_delivery_rule1(model, i, j):
        return model.x[i, j] >= min_delivery_per_contract[i] * model.y[i, j]
    model.min_delivery_con1 = pyo.Constraint(I, J, rule=min_delivery_rule1)

    def min_delivery_rule2(model, i, j):
        return model.x[i, j] <= M * model.y[i, j]
    model.min_delivery_con2 = pyo.Constraint(I, J, rule=min_delivery_rule2)

    # At least 2 producers per contract
    def min_producers_rule(model, j):
        return sum(model.y[i, j] for i in I) >= 2
    model.min_producers_con = pyo.Constraint(J, rule=min_producers_rule)

    # Solve
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        # If objective cannot be evaluated, assume infeasible/unbounded
        return {"objective": None, "status": f"solver_error: {str(e)}"}
```

## Clique member B-structured

```python
# {"sets":{"P":"producers","C":"contracts"},"params":["producer_capacities","contract_demands","cost_matrix","min_delivery_per_contract"],"vars":{"x":{"type":"continuous","domain":"NonNegativeReals","index":["P","C"]},"y":{"type":"binary","domain":"Binary","index":["P","C"]}},"constraints":["sum_c x[p,c] <= producer_capacities[p] for all p","sum_p x[p,c] >= contract_demands[c] for all c","sum_p y[p,c] >= 2 for all c","x[p,c] >= min_delivery_per_contract[p] * y[p,c] for all p,c","x[p,c] <= producer_capacities[p] * y[p,c] for all p,c"],"objective":"minimize sum_p sum_c cost_matrix[p][c] * x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacities = params["producer_capacities"]
    contract_demands = params["contract_demands"]
    cost_matrix = params["cost_matrix"]
    min_delivery_per_contract = params["min_delivery_per_contract"]

    num_producers = 4
    num_contracts = 5

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, num_producers - 1)
    model.C = pyo.RangeSet(0, num_contracts - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost_matrix[p][c] * model.x[p, c] for p in model.P for c in model.C)

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def producer_capacity_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= producer_capacities[p]

    model.producer_capacity = pyo.Constraint(model.P, rule=producer_capacity_rule)

    def contract_demand_rule(model, c):
        return sum(model.x[p, c] for p in model.P) >= contract_demands[c]

    model.contract_demand = pyo.Constraint(model.C, rule=contract_demand_rule)

    def min_contributors_rule(model, c):
        return sum(model.y[p, c] for p in model.P) >= 2

    model.min_contributors = pyo.Constraint(model.C, rule=min_contributors_rule)

    def min_delivery_rule(model, p, c):
        return model.x[p, c] >= min_delivery_per_contract[p] * model.y[p, c]

    model.min_delivery = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    def link_rule(model, p, c):
        return model.x[p, c] <= producer_capacities[p] * model.y[p, c]

    model.link = pyo.Constraint(model.P, model.C, rule=link_rule)

    solver = Highs()
    solver.solve(model)

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
    # Read parameters
    producer_capacities = params["producer_capacities"]
    contract_demands = params["contract_demands"]
    cost_matrix = params["cost_matrix"]
    min_delivery_per_contract = params["min_delivery_per_contract"]
    
    # Derive dimensions
    num_producers = len(producer_capacities)
    num_contracts = len(contract_demands)
    
    # Create model
    model = gp.Model("energy_allocation")
    model.setParam('OutputFlag', 0)
    
    # Decision variables: x[i,j] = energy from producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0, name="x")
    
    # Binary variables: y[i,j] = 1 if producer i participates in contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize total cost
    obj = gp.quicksum(cost_matrix[i][j] * x[i, j] 
                      for i in range(num_producers) 
                      for j in range(num_contracts))
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraint 1: Producer capacity constraints
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacities[i],
            name=f"capacity_{i}"
        )
    
    # Constraint 2: Contract demand constraints
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demands[j],
            name=f"demand_{j}"
        )
    
    # Constraint 3: Minimum delivery if participating
    # If y[i,j] = 1, then x[i,j] >= min_delivery_per_contract[i]
    # If y[i,j] = 0, then x[i,j] = 0
    M = max(producer_capacities)  # Big-M value
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i,j] >= min_delivery_per_contract[i] * y[i,j]
            model.addConstr(
                x[i, j] >= min_delivery_per_contract[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            # x[i,j] <= M * y[i,j] (if not participating, x must be 0)
            model.addConstr(
                x[i, j] <= M * y[i, j],
                name=f"participation_{i}_{j}"
            )
    
    # Constraint 4: Each contract must have at least 2 producers
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= 2,
            name=f"min_producers_{j}"
        )
    
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
            "status": f"gurobi_status_{model.status}"
        }
```
