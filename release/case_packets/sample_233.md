# sample_233

certified: 122841.99999999993
vault label: 122814.0
relative gap: 0.00022798703730785773
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 4

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

There are four energy producers (Producer 0, Producer 1, Producer 2, and Producer 3) and five contracts (Contract 0, Contract 1, Contract 2, Contract 3, and Contract 4). Each producer has a limited capacity for electricity generation, and each contract specifies a minimum amount of electricity that must be delivered. Additionally, each contract requires a minimum number of producers to contribute to its fulfillment. The cost of generating electricity varies depending on the producer and the contract. The unit production costs (per unit of electricity) are as follows: Producer 0 costs 20 for Contract 0, 34 for Contract 1, 26 for Contract 2, 28 for Contract 3, and 30 for Contract 4. Producer 1 costs 34 for Contract 0, 33 for Contract 1, 28 for Contract 2, 36 for Contract 3, and 38 for Contract 4. Producer 2 costs 23 for Contract 0, 29 for Contract 1, 28 for Contract 2, 30 for Contract 3, and 34 for Contract 4. Producer 3 costs 28 for Contract 0, 21 for Contract 1, 22 for Contract 2, 31 for Contract 3, and 31 for Contract 4. Each producer has a maximum capacity for electricity generation: Producer 0 can generate up to 1,204 units, Producer 1 up to 1,596 units, Producer 2 up to 1,653 units, and Producer 3 up to 1,303 units. Each contract has a minimum electricity delivery requirement: Contract 0 requires 950 units, Contract 1 requires 989 units, Contract 2 requires 860 units, Contract 3 requires 795 units, and Contract 4 requires 899 units. Additionally, each contract requires a minimum number of producers to contribute: Contract 0 requires at least 3 producers, Contract 1 requires at least 3 producers, Contract 2 requires at least 3 producers, Contract 3 requires at least 2 producers, and Contract 4 requires at least 3 producers. If a producer is assigned to a contract, they must deliver at least a specified minimum amount of electricity: Producer 0 must deliver at least 240 units per contract, Producer 1 must deliver at least 319 units per contract, Producer 2 must deliver at least 330 units per contract, and Producer 3 must deliver at least 260 units per contract. The goal is to determine how much electricity each producer should generate for each contract to minimize the total production cost, ensuring no producer exceeds their maximum capacity, each contract receives at least the required amount of electricity, each contract has the required number of contributing producers, and if a producer is assigned to a contract, they deliver at least their minimum required amount.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract all parameters from the dict
    unit_cost = params["unit_cost"]  # dict of dicts: [i][j]
    producer_capacity = params["producer_capacity"]  # dict: i -> capacity
    contract_demand = params["contract_demand"]  # dict: j -> demand
    min_producers_per_contract = params["min_producers_per_contract"]  # dict: j -> min producers
    min_delivery_if_assigned = params["min_delivery_if_assigned"]  # dict: i -> min amount
    
    # Define sets
    producers = list(range(4))  # 0..3
    contracts = list(range(5))  # 0..4
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Variables
    model.x = pyo.Var(producers, contracts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(producers, contracts, domain=pyo.Binary)
    
    # Objective: minimize total cost
    model.obj = pyo.Objective(
        expr=sum(unit_cost[i][j] * model.x[i, j] for i in producers for j in contracts),
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
    
    # Minimum producers per contract constraints
    def min_producers_rule(model, j):
        return sum(model.y[i, j] for i in producers) >= min_producers_per_contract[j]
    model.min_producers_con = pyo.Constraint(contracts, rule=min_producers_rule)
    
    # Linking constraints: if y[i,j]=0 then x[i,j]=0, if y[i,j]=1 then x[i,j] >= min_delivery_if_assigned[i]
    def linking_lower_rule(model, i, j):
        return model.x[i, j] >= min_delivery_if_assigned[i] * model.y[i, j]
    model.linking_lower_con = pyo.Constraint(producers, contracts, rule=linking_lower_rule)
    
    def linking_upper_rule(model, i, j):
        return model.x[i, j] <= producer_capacity[i] * model.y[i, j]
    model.linking_upper_con = pyo.Constraint(producers, contracts, rule=linking_upper_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution exists and objective value is retrievable
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError):
        return {'objective': None, 'status': 'infeasible or no solution'}
```

## Clique member B-structured

```python
# IR: {"sets":{"P":"producers=range(4)","C":"contracts=range(5)"},"params":{"unit_cost":"params['unit_cost'][p][c]","producer_capacity":"params['producer_capacity'][p]","contract_demand":"params['contract_demand'][c]","min_producers_per_contract":"params['min_producers_per_contract'][c]","min_delivery_if_assigned":"params['min_delivery_if_assigned'][p]"},"vars":{"x[p,c]":"NonNegativeReals","y[p,c]":"Binary"},"constraints":["producer_capacity_limit[p]: sum_c x[p,c] <= producer_capacity[p]","contract_demand_min[c]: sum_p x[p,c] >= contract_demand[c]","min_producers_count[c]: sum_p y[p,c] >= min_producers_per_contract[c]","min_delivery_link[p,c]: x[p,c] >= min_delivery_if_assigned[p]*y[p,c]","max_delivery_link[p,c]: x[p,c] <= producer_capacity[p]*y[p,c]"],"objective":"min sum_{p,c} unit_cost[p][c]*x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    producers = range(4)
    contracts = range(5)

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def producer_capacity_limit_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= params["producer_capacity"][p]

    model.producer_capacity_limit = pyo.Constraint(model.P, rule=producer_capacity_limit_rule)

    def contract_demand_min_rule(model, c):
        return sum(model.x[p, c] for p in model.P) >= params["contract_demand"][c]

    model.contract_demand_min = pyo.Constraint(model.C, rule=contract_demand_min_rule)

    def min_producers_count_rule(model, c):
        return sum(model.y[p, c] for p in model.P) >= params["min_producers_per_contract"][c]

    model.min_producers_count = pyo.Constraint(model.C, rule=min_producers_count_rule)

    def min_delivery_link_rule(model, p, c):
        return model.x[p, c] >= params["min_delivery_if_assigned"][p] * model.y[p, c]

    model.min_delivery_link = pyo.Constraint(model.P, model.C, rule=min_delivery_link_rule)

    def max_delivery_link_rule(model, p, c):
        return model.x[p, c] <= params["producer_capacity"][p] * model.y[p, c]

    model.max_delivery_link = pyo.Constraint(model.P, model.C, rule=max_delivery_link_rule)

    model.total_cost = pyo.Objective(
        expr=sum(params["unit_cost"][p][c] * model.x[p, c] for p in model.P for c in model.C),
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
    unit_cost = params["unit_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    min_delivery_if_assigned = params["min_delivery_if_assigned"]
    
    num_producers = 4
    num_contracts = 5
    
    model = gp.Model("energy_allocation")
    model.Params.LogToConsole = 0
    
    # Decision variables
    # x[i, j]: amount of electricity producer i delivers to contract j
    x = model.addVars(num_producers, num_contracts, lb=0, vtype=GRB.CONTINUOUS, name="x")
    
    # y[i, j]: binary variable indicating if producer i is assigned to contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")
    
    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(unit_cost[i][j] * x[i, j] 
                    for i in range(num_producers) 
                    for j in range(num_contracts)),
        GRB.MINIMIZE
    )
    
    # Constraints
    # 1. Producer capacity constraints
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"capacity_{i}"
        )
    
    # 2. Contract demand constraints
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}"
        )
    
    # 3. Minimum number of producers per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_producers_per_contract[j],
            name=f"min_producers_{j}"
        )
    
    # 4. Minimum delivery if assigned (linking constraints)
    for i in range(num_producers):
        for j in range(num_contracts):
            # If y[i,j] = 1, then x[i,j] >= min_delivery_if_assigned[i]
            model.addConstr(
                x[i, j] >= min_delivery_if_assigned[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            
            # If y[i,j] = 0, then x[i,j] = 0 (upper bound constraint)
            # x[i,j] <= M * y[i,j] where M is a big enough constant
            big_m = producer_capacity[i]
            model.addConstr(
                x[i, j] <= big_m * y[i, j],
                name=f"assignment_{i}_{j}"
            )
    
    # Optimize
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
