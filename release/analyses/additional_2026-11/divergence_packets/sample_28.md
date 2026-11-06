# sample_28

Decision: ABSTAIN, clique [], informative [0, 1, 2, 3, 4, 5], label 4.0

## Problem text

Imagine you are organizing a carpooling system for a group of participants attending a large event. The goal is to assign participants to available cars in a way that maximizes the number of successful assignments while respecting their preferences and ensuring that no participant is assigned to more than one car and no car is assigned more than one participant.

Here’s the situation:

- There are **7 participants** (participant_0 to participant_6) and **6 cars** (car_0 to car_5) available for carpooling.
- Each participant has expressed interest in certain cars, but not all cars are preferred by every participant. For example:
  - Participant_0 is only interested in car_2.
  - Participant_1 is only interested in car_0.
  - Participant_2 is interested in car_0 and car_1.
  - Participant_3 is only interested in car_1.
  - Participant_4 is only interested in car_1.
  - Participant_5 has no interest in any car.
  - Participant_6 is only interested in car_3.
- Each car can accommodate only one participant, and each participant can be assigned to at most one car.

Your task is to assign participants to cars in a way that:
1. **Maximizes the total number of successful assignments**, ensuring as many participants as possible are assigned to a car they prefer.
2. **Respects participant preferences**: A participant can only be assigned to a car they have expressed interest in.
3. **Ensures no participant is assigned to more than one car**.
4. **Ensures no car is assigned more than one participant**.

For example:
- If participant_0 is assigned to car_2, no other participant can be assigned to car_2.
- If participant_2 is assigned to car_0, they cannot also be assigned to car_1, and no other participant can be assigned to car_0.

The challenge is to find the optimal assignment that satisfies all these conditions while maximizing the total number of participants successfully assigned to a car. Can you determine the best way to assign participants to cars under these constraints?

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 3.0 (optimal) | 4.0 (optimal) | 3.0 (optimal) | 4.0 (optimal) | 5.0 (optimal) | 5.0 (optimal) |
| B-structured | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) |
| C-direct | 3.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"preference_matrix": [[0, 0, 1, 0, 0, 0], [1, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, -1, 0, 0, 0]]}`
instance 1: `{"preference_matrix": [[0, -1, 0, -1, 0, 0], [1, -1, 0, -1, -1, 0], [-1, -1, 0, 0, -1, 0], [1, -1, 1, 0, 0, -1], [1, 0, -1, -1, 1, 0], [1, 0, 0, 1, 0, 0], [1, 0, 1, 0, 0, -1]]}`
instance 2: `{"preference_matrix": [[-1, 0, -1, -1, -1, 0], [0, 0, 0, -1, 0, 1], [0, 0, -1, 0, -1, 0], [1, 0, 0, 0, 1, 1], [-1, -1, 0, 0, -1, 1], [1, 0, 0, 0, 1, 0], [0, -1, 0, 0, 0, 1]]}`
instance 3: `{"preference_matrix": [[0, -1, 1, 0, -1, -1], [-1, 0, 1, 0, -1, 0], [1, 0, 1, 1, -1, 0], [0, 0, 0, 0, -1, 0], [0, 1, 1, 0, 0, -1], [1, 1, 0, 0, 0, -1], [1, 0, 1, 0, -1, 0]]}`
instance 4: `{"preference_matrix": [[-1, 1, 1, 1, 0, -1], [1, 1, -1, 0, -1, 1], [1, -1, 0, 0, 0, 1], [0, -1, 0, 0, -1, 0], [1, 0, 0, 0, -1, -1], [0, 0, -1, -1, -1, 0], [-1, 1, 1, -1, -1, 0]]}`
instance 5: `{"preference_matrix": [[-1, -1, 1, 0, 0, 1], [1, -1, -1, 0, 0, 0], [0, 0, 1, -1, 0, 0], [1, -1, -1, 0, 0, 0], [-1, 1, 0, 1, 0, -1], [1, 1, 1, 1, 1, -1], [0, -1, 0, -1, 0, 1]]}`

## Extracted specification

```json
{
 "preference_matrix": {
  "base": [
   [
    0,
    0,
    1,
    0,
    0,
    0
   ],
   [
    1,
    0,
    0,
    0,
    0,
    0
   ],
   [
    1,
    1,
    0,
    0,
    0,
    0
   ],
   [
    0,
    1,
    0,
    0,
    0,
    0
   ],
   [
    0,
    1,
    0,
    0,
    0,
    0
   ],
   [
    0,
    0,
    0,
    0,
    0,
    0
   ],
   [
    0,
    0,
    -1,
    0,
    0,
    0
   ]
  ],
  "perturb": {
   "mode": "abs",
   "lo": -1.0,
   "hi": 1.0,
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
    # Extract preference matrix from params
    pref = params["preference_matrix"]
    
    # Determine dimensions
    n_participants = len(pref)
    n_cars = len(pref[0]) if n_participants > 0 else 0
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)
    
    # Variables: x[i,j] = 1 if participant i assigned to car j
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)
    
    # Objective: maximize total assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[i, j] for i in model.P for j in model.C),
        sense=pyo.maximize
    )
    
    # Constraints
    
    # 1. Each participant assigned to at most one car
    def participant_rule(model, i):
        return sum(model.x[i, j] for j in model.C) <= 1
    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)
    
    # 2. Each car assigned to at most one participant
    def car_rule(model, j):
        return sum(model.x[i, j] for i in model.P) <= 1
    model.car_con = pyo.Constraint(model.C, rule=car_rule)
    
    # 3. Respect preferences: only assign if preference_matrix[i][j] == 1
    def preference_rule(model, i, j):
        if pref[i][j] == 1:
            return pyo.Constraint.Skip
        else:
            return model.x[i, j] == 0
    model.pref_con = pyo.Constraint(model.P, model.C, rule=preference_rule)
    
    # Solve
    solver = Highs()
    results = solver.solve(model)
    
    # Check if solution exists and objective is retrievable
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError):
        return {'objective': None, 'status': 'infeasible or no solution found'}
```

## Program B-structured

```python
# IR: {"sets":{"participants":"range(7)","cars":"range(6)"},"params":{"preference_matrix":"binary matrix [7][6]"},"vars":{"assign[i,j]":"Binary participant-car assignment"},"constraints":["assign[i,j] <= preference_matrix[i][j] for all participants i and cars j","sum_j assign[i,j] <= 1 for all participants i","sum_i assign[i,j] <= 1 for all cars j"],"objective":"maximize sum_{i,j} assign[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]

    model = pyo.ConcreteModel()

    participant_list = list(range(7))
    car_list = list(range(6))

    model.participants = pyo.Set(initialize=participant_list)
    model.cars = pyo.Set(initialize=car_list)

    model.assign = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def preference_rule(model, participant, car):
        return model.assign[participant, car] <= preference_matrix[participant][car]
    model.preference_limit = pyo.Constraint(model.participants, model.cars, rule=preference_rule)

    def participant_at_most_one_rule(model, participant):
        return sum(model.assign[participant, car] for car in model.cars) <= 1
    model.participant_at_most_one = pyo.Constraint(model.participants, rule=participant_at_most_one_rule)

    def car_at_most_one_rule(model, car):
        return sum(model.assign[participant, car] for participant in model.participants) <= 1
    model.car_at_most_one = pyo.Constraint(model.cars, rule=car_at_most_one_rule)

    model.obj = pyo.Objective(
        expr=sum(model.assign[participant, car] for participant in model.participants for car in model.cars),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "failed"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    
    # Determine dimensions
    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0]) if num_participants > 0 else 0
    
    # Create model
    model = gp.Model("carpooling")
    model.Params.LogToConsole = 0
    
    # Decision variables: x[i,j] = 1 if participant i is assigned to car j
    x = model.addVars(num_participants, num_cars, vtype=GRB.BINARY, name="x")
    
    # Objective: maximize total number of assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i in range(num_participants) for j in range(num_cars)),
        GRB.MAXIMIZE
    )
    
    # Constraint 1: Each participant assigned to at most one car
    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars)) <= 1,
            name=f"participant_{i}_max_one_car"
        )
    
    # Constraint 2: Each car assigned to at most one participant
    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants)) <= 1,
            name=f"car_{j}_max_one_participant"
        )
    
    # Constraint 3: Respect preferences (participant can only be assigned to preferred cars)
    for i in range(num_participants):
        for j in range(num_cars):
            if preference_matrix[i][j] == 0:
                model.addConstr(x[i, j] == 0, name=f"preference_{i}_{j}")
    
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
            "status": f"status_{model.status}"
        }
```
