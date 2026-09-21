# sample_201

certified: 82958.0
vault label: 66586.0
relative gap: 0.245877511789265
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

You are responsible for managing the assignment of aircraft to routes for an airline company. The goal is to minimize the total operational costs while ensuring that all route demands are met and that the number of aircraft assigned does not exceed the availability of each aircraft type.

#### Aircraft and Route Details:
- There are **6 types of aircraft** (aircraft_0 to aircraft_5) and **7 routes** (route_0 to route_6).
- Each aircraft type has a limited availability:
  - Aircraft_0: Up to 5 can be assigned.
  - Aircraft_1: Up to 4 can be assigned.
  - Aircraft_2: Up to 5 can be assigned.
  - Aircraft_3: Up to 4 can be assigned.
  - Aircraft_4: Up to 5 can be assigned.
  - Aircraft_5: Up to 5 can be assigned.

#### Route Demands:
Each route has a specific demand that must be satisfied by the combined capabilities of the assigned aircraft. The demands are as follows:
- Route_0 requires at least 276 units of capacity.
- Route_1 requires at least 208 units of capacity.
- Route_2 requires at least 286 units of capacity.
- Route_3 requires at least 297 units of capacity.
- Route_4 requires at least 263 units of capacity.
- Route_5 requires at least 263 units of capacity.
- Route_6 requires at least 280 units of capacity.

#### Aircraft Capabilities:
Each aircraft type contributes differently to the capacity of each route. For example:
- Aircraft_0 contributes 95 units to Route_0, 88 units to Route_1, 80 units to Route_2, 80 units to Route_3, 87 units to Route_4, 109 units to Route_5, and 110 units to Route_6.
- Aircraft_1 contributes 105 units to Route_0, 119 units to Route_1, 99 units to Route_2, 112 units to Route_3, 114 units to Route_4, 89 units to Route_5, and 112 units to Route_6.
- Similar contributions are defined for the other aircraft types.

#### Operational Costs:
Assigning an aircraft to a route incurs a specific cost. For example:
- Assigning Aircraft_0 to Route_0 costs 3604 units, to Route_1 costs 3617 units, and so on.
- Assigning Aircraft_1 to Route_0 costs 3308 units, to Route_1 costs 3501 units, and so on.
- Costs for all other aircraft and route combinations are similarly defined.

#### Objective:
Your task is to determine how many aircraft of each type should be assigned to each route to **minimize the total operational cost** while ensuring:
1. The total number of aircraft assigned for each type does not exceed its availability.
2. The combined capacity of all aircraft assigned to each route meets or exceeds the route's demand.
3. The number of aircraft assigned must be a non-negative integer.

By solving this problem, you will ensure that the airline operates efficiently, meeting all route demands at the lowest possible cost.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract data from params dict
    aircraft_availability = params["aircraft_availability"]  # list of 6 integers
    route_demand = params["route_demand"]                    # list of 7 integers
    capacity_matrix = params["capacity_matrix"]              # 6x7 list of lists
    cost_matrix = params["cost_matrix"]                      # 6x7 list of lists
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets - using 0-based indexing to match Python lists
    model.I = pyo.Set(initialize=range(6))      # aircraft types indices 0..5
    model.J = pyo.Set(initialize=range(7))      # routes indices 0..6
    
    # Decision variables: x[i,j] = number of aircraft type i assigned to route j
    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)
    
    # Objective: minimize total cost
    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j] for i in mdl.I for j in mdl.J)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    # Constraint 1: aircraft availability
    def availability_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= aircraft_availability[i]
    model.availability_constr = pyo.Constraint(model.I, rule=availability_rule)
    
    # Constraint 2: route demand satisfaction
    def demand_rule(mdl, j):
        return sum(capacity_matrix[i][j] * mdl.x[i, j] for i in mdl.I) >= route_demand[j]
    model.demand_constr = pyo.Constraint(model.J, rule=demand_rule)
    
    # Solve
    solver = Highs()
    results = solver.solve(model)
    
    # Try to get objective value - if this fails, problem wasn't solved properly
    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except:
        return {"objective": None, "status": "infeasible or failed"}
```

## Clique member B-structured

```python
# {"sets":{"I":"aircraft types 0..5","J":"routes 0..6"},"params":{"aircraft_availability":"A[i]","route_demand":"D[j]","capacity_matrix":"cap[i][j]","cost_matrix":"cost[i][j]"},"vars":{"x":{"type":"NonNegative Integers","index":["I","J"]}},"constraints":["sum_j x[i,j] <= A[i] for all i","sum_i cap[i][j]*x[i,j] >= D[j] for all j"],"objective":"minimize sum_i sum_j cost[i][j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 6)

    avail = params["aircraft_availability"]
    demand = params["route_demand"]
    cap = params["capacity_matrix"]
    cost = params["cost_matrix"]

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def avail_rule(model, i):
        return sum(model.x[i, j] for j in model.J) <= avail[i]

    model.availability = pyo.Constraint(model.I, rule=avail_rule)

    def demand_rule(model, j):
        return sum(cap[i][j] * model.x[i, j] for i in model.I) >= demand[j]

    model.demand = pyo.Constraint(model.J, rule=demand_rule)

    model.objective = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

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
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity_matrix = params["capacity_matrix"]
    cost_matrix = params["cost_matrix"]
    
    num_aircraft = len(aircraft_availability)
    num_routes = len(route_demand)
    
    model = gp.Model("aircraft_assignment")
    model.Params.OutputFlag = 0
    
    # Decision variables: x[i,j] = number of aircraft of type i assigned to route j
    x = model.addVars(num_aircraft, num_routes, vtype=GRB.INTEGER, lb=0, name="x")
    
    # Objective: minimize total operational cost
    obj = gp.quicksum(
        cost_matrix[i][j] * x[i, j]
        for i in range(num_aircraft)
        for j in range(num_routes)
    )
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraint 1: aircraft availability
    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_routes)) <= aircraft_availability[i],
            name=f"availability_{i}"
        )
    
    # Constraint 2: route demand satisfaction
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity_matrix[i][j] * x[i, j] for i in range(num_aircraft)) >= route_demand[j],
            name=f"demand_{j}"
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
