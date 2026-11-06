# sample_165

Decision: ABSTAIN, clique [], informative [0, 1, 2, 3, 4, 5], label 4.0

## Problem text

Imagine you are organizing a carpooling event for a group of participants and a fleet of cars. Your goal is to maximize the number of successful assignments of participants to cars while respecting their preferences and ensuring that no participant is assigned to more than one car and no car is assigned to more than one participant.

Here’s the situation:

- There are **6 participants** (participant_0 to participant_5) and **6 cars** (car_0 to car_5).
- Each participant has specific preferences for which cars they are willing to ride in. These preferences are represented as binary values (0 or 1), where 1 indicates interest and 0 indicates no interest.
  - For example:
    - Participant_0 is only interested in car_1.
    - Participant_1 is only interested in car_5.
    - Participant_2 is only interested in car_3.
    - Participant_4 is interested in car_1, car_4, and car_5.
    - Participant_5 is only interested in car_4.
    - Participant_3 has no interest in any car.

Your task is to assign participants to cars in such a way that:
1. Each participant is assigned to at most one car.
2. Each car is assigned to at most one participant.
3. A participant can only be assigned to a car they are interested in.

The objective is to maximize the total number of successful assignments, ensuring that as many participants as possible are paired with a car they prefer.

### Key Constraints:
1. **Participant Preferences**:
   - Participant_0 can only be assigned to car_1.
   - Participant_1 can only be assigned to car_5.
   - Participant_2 can only be assigned to car_3.
   - Participant_4 can be assigned to car_1, car_4, or car_5.
   - Participant_5 can only be assigned to car_4.
   - Participant_3 cannot be assigned to any car.

2. **One Car Per Participant**:
   - No participant can be assigned to more than one car.

3. **One Participant Per Car**:
   - No car can be assigned to more than one participant.

### Objective:
Maximize the total number of participants successfully assigned to a car they are interested in, while adhering to the constraints above.

This problem requires careful consideration of participant preferences and the limited availability of cars to ensure an optimal and fair assignment.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 4.0 (optimal) | 4.0 (optimal) | 3.0 (optimal) | 4.0 (optimal) | 5.0 (optimal) | 3.0 (optimal) |
| B-structured | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) |
| C-direct | 4.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) | 6.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"preference_matrix": [[0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1], [0, 0, 0, 1, 0, -1], [0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 1, 1], [0, 0, 0, 0, 1, 0]]}`
instance 1: `{"preference_matrix": [[0, -1, 0, -1, 0, 0], [1, -1, 0, -1, -1, 0], [-1, -1, 0, 0, -1, 0], [1, -1, 1, 0, 0, -1], [1, 0, -1, -1, 1, 0], [1, 0, 0, 1, 0, 0]]}`
instance 2: `{"preference_matrix": [[1, 0, 1, 0, 0, -1], [-1, 0, -1, -1, -1, 0], [0, 0, 0, -1, 0, 1], [0, 0, -1, 0, -1, 0], [1, 0, 0, 0, 1, 1], [-1, -1, 0, 0, -1, 1]]}`
instance 3: `{"preference_matrix": [[1, 0, 0, 0, 1, 0], [0, -1, 0, 0, 0, 1], [0, -1, 1, 0, -1, -1], [-1, 0, 1, 0, -1, 0], [1, 0, 1, 1, -1, 0], [0, 0, 0, 0, -1, 0]]}`
instance 4: `{"preference_matrix": [[0, 1, 1, 0, 0, -1], [1, 1, 0, 0, 0, -1], [1, 0, 1, 0, -1, 0], [-1, 1, 1, 1, 0, -1], [1, 1, -1, 0, -1, 1], [1, -1, 0, 0, 0, 1]]}`
instance 5: `{"preference_matrix": [[0, -1, 0, 0, -1, 0], [1, 0, 0, 0, -1, -1], [0, 0, -1, -1, -1, 0], [-1, 1, 1, -1, -1, 0], [-1, -1, 1, 0, 0, 1], [1, -1, -1, 0, 0, 0]]}`

## Extracted specification

```json
{
 "preference_matrix": {
  "base": [
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
    1
   ],
   [
    0,
    0,
    0,
    1,
    0,
    -1
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
    1,
    0,
    0,
    1,
    1
   ],
   [
    0,
    0,
    0,
    0,
    1,
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
    preference_matrix = params["preference_matrix"]
    
    # Define sets
    participants = list(range(6))
    cars = list(range(6))
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Variables: x[i,j] = 1 if participant i assigned to car j
    model.x = pyo.Var(participants, cars, domain=pyo.Binary)
    
    # Objective: maximize number of assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[i,j] for i in participants for j in cars),
        sense=pyo.maximize
    )
    
    # Constraints: each participant at most one car
    def participant_rule(model, i):
        return sum(model.x[i,j] for j in cars) <= 1
    model.participant_con = pyo.Constraint(participants, rule=participant_rule)
    
    # Constraints: each car at most one participant
    def car_rule(model, j):
        return sum(model.x[i,j] for i in participants) <= 1
    model.car_con = pyo.Constraint(cars, rule=car_rule)
    
    # Constraints: only allowed preferences
    def preference_rule(model, i, j):
        if preference_matrix[i][j] == -1:
            return model.x[i,j] == 0
        return model.x[i,j] <= preference_matrix[i][j]
    model.preference_con = pyo.Constraint(participants, cars, rule=preference_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution was found by trying to access objective value
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible or failed'}
```

## Program B-structured

```python
# IR: {"sets":{"participants":"range(6)","cars":"range(6)"},"params":{"preference_matrix":"binary matrix [6][6] from params"},"decision_variables":{"assign[i,j]":"Binary assignment of participant i to car j"},"constraints":["participant_at_most_one: for each i, sum_j assign[i,j] <= 1","car_at_most_one: for each j, sum_i assign[i,j] <= 1","preference_only: for each i,j, assign[i,j] <= preference_matrix[i][j]"],"objective":"maximize sum_{i,j} assign[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=range(6))
    model.cars = pyo.Set(initialize=range(6))

    model.assign = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def participant_at_most_one_rule(model, participant):
        return sum(model.assign[participant, car] for car in model.cars) <= 1

    model.participant_at_most_one = pyo.Constraint(
        model.participants, rule=participant_at_most_one_rule
    )

    def car_at_most_one_rule(model, car):
        return sum(model.assign[participant, car] for participant in model.participants) <= 1

    model.car_at_most_one = pyo.Constraint(model.cars, rule=car_at_most_one_rule)

    def preference_only_rule(model, participant, car):
        return model.assign[participant, car] <= preference_matrix[participant][car]

    model.preference_only = pyo.Constraint(
        model.participants, model.cars, rule=preference_only_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assign[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_assignments))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_unbounded"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read parameters
    preference_matrix = params["preference_matrix"]
    
    # Determine dimensions
    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0]) if num_participants > 0 else 0
    
    # Create model
    model = gp.Model("carpooling")
    model.setParam('OutputFlag', 0)
    
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
    
    # Constraint 3: Participant can only be assigned to cars they prefer
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
            "status": "error"
        }
```
