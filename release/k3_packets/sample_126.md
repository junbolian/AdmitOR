# sample_126

certified: 341795.0
vault label: 351982.0
relative gap: 0.028941820888568167
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

In a large-scale energy distribution network, you are tasked with managing the allocation of electricity generation from multiple power producers to fulfill a set of contractual demands. The goal is to minimize the total production cost while ensuring that all contractual obligations are met and operational constraints are satisfied.

#### **Producers and Contracts**
There are **5 power producers** (Producer 0 to Producer 4) and **7 contracts** (Contract 0 to Contract 6) that need to be fulfilled. Each producer has a limited **generation capacity**, and each contract specifies a **minimum required amount of electricity** that must be delivered. Additionally, each contract requires a **minimum number of contributing producers** to ensure reliability and diversity in the energy supply.

#### **Costs and Capacities**
- **Production Costs**: The cost of generating electricity varies by producer and contract. For example:
  - Producer 0 incurs a cost of **50 units** per unit of electricity delivered to Contract 0, **48 units** for Contract 1, and so on, up to **44 units** for Contract 6.
  - Similarly, Producer 4 has costs ranging from **42 units** for Contract 0 to **44 units** for Contract 6.
- **Producer Capacities**: Each producer has a maximum amount of electricity they can generate:
  - Producer 0 can generate up to **2,712 units**.
  - Producer 1 has a capacity of **1,816 units**.
  - Producer 2 can generate up to **2,983 units**.
  - Producer 3 has a capacity of **2,866 units**.
  - Producer 4 can generate up to **1,897 units**.

#### **Contract Requirements**
- **Minimum Delivery**: Each contract must receive a specific amount of electricity:
  - Contract 0 requires at least **889 units**.
  - Contract 1 requires at least **1,083 units**.
  - Contract 2 requires at least **881 units**.
  - Contract 3 requires at least **1,121 units**.
  - Contract 4 requires at least **1,089 units**.
  - Contract 5 requires at least **921 units**.
  - Contract 6 requires at least **1,059 units**.
- **Minimum Contributors**: Each contract must be fulfilled by a minimum number of producers:
  - Contracts 0, 2, 3, 4, and 6 require at least **2 contributing producers**.
  - Contracts 1 and 5 require at least **3 contributing producers**.

#### **Operational Constraints**
- **Minimum Delivery per Producer**: If a producer contributes to a contract, they must deliver at least a specified minimum amount:
  - Producer 0 must deliver at least **596 units** to any contract they participate in.
  - Producer 1 must deliver at least **399 units**.
  - Producer 2 must deliver at least **656 units**.
  - Producer 3 must deliver at least **630 units**.
  - Producer 4 must deliver at least **417 units**.

#### **Objective**
Your task is to determine the optimal allocation of electricity generation from the producers to the contracts such that:
1. The **total production cost** is minimized.
2. All **contractual demands** are met.
3. Each producer does not exceed their **generation capacity**.
4. Each contract is fulfilled by the **required number of producers**.
5. The **minimum delivery requirements** for each producer-contract pair are satisfied.

This problem requires balancing cost efficiency with operational feasibility, ensuring that the energy distribution network operates reliably and economically.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters from the input dict
    production_cost = params["production_cost"]          # 5x7 matrix
    producer_capacity = params["producer_capacity"]      # length 5 list
    contract_demand = params["contract_demand"]         # length 7 list
    min_contributors = params["min_contributors"]       # length 7 list
    min_delivery_per_producer = params["min_delivery_per_producer"]  # length 5 list

    # Define sets
    producers = range(5)
    contracts = range(7)

    # Create model
    model = pyo.ConcreteModel()

    # Variables
    model.x = pyo.Var(producers, contracts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(producers, contracts, domain=pyo.Binary)

    # Objective: minimize total production cost
    model.obj = pyo.Objective(
        expr=sum(
            production_cost[i][j] * model.x[i, j]
            for i in producers
            for j in contracts
        ),
        sense=pyo.minimize
    )

    # Producer capacity constraints
    def producer_capacity_rule(model, i):
        return sum(model.x[i, j] for j in contracts) <= producer_capacity[i]
    model.producer_capacity_con = pyo.Constraint(producers, rule=producer_capacity_rule)

    # Contract demand constraints
    def contract_demand_rule(model, j):
        return sum(model.x[i, j] for i in producers) >= contract_demand[j]
    model.contract_demand_con = pyo.Constraint(contracts, rule=contract_demand_rule)

    # Minimum contributors per contract
    def min_contributors_rule(model, j):
        return sum(model.y[i, j] for i in producers) >= min_contributors[j]
    model.min_contributors_con = pyo.Constraint(contracts, rule=min_contributors_rule)

    # Linking constraints: if y[i,j]=0 then x[i,j]=0, if y[i,j]=1 then x[i,j] >= min_delivery_per_producer[i]
    def min_delivery_lower_rule(model, i, j):
        return model.x[i, j] >= min_delivery_per_producer[i] * model.y[i, j]
    model.min_delivery_lower_con = pyo.Constraint(producers, contracts, rule=min_delivery_lower_rule)

    def min_delivery_upper_rule(model, i, j):
        return model.x[i, j] <= producer_capacity[i] * model.y[i, j]
    model.min_delivery_upper_con = pyo.Constraint(producers, contracts, rule=min_delivery_upper_rule)

    # Solve
    solver = Highs()
    result = solver.solve(model)

    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible or no solution found"}
```

## Clique member B-structured

```python
# {"sets":{"P":"producers={0,1,2,3,4}","C":"contracts={0,1,2,3,4,5,6}"},"params":{"production_cost":"params['production_cost'][p][c] or params['production_cost'][p,c]","producer_capacity":"params['producer_capacity'][p]","contract_demand":"params['contract_demand'][c]","min_contributors":"params['min_contributors'][c]","min_delivery_per_producer":"params['min_delivery_per_producer'][p]"},"vars":{"x[p,c]":"NonNegativeReals","y[p,c]":"Binary"},"constraints":["producer_capacity: sum_c x[p,c] <= producer_capacity[p] for all p","contract_demand: sum_p x[p,c] >= contract_demand[c] for all c","min_contributors: sum_p y[p,c] >= min_contributors[c] for all c","min_delivery_link: x[p,c] >= min_delivery_per_producer[p]*y[p,c] for all p,c","activation_upper: x[p,c] <= producer_capacity[p]*y[p,c] for all p,c"],"objective":"min sum_{p,c} production_cost[p,c]*x[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = range(5)
    contracts = range(7)

    def get_matrix_value(data, p, c):
        try:
            return data[p][c]
        except Exception:
            return data[p, c]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def objective_rule(model):
        return sum(
            get_matrix_value(params["production_cost"], p, c) * model.x[p, c]
            for p in model.P
            for c in model.C
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def producer_capacity_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= params["producer_capacity"][p]

    model.producer_capacity_con = pyo.Constraint(model.P, rule=producer_capacity_rule)

    def contract_demand_rule(model, c):
        return sum(model.x[p, c] for p in model.P) >= params["contract_demand"][c]

    model.contract_demand_con = pyo.Constraint(model.C, rule=contract_demand_rule)

    def min_contributors_rule(model, c):
        return sum(model.y[p, c] for p in model.P) >= params["min_contributors"][c]

    model.min_contributors_con = pyo.Constraint(model.C, rule=min_contributors_rule)

    def min_delivery_link_rule(model, p, c):
        return model.x[p, c] >= params["min_delivery_per_producer"][p] * model.y[p, c]

    model.min_delivery_link_con = pyo.Constraint(model.P, model.C, rule=min_delivery_link_rule)

    def activation_upper_rule(model, p, c):
        return model.x[p, c] <= params["producer_capacity"][p] * model.y[p, c]

    model.activation_upper_con = pyo.Constraint(model.P, model.C, rule=activation_upper_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]
    
    num_producers = 5
    num_contracts = 7
    
    model = gp.Model("energy_distribution")
    model.Params.OutputFlag = 0
    
    # Decision variables: amount of electricity from producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0, vtype=GRB.CONTINUOUS, name="x")
    
    # Binary variables: whether producer i participates in contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(production_cost[i][j] * x[i, j] 
                    for i in range(num_producers) 
                    for j in range(num_contracts)),
        GRB.MINIMIZE
    )
    
    # Constraint: each producer does not exceed their generation capacity
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"capacity_{i}"
        )
    
    # Constraint: each contract must meet its minimum demand
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}"
        )
    
    # Constraint: each contract must have minimum number of contributing producers
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_contributors[j],
            name=f"min_contrib_{j}"
        )
    
    # Constraint: if producer participates, must deliver minimum amount
    # x[i,j] >= min_delivery_per_producer[i] * y[i,j]
    # x[i,j] <= M * y[i,j] where M is a large enough value (we use producer capacity)
    for i in range(num_producers):
        for j in range(num_contracts):
            # If y[i,j] = 1, then x[i,j] >= min_delivery_per_producer[i]
            model.addConstr(
                x[i, j] >= min_delivery_per_producer[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            # If y[i,j] = 0, then x[i,j] = 0
            model.addConstr(
                x[i, j] <= producer_capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
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
            "status": "failed"
        }
```
