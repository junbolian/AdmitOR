# sample_140

Decision: ACCEPT, clique ['A-direct', 'C-direct'], informative [0, 1, 2, 3, 4, 5], label 3.0

## Problem text

There are 6 participants (participant_0 to participant_5) and 6 cars (car_0 to car_5). Each participant can be assigned to at most one car, and each car can be assigned to at most one participant. The goal is to maximize the total number of successful assignments while respecting the participants' preferences. 

Participant 0 can only be assigned to car_5. Participant 1 can only be assigned to car_2 or car_3. Participant 2 can only be assigned to car_4. Participants 3, 4, and 5 have no interest in any cars, so they cannot be assigned to any car. The preferences are binary: a participant is either interested in a car (1) or not (0). The objective is to maximize the sum of all valid assignments, where each valid assignment contributes a value of 1 to the total. The assignments must ensure that no participant is assigned to more than one car, no car is assigned to more than one participant, and all assignments respect the participants' preferences.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 3.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) |
| B-structured | 3.0 (optimal) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) |
| C-direct | 3.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) | -0.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"preference_matrix": [[0, 0, 0, 0, 0, 1], [0, 0, 1, 1, 0, 0], [0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]], "assignment_value": 1}`
instance 1: `{"preference_matrix": [[0, -1, -1, -1, 0, 0], [0, -1, -1, -1, -1, 0], [-1, -1, 0, 0, -1, 0], [0, -1, 0, 0, -1, -1], [0, -1, -1, -1, 0, 0], [0, 0, 0, 0, -1, 0]], "assignment_value": 3.805832649770964}`
instance 2: `{"preference_matrix": [[0, 0, 0, 0, -1, -1], [-1, -1, -1, -1, -1, 0], [-1, -1, -1, -1, 0, 0], [0, -1, 0, -1, -1, 0], [0, 0, 0, 0, 0, -1], [-1, -1, -1, -1, 0, 0]], "assignment_value": 0.20274516558934552}`
instance 3: `{"preference_matrix": [[0, -1, 0, -1, -1, -1], [0, -1, 0, 0, -1, -1], [0, 0, -1, -1, -1, 0], [0, -1, -1, -1, 0, 0], [0, 0, -1, 0, 0, 0], [-1, 0, -1, -1, -1, 0]], "assignment_value": 4.130970582647358}`
instance 4: `{"preference_matrix": [[-1, 0, -1, 0, 0, -1], [0, 0, -1, 0, 0, 0], [0, -1, -1, -1, 0, 0], [0, -1, -1, 0, 0, -1], [-1, -1, 0, 0, -1, -1], [0, -1, 0, -1, -1, 0]], "assignment_value": 3.1095174836298334}`
instance 5: `{"preference_matrix": [[-1, -1, 0, 0, -1, 0], [-1, -1, -1, 0, -1, -1], [-1, 0, -1, 0, 0, -1], [-1, 0, -1, -1, 0, 0], [-1, 0, 0, -1, -1, -1], [-1, -1, 0, 0, 0, -1]], "assignment_value": 0.8183489747158816}`

## Extracted specification

```json
{
 "preference_matrix": {
  "base": [
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
    1,
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
   ]
  ],
  "perturb": {
   "mode": "abs",
   "lo": -1.0,
   "hi": 0.0,
   "integer": true
  }
 },
 "assignment_value": {
  "base": 1,
  "perturb": {
   "mode": "abs",
   "lo": -2.0,
   "hi": 5.0,
   "integer": false
  }
 }
}
```

## Program A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    preference_matrix = params["preference_matrix"]
    assignment_value = params["assignment_value"]
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    participants = range(6)
    cars = range(6)
    
    # Decision variables
    model.x = pyo.Var(participants, cars, within=pyo.Binary)
    
    # Objective
    model.obj = pyo.Objective(
        expr=assignment_value * sum(
            preference_matrix[p][c] * model.x[p, c] 
            for p in participants 
            for c in cars
        ),
        sense=pyo.maximize
    )
    
    # Constraints
    # Each participant assigned to at most one car
    def participant_rule(model, p):
        return sum(preference_matrix[p][c] * model.x[p, c] for c in cars) <= 1
    model.participant_constr = pyo.Constraint(participants, rule=participant_rule)
    
    # Each car assigned to at most one participant
    def car_rule(model, c):
        return sum(preference_matrix[p][c] * model.x[p, c] for p in participants) <= 1
    model.car_constr = pyo.Constraint(cars, rule=car_rule)
    
    # Solve
    try:
        solver = Highs()
        results = solver.solve(model)
        
        # Check if objective value is retrievable
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except (ValueError, TypeError, AttributeError) as e:
        # If objective cannot be evaluated, assume infeasible/failed
        return {'objective': None, 'status': 'infeasible'}
```

## Program B-structured

```python
# IR: {"sets":{"P":["participant_0","participant_1","participant_2","participant_3","participant_4","participant_5"],"C":["car_0","car_1","car_2","car_3","car_4","car_5"]},"params":{"preference_matrix":"binary matrix [P][C]","assignment_value":"value per valid assignment"},"vars":{"assign[p,c]":"Binary, 1 if participant p assigned to car c"},"constraints":["participant_capacity[p]: sum_c assign[p,c] <= 1 for all p","car_capacity[c]: sum_p assign[p,c] <= 1 for all c","preference_respect[p,c]: assign[p,c] <= preference_matrix[p][c] for all p,c"],"objective":"maximize assignment_value * sum_{p,c} assign[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    assignment_value = params["assignment_value"]

    participants = [f"participant_{idx}" for idx in range(6)]
    cars = [f"car_{idx}" for idx in range(6)]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participants, ordered=True)
    model.C = pyo.Set(initialize=cars, ordered=True)

    def pref_init(model_ref, participant, car):
        participant_idx = int(participant.split("_")[1])
        car_idx = int(car.split("_")[1])
        return preference_matrix[participant_idx][car_idx]

    model.preference = pyo.Param(model.P, model.C, initialize=pref_init, within=pyo.Binary)
    model.assignment_value = pyo.Param(initialize=assignment_value)

    model.assign = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def participant_capacity_rule(model_ref, participant):
        return sum(model_ref.assign[participant, car] for car in model_ref.C) <= 1

    model.participant_capacity = pyo.Constraint(model.P, rule=participant_capacity_rule)

    def car_capacity_rule(model_ref, car):
        return sum(model_ref.assign[participant, car] for participant in model_ref.P) <= 1

    model.car_capacity = pyo.Constraint(model.C, rule=car_capacity_rule)

    def preference_respect_rule(model_ref, participant, car):
        return model_ref.assign[participant, car] <= model_ref.preference[participant, car]

    model.preference_respect = pyo.Constraint(model.P, model.C, rule=preference_respect_rule)

    model.objective = pyo.Objective(
        expr=model.assignment_value * sum(model.assign[participant, car] for participant in model.P for car in model.C),
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
    assignment_value = params["assignment_value"]
    
    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])
    
    try:
        model = gp.Model("car_assignment")
        model.Params.OutputFlag = 0
        
        # Decision variables: x[i][j] = 1 if participant i assigned to car j
        x = {}
        for i in range(num_participants):
            for j in range(num_cars):
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
        
        # Objective: maximize total valid assignments
        obj_expr = gp.quicksum(
            assignment_value * x[i, j]
            for i in range(num_participants)
            for j in range(num_cars)
            if preference_matrix[i][j] == 1
        )
        model.setObjective(obj_expr, GRB.MAXIMIZE)
        
        # Constraint: each participant assigned to at most one car
        for i in range(num_participants):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(num_cars)) <= 1,
                name=f"participant_{i}_max_one"
            )
        
        # Constraint: each car assigned to at most one participant
        for j in range(num_cars):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(num_participants)) <= 1,
                name=f"car_{j}_max_one"
            )
        
        # Constraint: respect preferences (can only assign if preference is 1)
        for i in range(num_participants):
            for j in range(num_cars):
                if preference_matrix[i][j] == 0:
                    model.addConstr(x[i, j] == 0, name=f"pref_{i}_{j}")
        
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
                "status": "suboptimal"
            }
    
    except gp.GurobiError as e:
        return {
            "objective": None,
            "status": f"gurobi_error"
        }
```
