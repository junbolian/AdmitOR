# sample_167

certified: 137033.0
vault label: 299884.0
relative gap: 0.5430466447026183
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

Imagine you are managing a network of energy producers who must fulfill contracts for delivering electricity to various regions. Your goal is to allocate the electricity generation from each producer to the contracts in a way that minimizes the total production cost while ensuring all contractual obligations are met.

#### **Producers and Contracts**
There are six energy producers (Producer 0 to Producer 5) and six contracts (Contract 0 to Contract 5). Each producer has a limited capacity for electricity generation, and each contract has a specific demand that must be fulfilled. The producers also have minimum delivery requirements if they are chosen to contribute to a contract.

#### **Production Costs**
The cost of generating electricity varies depending on the producer and the contract. For example:
- Producer 0 incurs a cost of 43 units per unit of electricity delivered to Contract 0, 46 units for Contract 1, and so on.
- Producer 1 has costs of 41 units for Contract 0, 44 units for Contract 1, etc.
- Similar cost structures apply to the other producers, with costs ranging from 40 to 50 units per unit of electricity.

#### **Producer Capacities**
Each producer has a maximum capacity for electricity generation:
- Producer 0 can generate up to 2,167 units.
- Producer 1 can generate up to 1,875 units.
- Producer 2 can generate up to 2,570 units.
- Producer 3 can generate up to 2,650 units.
- Producer 4 can generate up to 2,340 units.
- Producer 5 can generate up to 2,297 units.

#### **Contract Demands**
Each contract has a minimum electricity requirement that must be met:
- Contract 0 requires at least 971 units.
- Contract 1 requires at least 1,005 units.
- Contract 2 requires at least 871 units.
- Contract 3 requires at least 1,039 units.
- Contract 4 requires at least 1,051 units.
- Contract 5 requires at least 1,106 units.

#### **Minimum Contributors**
Each contract must be fulfilled by a minimum number of producers:
- Contracts 0, 1, 4, and 5 require at least 2 contributing producers.
- Contracts 2 and 3 require at least 3 contributing producers.

#### **Minimum Delivery Requirements**
If a producer is selected to contribute to a contract, they must deliver at least a specified minimum amount of electricity:
- Producer 0 must deliver at least 476 units if contributing to any contract.
- Producer 1 must deliver at least 412 units.
- Producer 2 must deliver at least 565 units.
- Producer 3 must deliver at least 583 units.
- Producer 4 must deliver at least 514 units.
- Producer 5 must deliver at least 505 units.

#### **Objective**
Your task is to determine how much electricity each producer should allocate to each contract to minimize the total production cost while ensuring:
1. No producer exceeds their generation capacity.
2. All contract demands are met.
3. Each contract has the required number of contributing producers.
4. If a producer contributes to a contract, they meet the minimum delivery requirement.

By carefully balancing these constraints, you aim to find the most cost-effective allocation of electricity generation across the network.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    cost = params["cost"]           # cost[i][j]
    capacity = params["capacity"]   # capacity[i]
    demand = params["demand"]       # demand[j]
    min_delivery = params["min_delivery"]           # min_delivery[i]
    min_contributors = params["min_contributors"]   # min_contributors[j]

    # Sets
    I = range(6)   # producers 0..5
    J = range(6)   # contracts 0..5

    # Model
    model = pyo.ConcreteModel()

    # Variables
    model.x = pyo.Var(I, J, within=pyo.NonNegativeReals)
    model.y = pyo.Var(I, J, within=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in I for j in J),
        sense=pyo.minimize
    )

    # Capacity constraints
    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in J) <= capacity[i]
    model.capacity_con = pyo.Constraint(I, rule=capacity_rule)

    # Demand constraints
    def demand_rule(model, j):
        return sum(model.x[i, j] for i in I) >= demand[j]
    model.demand_con = pyo.Constraint(J, rule=demand_rule)

    # Minimum delivery if contributing (big‑M)
    def min_delivery_rule(model, i, j):
        return model.x[i, j] >= min_delivery[i] * model.y[i, j]
    model.min_delivery_con = pyo.Constraint(I, J, rule=min_delivery_rule)

    # Upper bound linking x and y (x <= capacity[i] * y)
    def link_rule(model, i, j):
        return model.x[i, j] <= capacity[i] * model.y[i, j]
    model.link_con = pyo.Constraint(I, J, rule=link_rule)

    # Minimum number of contributors per contract
    def min_contributors_rule(model, j):
        return sum(model.y[i, j] for i in I) >= min_contributors[j]
    model.min_contributors_con = pyo.Constraint(J, rule=min_contributors_rule)

    # Solve
    solver = Highs()
    result = solver.solve(model)

    # Check if solution is available
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible or no solution"}
```

## Clique member B-structured

```python
# {"sets":{"producers":"range(6)","contracts":"range(6)"},"params":{"cost":"cost[i][j] or cost[i,j]","capacity":"capacity[i]","demand":"demand[j]","min_delivery":"min_delivery[i]","min_contributors":"min_contributors[j]"},"variables":{"x[i,j]":"NonNegativeReals","y[i,j]":"Binary"},"constraints":["sum_j x[i,j] <= capacity[i] for each producer i","sum_i x[i,j] >= demand[j] for each contract j","sum_i y[i,j] >= min_contributors[j] for each contract j","x[i,j] >= min_delivery[i] * y[i,j] for each producer-contract pair (i,j)","x[i,j] <= capacity[i] * y[i,j] for each producer-contract pair (i,j)"],"objective":"minimize sum_{i,j} cost[i,j] * x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = range(6)
    contracts = range(6)

    def get_1d(data, idx):
        try:
            return data[idx]
        except Exception:
            return data[str(idx)]

    def get_2d(data, idx1, idx2):
        try:
            return data[idx1][idx2]
        except Exception:
            try:
                return data[idx1, idx2]
            except Exception:
                try:
                    return data[str(idx1)][str(idx2)]
                except Exception:
                    return data[f"{idx1},{idx2}"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(model, producer):
        return sum(model.x[producer, contract] for contract in model.C) <= get_1d(params["capacity"], producer)
    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(model, contract):
        return sum(model.x[producer, contract] for producer in model.P) >= get_1d(params["demand"], contract)
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def contributors_rule(model, contract):
        return sum(model.y[producer, contract] for producer in model.P) >= get_1d(params["min_contributors"], contract)
    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    def min_delivery_rule(model, producer, contract):
        return model.x[producer, contract] >= get_1d(params["min_delivery"], producer) * model.y[producer, contract]
    model.min_delivery_con = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    def linking_rule(model, producer, contract):
        return model.x[producer, contract] <= get_1d(params["capacity"], producer) * model.y[producer, contract]
    model.linking_con = pyo.Constraint(model.P, model.C, rule=linking_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            get_2d(params["cost"], producer, contract) * model.x[producer, contract]
            for producer in model.P
            for contract in model.C
        ),
        sense=pyo.minimize,
    )

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
    # Read parameters
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]
    
    # Infer dimensions
    num_producers = len(capacity)
    num_contracts = len(demand)
    
    # Create model
    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0
    
    # Decision variables
    # x[i,j] = amount of electricity from producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0, vtype=GRB.CONTINUOUS, name="x")
    
    # y[i,j] = 1 if producer i contributes to contract j, 0 otherwise
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize total production cost
    obj = gp.quicksum(cost[i][j] * x[i, j] 
                      for i in range(num_producers) 
                      for j in range(num_contracts))
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraints
    
    # 1. Producer capacity constraints
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= capacity[i],
            name=f"capacity_{i}"
        )
    
    # 2. Contract demand constraints
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= demand[j],
            name=f"demand_{j}"
        )
    
    # 3. Minimum contributors per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_contributors[j],
            name=f"min_contributors_{j}"
        )
    
    # 4. Minimum delivery if contributing (big-M constraints)
    # If y[i,j] = 1, then x[i,j] >= min_delivery[i]
    # If y[i,j] = 0, then x[i,j] = 0
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i,j] >= min_delivery[i] * y[i,j]
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            # x[i,j] <= capacity[i] * y[i,j] (link x to y)
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
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
            "status": f"status_{model.status}"
        }
```
