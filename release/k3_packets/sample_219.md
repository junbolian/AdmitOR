# sample_219

certified: 0.0
vault label: 0.647426219434134
relative gap: 1.0
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

The problem involves assigning 4 spectral peaks (indexed 0 to 3) to 5 amino acids (indexed 0 to 4) to minimize the total assignment cost. Each assignment of peak \(i\) to amino acid \(j\) has a specific cost \(c_{i,j}\), such as assigning Peak 0 to Amino Acid 0 costing 0.5003 units, Peak 0 to Amino Acid 1 costing 0.6370 units, and so on for all combinations. The objective is to minimize the sum of these costs. 

Constraints include ensuring each amino acid is assigned to at most one peak (e.g., Amino Acid 0 can be assigned to only one of Peaks 0, 1, 2, or 3), and each peak is assigned to at most one amino acid (e.g., Peak 0 can be assigned to only one of Amino Acids 0, 1, 2, 3, or 4). Exactly 2 assignments must be made in total across all peaks and amino acids. Additionally, NOE (Nuclear Overhauser Effect) constraints are imposed to ensure spatial consistency. For example, if Peak 1 is assigned to Amino Acid 1, then Peak 3 cannot be assigned to Amino Acid 0 unless the distance between Amino Acid 1 and Amino Acid 0 is below a specified threshold. Similar pairwise constraints apply to other combinations, such as Peak 1 to Amino Acid 2 and Peak 3 to Amino Acid 0, ensuring assignments align with the protein's spatial structure. All decision variables \(x_{i,j}\) are binary, indicating whether peak \(i\) is assigned to amino acid \(j\). The goal is to find the optimal assignments that satisfy all constraints while minimizing the total cost.

## Clique member A-direct

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Extract parameters
    c = params["c"]  # cost matrix: 4 peaks x 5 amino acids
    required_assignments = params["required_assignments"]
    
    # Create model
    model = pyo.ConcreteModel()
    
    # Sets
    model.P = pyo.Set(initialize=range(4))  # peaks
    model.A = pyo.Set(initialize=range(5))  # amino acids
    
    # Variables
    model.x = pyo.Var(model.P, model.A, domain=pyo.Binary)
    
    # Objective
    def obj_rule(m):
        return sum(c[i][j] * m.x[i, j] for i in m.P for j in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    # Constraints
    # Exactly required_assignments total assignments
    def total_assignments_rule(m):
        return sum(m.x[i, j] for i in m.P for j in m.A) == required_assignments
    model.total_assignments = pyo.Constraint(rule=total_assignments_rule)
    
    # Each peak assigned to at most one amino acid
    def peak_rule(m, i):
        return sum(m.x[i, j] for j in m.A) <= 1
    model.peak_constraint = pyo.Constraint(model.P, rule=peak_rule)
    
    # Each amino acid assigned to at most one peak
    def amino_acid_rule(m, j):
        return sum(m.x[i, j] for i in m.P) <= 1
    model.amino_acid_constraint = pyo.Constraint(model.A, rule=amino_acid_rule)
    
    # NOE constraints (spatial consistency)
    # If Peak 1 assigned to Amino Acid 1, then Peak 3 cannot be assigned to Amino Acid 0
    def noe1_rule(m):
        return m.x[1, 1] + m.x[3, 0] <= 1
    model.noe1 = pyo.Constraint(rule=noe1_rule)
    
    # If Peak 1 assigned to Amino Acid 2, then Peak 3 cannot be assigned to Amino Acid 0
    def noe2_rule(m):
        return m.x[1, 2] + m.x[3, 0] <= 1
    model.noe2 = pyo.Constraint(rule=noe2_rule)
    
    # Solve
    solver = Highs()
    result = solver.solve(model)
    
    # Check if solution exists
    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible'}
```

## Clique member B-structured

```python
# {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"c":"2D array-like indexed by (i,j)","required_assignments":"int"},"vars":{"x":{"type":"binary","index":["I","J"]}},"constraints":["sum_j x[i,j] <= 1 for all i","sum_i x[i,j] <= 1 for all j","sum_i sum_j x[i,j] == required_assignments"],"objective":"minimize sum_i sum_j c[i][j] * x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    c = params["c"]
    required_assignments = params["required_assignments"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 4)

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(model):
        return sum(c[i][j] * model.x[i, j] for i in model.I for j in model.J)

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def peak_limit_rule(model, i):
        return sum(model.x[i, j] for j in model.J) <= 1

    model.peak_limit = pyo.Constraint(model.I, rule=peak_limit_rule)

    def aa_limit_rule(model, j):
        return sum(model.x[i, j] for i in model.I) <= 1

    model.aa_limit = pyo.Constraint(model.J, rule=aa_limit_rule)

    model.total_assignments = pyo.Constraint(
        expr=sum(model.x[i, j] for i in model.I for j in model.J) == required_assignments
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
    c = params["c"]
    required_assignments = params["required_assignments"]
    
    # Problem structure
    num_peaks = 4  # peaks indexed 0 to 3
    num_amino_acids = 5  # amino acids indexed 0 to 4
    
    # Create model
    model = gp.Model("peak_assignment")
    model.Params.LogToConsole = 0
    
    # Decision variables: x[i,j] = 1 if peak i is assigned to amino acid j
    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(c[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )
    
    # Constraint: each amino acid is assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
            name=f"amino_acid_{j}_at_most_one"
        )
    
    # Constraint: each peak is assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
            name=f"peak_{i}_at_most_one"
        )
    
    # Constraint: exactly required_assignments assignments must be made
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == required_assignments,
        name="exact_assignments"
    )
    
    # NOE constraints: if peak 1 is assigned to amino acid 1, then peak 3 cannot be assigned to amino acid 0
    # (unless distance constraint is satisfied, but we assume it's not based on problem description)
    model.addConstr(x[1, 1] + x[3, 0] <= 1, name="noe_p1a1_p3a0")
    
    # NOE constraint: if peak 1 is assigned to amino acid 2, then peak 3 cannot be assigned to amino acid 0
    model.addConstr(x[1, 2] + x[3, 0] <= 1, name="noe_p1a2_p3a0")
    
    # Optimize
    model.optimize()
    
    # Extract results
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
            "status": "not_solved"
        }
```
