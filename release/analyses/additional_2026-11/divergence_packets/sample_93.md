# sample_93

Decision: ABSTAIN, clique [], informative [0, 1, 2, 3, 4, 5], label 7.0

## Problem text

Car Assignment for Participants

You are responsible for assigning a group of participants to a set of available cars for a transportation event. The goal is to maximize the number of successful assignments while ensuring that each participant is assigned to at most one car and each car is assigned to at most one participant. Additionally, assignments must respect the preferences of the participants, as each participant is only interested in certain cars.

#### Participants and Cars:
- There are **8 participants** (labeled participant_0 to participant_7) and **7 cars** (labeled car_0 to car_6).
- Each participant has expressed interest in specific cars, as indicated by their preferences. For example:
  - Participant_0 is interested in car_2 and car_4.
  - Participant_1 is interested in car_1, car_2, and car_5.
  - Participant_2 is only interested in car_6.
  - Participant_3 is interested in car_3 and car_4.
  - Participant_4 is not interested in any car.
  - Participant_5 is interested in car_0, car_1, and car_4.
  - Participant_6 is interested in car_0, car_3, and car_6.
  - Participant_7 is interested in car_1, car_4, and car_5.

#### Objective:
Your objective is to maximize the total number of successful assignments, ensuring that as many participants as possible are assigned to a car they are interested in.

#### Constraints:
1. **Participant Preferences**: A participant can only be assigned to a car they are interested in. For example:
   - Participant_0 cannot be assigned to car_0, car_1, car_3, car_5, or car_6 because they are not interested in these cars.
   - Participant_1 cannot be assigned to car_0, car_3, car_4, or car_6.

2. **One Car per Participant**: Each participant can be assigned to at most one car. For example:
   - Participant_0 cannot be assigned to both car_2 and car_4 simultaneously.
   - Participant_1 cannot be assigned to more than one of car_1, car_2, or car_5.

3. **One Participant per Car**: Each car can be assigned to at most one participant. For example:
   - If car_0 is assigned to participant_5, it cannot be assigned to participant_6 or any other participant.
   - If car_1 is assigned to participant_1, it cannot be assigned to participant_5 or participant_7.

#### Numerical Parameters:
- The preferences of participants are binary (0 or 1), where 1 indicates interest and 0 indicates no interest. For example:
  - Participant_0's preferences: car_2 (1), car_4 (1), and all others (0).
  - Participant_1's preferences: car_1 (1), car_2 (1), car_5 (1), and all others (0).
  - Participant_2's preferences: car_6 (1), and all others (0).
  - Participant_3's preferences: car_3 (1), car_4 (1), and all others (0).
  - Participant_4's preferences: all cars (0).
  - Participant_5's preferences: car_0 (1), car_1 (1), car_4 (1), and all others (0).
  - Participant_6's preferences: car_0 (1), car_3 (1), car_6 (1), and all others (0).
  - Participant_7's preferences: car_1 (1), car_4 (1), car_5 (1), and all others (0).

#### Summary:
Your task is to assign participants to cars in a way that maximizes the total number of assignments while respecting participant preferences and ensuring that no participant is assigned to more than one car and no car is assigned to more than one participant. The solution must account for all the constraints and preferences outlined above.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) |
| B-structured | 7.0 (optimal) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) | None (infeasible_or_unbounded) |
| C-direct | 7.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"preference_matrix": [[0, 0, 1, 0, 1, 0, 0], [0, 1, 1, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 1, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 0, 0, 1], [0, 1, 0, 0, 1, 1, 0]]}`
instance 1: `{"preference_matrix": [[0, -1, -1, -1, 0, 0, 0], [-1, -1, -1, -1, 0, -1, -1], [0, 0, -1, 0, 0, -1, 0], [0, -1, -1, 0, -1, -1, -1], [0, 0, 0, 0, 0, 0, -1], [0, 0, 0, 0, 0, 0, -1], [-1, -1, -1, -1, -1, -1, 0], [-1, -1, -1, -1, 0, 0, 0]]}`
instance 2: `{"preference_matrix": [[-1, 0, -1, -1, 0, 0, 0], [0, 0, 0, -1, -1, -1, -1], [-1, 0, 0, -1, 0, -1, 0], [-1, -1, -1, 0, -1, 0, 0], [-1, -1, 0, 0, -1, -1, -1], [0, 0, -1, -1, -1, 0, 0], [0, 0, -1, 0, 0, 0, -1], [0, -1, -1, -1, 0, 0, -1]]}`
instance 3: `{"preference_matrix": [[0, -1, 0, 0, -1, 0, 0], [-1, 0, 0, 0, 0, -1, -1], [-1, 0, 0, 0, -1, -1, 0], [0, -1, -1, -1, 0, 0, -1], [-1, 0, -1, 0, -1, -1, 0], [0, -1, -1, 0, 0, -1, 0], [-1, -1, -1, 0, -1, -1, -1], [0, -1, 0, 0, -1, -1, 0]]}`
instance 4: `{"preference_matrix": [[-1, -1, 0, 0, -1, 0, 0], [-1, -1, -1, -1, -1, 0, 0], [0, -1, -1, -1, 0, -1, -1], [-1, -1, -1, -1, 0, -1, 0], [0, -1, 0, 0, 0, 0, 0], [-1, -1, -1, -1, -1, -1, 0], [-1, 0, -1, -1, 0, 0, 0], [0, -1, -1, 0, 0, 0, 0]]}`
instance 5: `{"preference_matrix": [[-1, 0, 0, 0, -1, 0, -1], [-1, 0, 0, -1, -1, 0, -1], [0, 0, -1, 0, 0, 0, -1], [0, -1, -1, 0, -1, -1, 0], [-1, -1, 0, 0, -1, -1, -1], [0, 0, 0, -1, -1, 0, 0], [0, 0, 0, -1, 0, -1, 0], [0, -1, -1, -1, 0, -1, 0]]}`

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
    1,
    0,
    0
   ],
   [
    0,
    1,
    1,
    0,
    0,
    1,
    0
   ],
   [
    0,
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
    1,
    0,
    0
   ],
   [
    0,
    0,
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
    1,
    0,
    0
   ],
   [
    1,
    0,
    0,
    1,
    0,
    0,
    1
   ],
   [
    0,
    1,
    0,
    0,
    1,
    1,
    0
   ]
  ],
  "perturb": {
   "mode": "abs",
   "lo": -1.0,
   "hi": 0.0,
   "integer": true
  }
 }
}
```

## Program A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract preference matrix from params
    preference_matrix = params["preference_matrix"]
    
    # Define sets
    participants = list(range(8))  # participant_0 to participant_7
    cars = list(range(7))          # car_0 to car_6
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Decision variables: x[i,j] = 1 if participant i assigned to car j
    model.x = pyo.Var(participants, cars, domain=pyo.Binary)
    
    # Objective: maximize total assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[i, j] for i in participants for j in cars),
        sense=pyo.maximize
    )
    
    # Constraint 1: each participant assigned to at most one car
    model.one_car_per_participant = pyo.ConstraintList()
    for i in participants:
        model.one_car_per_participant.add(
            sum(model.x[i, j] for j in cars) <= 1
        )
    
    # Constraint 2: each car assigned to at most one participant
    model.one_participant_per_car = pyo.ConstraintList()
    for j in cars:
        model.one_participant_per_car.add(
            sum(model.x[i, j] for i in participants) <= 1
        )
    
    # Constraint 3: assignments only allowed if participant is interested
    model.preference_constraint = pyo.ConstraintList()
    for i in participants:
        for j in cars:
            if preference_matrix[i][j] == 0:
                model.preference_constraint.add(model.x[i, j] == 0)
    
    # Solve using HiGHS
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        results = solver.solve(model)
        
        # Check if solution exists and objective is retrievable
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
        
    except (ValueError, TypeError, AttributeError) as e:
        # If objective cannot be evaluated, problem likely infeasible
        return {'objective': None, 'status': 'infeasible'}
```

## Program B-structured

```python
# {"sets":{"participants":"range(8)","cars":"range(7)"},"params":{"preference_matrix":"binary matrix [8][7] from params"},"vars":{"assign[i,j]":"Binary for participant-car assignment"},"constraints":["assign[i,j] <= preference_matrix[i][j] for all i,j","sum_j assign[i,j] <= 1 for all i","sum_i assign[i,j] <= 1 for all j"],"objective":"maximize sum_{i,j} assign[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 6)

    model.assign = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def preference_rule(model, participant_idx, car_idx):
        return model.assign[participant_idx, car_idx] <= preference_matrix[participant_idx][car_idx]
    model.preference_limit = pyo.Constraint(model.participants, model.cars, rule=preference_rule)

    def participant_capacity_rule(model, participant_idx):
        return sum(model.assign[participant_idx, car_idx] for car_idx in model.cars) <= 1
    model.participant_capacity = pyo.Constraint(model.participants, rule=participant_capacity_rule)

    def car_capacity_rule(model, car_idx):
        return sum(model.assign[participant_idx, car_idx] for participant_idx in model.participants) <= 1
    model.car_capacity = pyo.Constraint(model.cars, rule=car_capacity_rule)

    model.total_assignments = pyo.Objective(
        expr=sum(model.assign[participant_idx, car_idx] for participant_idx in model.participants for car_idx in model.cars),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except Exception:
        return {"objective": None, "status": "solve failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    
    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])
    
    model = gp.Model("car_assignment")
    model.Params.OutputFlag = 0
    
    # Decision variables: x[i][j] = 1 if participant i is assigned to car j
    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preference_matrix[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # Objective: maximize the number of assignments
    model.setObjective(
        gp.quicksum(x[i, j] for i, j in x.keys()),
        GRB.MAXIMIZE
    )
    
    # Constraint 1: Each participant assigned to at most one car
    for i in range(num_participants):
        participant_vars = [x[i, j] for j in range(num_cars) if (i, j) in x]
        if participant_vars:
            model.addConstr(gp.quicksum(participant_vars) <= 1, name=f"participant_{i}")
    
    # Constraint 2: Each car assigned to at most one participant
    for j in range(num_cars):
        car_vars = [x[i, j] for i in range(num_participants) if (i, j) in x]
        if car_vars:
            model.addConstr(gp.quicksum(car_vars) <= 1, name=f"car_{j}")
    
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
