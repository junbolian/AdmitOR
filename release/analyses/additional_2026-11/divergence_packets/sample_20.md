# sample_20

Decision: ABSTAIN, clique [], informative [0, 1, 2, 3, 4, 5], label 6.0

## Problem text

Carpool Matching Optimization

You are tasked with organizing a carpool system for a group of participants who need to travel to a common destination. There are **7 participants** and **7 cars** available for the carpool. Each participant has expressed interest in certain cars based on their preferences, and your goal is to assign participants to cars in a way that maximizes the number of successful matches while respecting the following constraints:

1. **Participant Preferences**: Each participant can only be assigned to a car they have expressed interest in. For example:
   - Participant 0 is interested in cars 1, 2, and 3 but not in cars 0, 4, 5, or 6.
   - Participant 1 is interested in cars 0, 1, and 2 but not in cars 3, 4, 5, or 6.
   - Participant 2 is interested in cars 0, 1, 5, and 6 but not in cars 2, 3, or 4.
   - Participant 3 is not interested in any cars.
   - Participant 4 is interested in cars 5 and 6 but not in cars 0, 1, 2, 3, or 4.
   - Participant 5 is interested in cars 0, 1, 5, and 6 but not in cars 2, 3, or 4.
   - Participant 6 is interested in cars 2 and 5 but not in cars 0, 1, 3, 4, or 6.

2. **One Car per Participant**: Each participant can be assigned to at most one car. For example:
   - Participant 0 cannot be assigned to both car 1 and car 2 simultaneously.
   - Participant 1 cannot be assigned to both car 0 and car 1 simultaneously.

3. **One Participant per Car**: Each car can accommodate at most one participant. For example:
   - Car 0 cannot be assigned to both Participant 1 and Participant 2 simultaneously.
   - Car 1 cannot be assigned to both Participant 0 and Participant 1 simultaneously.

4. **Binary Assignments**: The assignment of a participant to a car is a binary decision—either the participant is assigned to the car (1) or not (0).

### Objective:
Your objective is to maximize the total number of successful assignments, ensuring that as many participants as possible are matched to a car they are interested in, while adhering to the constraints above.

### Constraints in Detail:
- **Preference Constraints**: Assignments must respect the participants' preferences. For example:
  - Participant 0 cannot be assigned to car 0, 4, 5, or 6 because they are not interested in these cars.
  - Participant 1 cannot be assigned to car 3, 4, 5, or 6 because they are not interested in these cars.

- **One Car per Participant**: Each participant can only be assigned to one car. For example:
  - If Participant 2 is assigned to car 0, they cannot also be assigned to car 1, 5, or 6.

- **One Participant per Car**: Each car can only be assigned to one participant. For example:
  - If car 0 is assigned to Participant 1, it cannot also be assigned to Participant 2 or any other participant.

### Numerical Parameters:
The specific preferences for each participant are as follows:
- **Participant 0**: Interested in cars 1, 2, 3.
- **Participant 1**: Interested in cars 0, 1, 2.
- **Participant 2**: Interested in cars 0, 1, 5, 6.
- **Participant 3**: Not interested in any cars.
- **Participant 4**: Interested in cars 5, 6.
- **Participant 5**: Interested in cars 0, 1, 5, 6.
- **Participant 6**: Interested in cars 2, 5.

### Summary:
Your task is to assign participants to cars in a way that maximizes the number of successful matches, ensuring that each participant is assigned to at most one car they are interested in, and each car is assigned to at most one participant. The goal is to achieve the highest possible number of assignments while respecting all constraints.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 6.0 (optimal) | 5.0 (optimal) | 5.0 (optimal) | 7.0 (optimal) | 5.0 (optimal) | 5.0 (optimal) |
| B-structured | None (crash:pyomo.common.error) | None (crash:pyomo.common.error) | None (crash:pyomo.common.error) | 7.0 (optimal) | None (crash:pyomo.common.error) | None (crash:pyomo.common.error) |
| C-direct | 6.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) | 7.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"preference_matrix": [[0, 1, 1, 1, 0, 0, 0], [1, 1, 1, 0, 0, 0, 0], [1, 1, 0, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, -1, 1, 1], [1, 1, 0, 0, 0, 1, 1], [0, 0, 1, 0, 0, 1, 0]]}`
instance 1: `{"preference_matrix": [[0, -1, 0, -1, 0, 0, 1], [-1, 0, -1, -1, 0, -1, -1], [0, 0, -1, 0, 1, -1, 1], [0, 0, -1, 1, 0, -1, -1], [1, 0, 1, 0, 0, 1, 0], [0, 1, 0, 1, 0, 0, -1], [-1, 0, -1, -1, -1, 0, 0]]}`
instance 2: `{"preference_matrix": [[0, 0, -1, 0, 1, 0, 0], [-1, 0, -1, 0, 1, 0, 0], [0, 1, 1, -1, -1, 0, 0], [-1, 1, 1, 0, 0, 0, 1], [0, 0, -1, 0, 0, 0, 1], [0, -1, 1, 0, -1, -1, -1], [0, 1, 0, -1, 0, 1, 0]]}`
instance 3: `{"preference_matrix": [[1, 1, -1, 0, 0, 0, 0], [0, -1, 0, 0, 1, 1, 0], [0, -1, 1, 1, 0, 0, 0], [-1, 1, 0, 1, 0, -1, 0], [-1, 1, 1, 1, 0, -1, 1], [1, -1, 0, -1, 1, 1, -1], [0, 0, 0, 1, 0, -1, 0]]}`
instance 4: `{"preference_matrix": [[0, -1, 0, 1, 0, 0, 0], [-1, -1, 0, 0, -1, -1, -1], [0, -1, 1, 1, -1, -1, 0], [-1, -1, 1, 0, 0, 1, 1], [-1, -1, 0, 0, 0, 0, 0], [1, -1, 0, 0, 1, -1, -1], [0, 0, 0, -1, 1, 0, 1]]}`
instance 5: `{"preference_matrix": [[0, -1, 1, 1, 1, 1, 1], [-1, 0, -1, 0, -1, 0, 1], [0, 1, 0, 0, 1, 1, 0], [0, -1, 0, 1, 0, 0, 0], [-1, 0, 0, 1, -1, 1, -1], [-1, 0, 0, -1, -1, 1, -1], [0, 0, 0, 0, 0, 1, -1]]}`

## Extracted specification

```json
{
 "preference_matrix": {
  "base": [
   [
    0,
    1,
    1,
    1,
    0,
    0,
    0
   ],
   [
    1,
    1,
    1,
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
    1,
    1
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
    0,
    0,
    0,
    0,
    -1,
    1,
    1
   ],
   [
    1,
    1,
    0,
    0,
    0,
    1,
    1
   ],
   [
    0,
    0,
    1,
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
    participants = range(7)  # 0..6
    cars = range(7)          # 0..6
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Variables
    model.x = pyo.Var(participants, cars, domain=pyo.Binary)
    
    # Objective: maximize total assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[i, j] for i in participants for j in cars),
        sense=pyo.maximize
    )
    
    # Constraints
    
    # 1. Preference constraints: only assign if participant is interested
    def preference_rule(model, i, j):
        if preference_matrix[i][j] == -1:
            # Participant has no interest in any car (e.g., participant 3)
            return model.x[i, j] == 0
        return model.x[i, j] <= preference_matrix[i][j]
    model.preference_constraints = pyo.Constraint(participants, cars, rule=preference_rule)
    
    # 2. One car per participant
    model.one_car_per_participant = pyo.ConstraintList()
    for i in participants:
        model.one_car_per_participant.add(
            sum(model.x[i, j] for j in cars) <= 1
        )
    
    # 3. One participant per car
    model.one_participant_per_car = pyo.ConstraintList()
    for j in cars:
        model.one_participant_per_car.add(
            sum(model.x[i, j] for i in participants) <= 1
        )
    
    # Solve
    try:
        solver = Highs()
        results = solver.solve(model)
        
        # Check if solution exists and objective is retrievable
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError):
        # Infeasible or no solution found
        return {'objective': None, 'status': 'infeasible'}
```

## Program B-structured

```python
# {"sets":{"I":"participants 0..6","J":"cars 0..6"},"params":{"preference_matrix":"7x7 binary matrix"},"vars":{"x":{"type":"Binary","index":["I","J"]}},"constraints":["x[i,j] == 0 for all i,j with preference_matrix[i][j] = 0","sum_j x[i,j] <= 1 for all i in I","sum_i x[i,j] <= 1 for all j in J"],"objective":"maximize sum_{i in I, j in J} x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 6)

    preference_matrix = params["preference_matrix"]

    allowed_pairs = [
        (i, j)
        for i in range(7)
        for j in range(7)
        if preference_matrix[i][j] == 1
    ]

    model.A = pyo.Set(initialize=allowed_pairs, dimen=2)
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def participant_rule(model, i):
        return sum(model.x[i, j] for j in model.J if (i, j) in model.A) <= 1

    model.participant_con = pyo.Constraint(model.I, rule=participant_rule)

    def car_rule(model, j):
        return sum(model.x[i, j] for i in model.I if (i, j) in model.A) <= 1

    model.car_con = pyo.Constraint(model.J, rule=car_rule)

    model.objective = pyo.Objective(
        expr=sum(model.x[i, j] for (i, j) in model.A),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.objective))
    except Exception:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    preference_matrix = params["preference_matrix"]
    
    # Determine dimensions
    n_participants = len(preference_matrix)
    n_cars = len(preference_matrix[0]) if n_participants > 0 else 0
    
    try:
        # Create model
        model = gp.Model("carpool_matching")
        model.setParam('OutputFlag', 0)
        
        # Decision variables: x[i,j] = 1 if participant i is assigned to car j
        x = model.addVars(n_participants, n_cars, vtype=GRB.BINARY, name="x")
        
        # Objective: maximize total number of successful assignments
        model.setObjective(
            gp.quicksum(x[i, j] for i in range(n_participants) for j in range(n_cars)),
            GRB.MAXIMIZE
        )
        
        # Constraint 1: Participant preferences - can only assign if preference is 1
        for i in range(n_participants):
            for j in range(n_cars):
                if preference_matrix[i][j] == 0:
                    model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")
        
        # Constraint 2: Each participant assigned to at most one car
        for i in range(n_participants):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(n_cars)) <= 1,
                name=f"one_car_per_participant_{i}"
            )
        
        # Constraint 3: Each car assigned to at most one participant
        for j in range(n_cars):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(n_participants)) <= 1,
                name=f"one_participant_per_car_{j}"
            )
        
        # Solve the model
        model.optimize()
        
        # Check solution status
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
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }
```
