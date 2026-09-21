# sample_287

certified: -56.0
vault label: 19276.0
relative gap: 1.0029051670471052
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

In the context of managing an airline's fleet operations, you are tasked with optimizing the assignment of aircraft to various routes to minimize operational costs while meeting passenger demand and respecting aircraft availability constraints. The airline operates five types of aircraft and serves five distinct routes. Each aircraft type has a limited number of units available, and each route has a specific passenger demand that must be satisfied.

### Scenario Details:
1. **Aircraft Types and Availability**:
   - Aircraft Type 0: 14 units available.
   - Aircraft Type 1: 13 units available.
   - Aircraft Type 2: 15 units available.
   - Aircraft Type 3: 13 units available.
   - Aircraft Type 4: 15 units available.

2. **Routes and Passenger Demand**:
   - Route 0 requires at least 201 passengers to be transported.
   - Route 1 requires at least 210 passengers.
   - Route 2 requires at least 212 passengers.
   - Route 3 requires at least 212 passengers.
   - Route 4 requires at least 210 passengers.

3. **Aircraft Capabilities**:
   Each aircraft type has a specific capacity for each route, measured in the number of passengers it can transport. For example:
   - Aircraft Type 0 can carry 129 passengers on Route 0, 128 on Route 1, 130 on Route 2, 130 on Route 3, and 125 on Route 4.
   - Aircraft Type 1 can carry 130 passengers on Route 0, 129 on Route 1, 126 on Route 2, 130 on Route 3, and 126 on Route 4.
   - Aircraft Type 2 can carry 125 passengers on Route 0, 125 on Route 1, 127 on Route 2, 130 on Route 3, and 127 on Route 4.
   - Aircraft Type 3 can carry 130 passengers on Route 0, 128 on Route 1, 125 on Route 2, 127 on Route 3, and 125 on Route 4.
   - Aircraft Type 4 can carry 125 passengers on Route 0, 129 on Route 1, 127 on Route 2, 127 on Route 3, and 128 on Route 4.

4. **Operational Costs**:
   Assigning an aircraft to a route incurs a specific cost. For example:
   - Assigning Aircraft Type 0 to Route 0 costs 2006 units, to Route 1 costs 2073 units, to Route 2 costs 1975 units, to Route 3 costs 2047 units, and to Route 4 costs 2062 units.
   - Similar costs apply for other aircraft types and routes, with values ranging from 1909 to 2092 units per assignment.

### Objective:
Your goal is to determine how many aircraft of each type should be assigned to each route to minimize the total operational cost while ensuring:
1. The total number of aircraft assigned from each type does not exceed its availability.
2. The total passenger capacity assigned to each route meets or exceeds the demand.

### Constraints:
- **Aircraft Availability**: The total number of aircraft assigned from each type across all routes must not exceed the available units for that type.
- **Passenger Demand**: The combined passenger capacity of all aircraft assigned to a route must meet or exceed the demand for that route.
- **Non-Negativity and Integer Assignments**: The number of aircraft assigned to each route must be a non-negative integer.

### Example Decisions:
- How many Aircraft Type 0 units should be assigned to Route 0, Route 1, etc.?
- How many Aircraft Type 1 units should be assigned to each route?
- And so on for all aircraft types and routes.

By solving this problem, you will ensure the airline operates efficiently, meeting passenger demands while minimizing costs.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract data from params dict
    availability = params["availability"]  # list of length 5
    demand = params["demand"]              # list of length 5
    capacity = params["capacity"]          # 5x5 list of lists
    cost = params["cost"]                  # 5x5 list of lists
    
    # Define sets
    aircraft_types = range(5)
    routes = range(5)
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    model.x = pyo.Var(aircraft_types, routes, domain=pyo.NonNegativeIntegers)
    
    # Objective: minimize total cost
    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in aircraft_types for j in routes),
        sense=pyo.minimize
    )
    
    # Aircraft availability constraints
    def availability_rule(model, i):
        return sum(model.x[i, j] for j in routes) <= availability[i]
    model.availability_con = pyo.Constraint(aircraft_types, rule=availability_rule)
    
    # Passenger demand constraints
    def demand_rule(model, j):
        return sum(capacity[i][j] * model.x[i, j] for i in aircraft_types) >= demand[j]
    model.demand_con = pyo.Constraint(routes, rule=demand_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution exists by trying to retrieve objective value
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible or failed'}
```

## Clique member B-structured

```python
# {"sets":{"I":"aircraft types 0..4","J":"routes 0..4"},"params":{"availability":"params['availability'][i]","demand":"params['demand'][j]","capacity":"params['capacity'][i][j]","cost":"params['cost'][i][j]"},"decision_variables":{"assign[i,j]":"nonnegative integer"},"constraints":["sum_j assign[i,j] <= availability[i] for all i","sum_i capacity[i][j]*assign[i,j] >= demand[j] for all j"],"objective":"minimize sum_i,sum_j cost[i][j]*assign[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    aircraft_types = range(5)
    routes = range(5)

    model.I = pyo.Set(initialize=aircraft_types)
    model.J = pyo.Set(initialize=routes)

    availability_data = params["availability"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    model.assign = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(model, aircraft_type):
        return sum(model.assign[aircraft_type, route] for route in model.J) <= availability_data[aircraft_type]

    model.availability_con = pyo.Constraint(model.I, rule=availability_rule)

    def demand_rule(model, route):
        return sum(capacity_data[aircraft_type][route] * model.assign[aircraft_type, route] for aircraft_type in model.I) >= demand_data[route]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(cost_data[aircraft_type][route] * model.assign[aircraft_type, route]
                 for aircraft_type in model.I for route in model.J),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}
```

## Clique member C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]
    
    num_aircraft_types = len(availability)
    num_routes = len(demand)
    
    model = gp.Model("airline_fleet_assignment")
    model.Params.OutputFlag = 0
    
    # Decision variables: x[i,j] = number of aircraft type i assigned to route j
    x = model.addVars(num_aircraft_types, num_routes, vtype=GRB.INTEGER, lb=0, name="x")
    
    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_aircraft_types) for j in range(num_routes)),
        GRB.MINIMIZE
    )
    
    # Constraint 1: Aircraft availability
    # Sum of aircraft type i assigned to all routes <= availability[i]
    for i in range(num_aircraft_types):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_routes)) <= availability[i],
            name=f"availability_{i}"
        )
    
    # Constraint 2: Passenger demand
    # Sum of capacity provided to route j >= demand[j]
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i, j] for i in range(num_aircraft_types)) >= demand[j],
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
