# sample_179

certified: 329050.0
vault label: 338348.0
relative gap: 0.02748058212254838
clique: ['A-direct', 'B-structured', 'C-direct']  informative: 5

## Classification (fill in)
[ ] (a) gate model defect: text states a constraint the
        clique's model drops or misreads
[ ] (b) label error: text has one reasonable reading and the
        clique's value is correct under it
[ ] (c) ambiguity: text supports multiple readings; clique's
        reading is legitimate but differs from the labeler's
notes:

## Problem text

Imagine you are managing a network of energy producers who must fulfill a set of contracts for delivering electricity to various regions. Each producer has a limited capacity to generate electricity, and each contract specifies a minimum amount of electricity that must be delivered. Additionally, each contract requires a minimum number of producers to contribute to its fulfillment to ensure reliability and diversity in the energy supply.

#### Key Details:
1. **Producers and Their Capacities**:
   - **Producer 0** can generate up to **2,226** units of electricity.
   - **Producer 1** has a capacity of **2,118** units.
   - **Producer 2** can produce up to **2,644** units.
   - **Producer 3** has a capacity of **2,649** units.
   - **Producer 4** can generate up to **2,548** units.
   - **Producer 5** has a capacity of **2,682** units.

2. **Contracts and Their Requirements**:
   - **Contract 0** requires at least **989** units of electricity and must involve contributions from at least **3** producers.
   - **Contract 1** requires **1,142** units and must involve at least **2** producers.
   - **Contract 2** requires **1,012** units and must involve at least **2** producers.
   - **Contract 3** requires **1,011** units and must involve at least **2** producers.
   - **Contract 4** requires **1,015** units and must involve at least **3** producers.
   - **Contract 5** requires **1,096** units and must involve at least **3** producers.

3. **Producer-Specific Minimum Delivery Requirements**:
   - If a producer contributes to a contract, they must deliver at least a certain minimum amount:
     - **Producer 0** must deliver at least **489** units per contract.
     - **Producer 1** must deliver at least **465** units per contract.
     - **Producer 2** must deliver at least **581** units per contract.
     - **Producer 3** must deliver at least **582** units per contract.
     - **Producer 4** must deliver at least **560** units per contract.
     - **Producer 5** must deliver at least **590** units per contract.

4. **Costs**:
   - The cost of generating electricity varies by producer and contract. For example:
     - **Producer 0** incurs a cost of **46** units per unit of electricity delivered to **Contract 0**, **43** units for **Contract 1**, and so on.
     - Similar cost structures apply to all other producers and contracts, with costs ranging from **40** to **50** units per unit of electricity delivered.

#### Objective:
Your goal is to determine how much electricity each producer should deliver to each contract to **minimize the total generation cost** while ensuring:
- No producer exceeds their capacity.
- Each contract receives the required amount of electricity.
- Each contract involves the required minimum number of producers.
- If a producer contributes to a contract, they deliver at least their specified minimum amount.

#### Constraints:
- **Capacity Constraints**: The total electricity delivered by each producer across all contracts must not exceed their available capacity.
- **Contract Fulfillment**: The total electricity delivered to each contract must meet or exceed the contract's requirement.
- **Minimum Contributors**: Each contract must involve contributions from the specified minimum number of producers.
- **Minimum Delivery**: If a producer contributes to a contract, they must deliver at least their specified minimum amount.

By solving this problem, you will ensure that all contracts are fulfilled at the lowest possible cost while adhering to all operational and reliability constraints.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    producer_capacity = params["producer_capacity"]          # list of 6
    contract_demand = params["contract_demand"]              # list of 6
    min_producers_per_contract = params["min_producers_per_contract"]  # list of 6
    min_delivery_if_active = params["min_delivery_if_active"]  # list of 6
    cost_per_unit = params["cost_per_unit"]                  # 6x6 list of lists

    # Sets
    I = range(len(producer_capacity))   # producers
    J = range(len(contract_demand))     # contracts

    # Model
    model = pyo.ConcreteModel()

    # Variables
    model.x = pyo.Var(I, J, within=pyo.NonNegativeReals)
    model.y = pyo.Var(I, J, within=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(cost_per_unit[i][j] * model.x[i, j] for i in I for j in J),
        sense=pyo.minimize
    )

    # Capacity constraints
    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in J) <= producer_capacity[i]
    model.capacity_con = pyo.Constraint(I, rule=capacity_rule)

    # Contract demand constraints
    def demand_rule(model, j):
        return sum(model.x[i, j] for i in I) >= contract_demand[j]
    model.demand_con = pyo.Constraint(J, rule=demand_rule)

    # Minimum producers per contract
    def min_producers_rule(model, j):
        return sum(model.y[i, j] for i in I) >= min_producers_per_contract[j]
    model.min_producers_con = pyo.Constraint(J, rule=min_producers_rule)

    # Linking constraints: if y[i,j]=0 then x[i,j]=0, if y[i,j]=1 then x[i,j] >= min_delivery_if_active[i]
    def link_lower_rule(model, i, j):
        return model.x[i, j] >= min_delivery_if_active[i] * model.y[i, j]
    model.link_lower_con = pyo.Constraint(I, J, rule=link_lower_rule)

    def link_upper_rule(model, i, j):
        return model.x[i, j] <= producer_capacity[i] * model.y[i, j]
    model.link_upper_con = pyo.Constraint(I, J, rule=link_upper_rule)

    # Solve
    try:
        solver = Highs()
        results = solver.solve(model)
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception as e:
        # If the objective cannot be evaluated, assume infeasible/unbounded
        return {'objective': None, 'status': 'infeasible'}
```

## Clique member B-structured

```python
# {"sets":{"P":"producers=range(len(params['producer_capacity']))","C":"contracts=range(len(params['contract_demand']))"},"params":{"producer_capacity":"capacity[p]","contract_demand":"demand[c]","min_producers_per_contract":"min_prod[c]","min_delivery_if_active":"min_deliv[p]","cost_per_unit":"cost[p][c]"},"vars":{"x[p,c]":"NonNegativeReals delivered amount","y[p,c]":"Binary active contribution"},"constraints":["capacity[p]: sum_c x[p,c] <= producer_capacity[p]","demand[c]: sum_p x[p,c] >= contract_demand[c]","min_contributors[c]: sum_p y[p,c] >= min_producers_per_contract[c]","min_delivery_link[p,c]: x[p,c] >= min_delivery_if_active[p] * y[p,c]","activation_upper_link[p,c]: x[p,c] <= producer_capacity[p] * y[p,c]"],"objective":"minimize sum_{p,c} cost_per_unit[p][c] * x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    min_delivery_if_active = params["min_delivery_if_active"]
    cost_per_unit = params["cost_per_unit"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_producers - 1)
    model.C = pyo.RangeSet(0, num_contracts - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def objective_rule(model):
        return sum(cost_per_unit[p_idx][c_idx] * model.x[p_idx, c_idx] for p_idx in model.P for c_idx in model.C)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def capacity_rule(model, p_idx):
        return sum(model.x[p_idx, c_idx] for c_idx in model.C) <= producer_capacity[p_idx]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(model, c_idx):
        return sum(model.x[p_idx, c_idx] for p_idx in model.P) >= contract_demand[c_idx]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def min_contributors_rule(model, c_idx):
        return sum(model.y[p_idx, c_idx] for p_idx in model.P) >= min_producers_per_contract[c_idx]

    model.min_contributors_con = pyo.Constraint(model.C, rule=min_contributors_rule)

    def min_delivery_link_rule(model, p_idx, c_idx):
        return model.x[p_idx, c_idx] >= min_delivery_if_active[p_idx] * model.y[p_idx, c_idx]

    model.min_delivery_link_con = pyo.Constraint(model.P, model.C, rule=min_delivery_link_rule)

    def activation_upper_link_rule(model, p_idx, c_idx):
        return model.x[p_idx, c_idx] <= producer_capacity[p_idx] * model.y[p_idx, c_idx]

    model.activation_upper_link_con = pyo.Constraint(model.P, model.C, rule=activation_upper_link_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    min_delivery_if_active = params["min_delivery_if_active"]
    cost_per_unit = params["cost_per_unit"]
    
    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)
    
    model = gp.Model("energy_producer_contracts")
    model.Params.OutputFlag = 0
    
    # Decision variables: amount of electricity from producer i to contract j
    x = {}
    for i in range(num_producers):
        for j in range(num_contracts):
            x[i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
    
    # Binary variables: whether producer i contributes to contract j
    y = {}
    for i in range(num_producers):
        for j in range(num_contracts):
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")
    
    model.update()
    
    # Objective: minimize total generation cost
    obj_expr = gp.quicksum(cost_per_unit[i][j] * x[i, j] 
                           for i in range(num_producers) 
                           for j in range(num_contracts))
    model.setObjective(obj_expr, GRB.MINIMIZE)
    
    # Capacity constraints: total delivered by each producer must not exceed capacity
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"capacity_{i}"
        )
    
    # Contract fulfillment: each contract must receive at least its demand
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}"
        )
    
    # Minimum contributors: each contract must involve at least min_producers
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_producers_per_contract[j],
            name=f"min_contributors_{j}"
        )
    
    # Minimum delivery if active: if producer contributes, deliver at least minimum
    # Also link y and x: if y[i,j] = 0, then x[i,j] = 0
    for i in range(num_producers):
        for j in range(num_contracts):
            # If y[i,j] = 1, then x[i,j] >= min_delivery_if_active[i]
            model.addConstr(
                x[i, j] >= min_delivery_if_active[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            # If y[i,j] = 0, then x[i,j] = 0 (enforced by upper bound)
            # Use big-M constraint: x[i,j] <= producer_capacity[i] * y[i,j]
            model.addConstr(
                x[i, j] <= producer_capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
            )
    
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
```
