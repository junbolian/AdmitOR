# Label-matching panel_base_3of3 certificates withdrawn by the rule B or C

Every panel_base_3of3 certificate whose value matches the label and that the rule "B or C" withdraws (family B or C raises flag_any). IndustryOR and Mamo ComplexLP, scored with `round_aware` of scripts/score_eval.py against the original labels. Sections: identification with the expert status of Xiao et al. (2025), problem text, extracted parameter set with warnings, the three programs, values on the stated and resampled instances (both samplers), and the data-verification replies of the three families.

| Sample id | Benchmark | Certified value | Label | Expert status | B or C flags |
|---|---|---:|---:|---|---|
| `industryor_24` | IndustryOR | 150.0 | 150 | kept, same label; expert label 150 | yes |
| `industryor_44` | IndustryOR | 153.0 | 153 | removed | yes |
| `mamo_complex_29` | Mamo ComplexLP | 1324.0 | 1324 | removed | yes |
| `mamo_complex_32` | Mamo ComplexLP | 47.0 | 47 | kept, same label; expert label 47.0 | yes |
| `mamo_complex_63` | Mamo ComplexLP | 6218.0 | 6218 | removed | yes |
| `mamo_complex_132` | Mamo ComplexLP | 1494.0 | 1494 | removed | yes |
| `mamo_complex_133` | Mamo ComplexLP | 1490.0 | 1490 | removed | yes |
| `mamo_complex_138` | Mamo ComplexLP | 257.0 | 257 | kept, same label; expert label 257.0 | yes |
| `mamo_complex_155` | Mamo ComplexLP | 96.0 | 96 | kept, same label; expert label 96.0 | yes |
| `mamo_complex_164` | Mamo ComplexLP | 60.0 | 60 | kept, same label; expert label 60.0 | yes |
| `mamo_complex_168` | Mamo ComplexLP | 63.0 | 63 | kept, same label; expert label 63.0 | yes |
| `mamo_complex_170` | Mamo ComplexLP | 54.0 | 54 | kept, same label; expert label 54.0 | yes |
| `mamo_complex_172` | Mamo ComplexLP | 60.0 | 60 | kept, same label; expert label 60.0 | yes |
| `mamo_complex_175` | Mamo ComplexLP | 62.0 | 62 | kept, same label; expert label 62.0 | yes |
| `mamo_complex_177` | Mamo ComplexLP | 44.0 | 44 | kept, same label; expert label 44.0 | yes |
| `mamo_complex_203` | Mamo ComplexLP | 12170.0 | 12170 | kept, same label; expert label 12170 | yes |
| `mamo_complex_204` | Mamo ComplexLP | 1.0 | 1 | removed | yes |

## 1. industryor_24 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_24` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 24) |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 150.0 |
| Label (original benchmark) | 150 |
| Rules that certify it | gate 150.0, panel_base_2of3 150.0, panel_base_3of3 150.0, ind_gate 150.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 150 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
The number of drivers and crew members required for each time period of a certain day and night service bus route is shown in Table 1-17.
Table 1-17
\begin{tabular}{c|c|c}
\hline Shift & Time & Number Required \\
\hline 1 & $6: 00 \sim 10: 00$ & 60 \\
\hline 2 & $10: 00 \sim 14: 00$ & 70 \\
\hline 3 & $14: 00 \sim 18: 00$ & 60 \\
\hline 4 & $22: 00 \sim 22: 00$ & 50 \\
\hline 5 & $22: 00 \sim 2: 00$ & 20 \\
\hline 6 & $2: 00 \sim 6: 00$ & 30 \\
\hline
\end{tabular}

Assuming the drivers and crew members start working at the beginning of each time period and work continuously for eight hours, how many drivers and crew members should be equipped for this bus route at least? Provide the linear programming model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"requirements": {"base":[60,70,60,50,20,30],"perturb":{"mode":"rel","r":0.5}}
"shift_length": {"base":8,"perturb":{"mode":"abs","lo":8.0,"hi":8.0,"integer":true}}
"period_length": {"base":4,"perturb":{"mode":"abs","lo":4.0,"hi":4.0,"integer":true}}
```

Warnings:

```
[shift_length] degenerate abs range (lo == hi); perturbation has no effect
[period_length] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]
    shift_length = params["shift_length"]
    period_length = params["period_length"]

    n_shifts = len(requirements)
    covers = int(round(shift_length / period_length))

    model = pyo.ConcreteModel()
    model.shifts = pyo.RangeSet(0, n_shifts - 1)

    # x[i] = number of crew starting at beginning of shift i
    model.x = pyo.Var(model.shifts, domain=pyo.NonNegativeReals)

    # Each 4-hour period's requirement must be covered by all starts whose
    # 8-hour window (covering `covers` consecutive periods) overlaps it.
    def cover_rule(model, p):
        total = 0
        for i in range(n_shifts):
            covers_period = any((i + k) % n_shifts == p for k in range(covers))
            if covers_period:
                total = total + model.x[i]
        return total >= requirements[p]

    model.cover = pyo.Constraint(model.shifts, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(model.x[i] for i in model.shifts), sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_failed"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"requirements":"six-element sequence indexed by T","shift_length":"positive working hours","period_length":"positive hours per period","K":"shift_length / period_length; must be an integer in [1,6]"},"variables":{"crew_start[t]":"nonnegative integer for t in T"},"constraints":["coverage[t]: sum(crew_start[(t-offset) mod 6] for offset in range(K)) >= requirements[t], for each t in T"],"objective":"minimize sum(crew_start[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]
    shift_length = params["shift_length"]
    period_length = params["period_length"]

    periods = tuple(range(6))
    period_count = len(periods)

    if len(requirements) != period_count:
        return {"objective": None, "status": "invalid_requirements"}

    if shift_length <= 0 or period_length <= 0:
        return {"objective": None, "status": "invalid_lengths"}

    coverage_ratio = shift_length / period_length
    if not 1 <= coverage_ratio <= period_count:
        return {"objective": None, "status": "invalid_shift_length"}

    coverage_count = int(coverage_ratio)
    if coverage_count != coverage_ratio:
        return {"objective": None, "status": "nonintegral_shift_length"}

    model = pyo.ConcreteModel()
    model.periods = pyo.Set(initialize=periods, ordered=True)

    model.required_crew = pyo.Param(
        model.periods,
        initialize={
            period: requirements[period]
            for period in periods
        },
        within=pyo.NonNegativeReals,
    )

    model.crew_start = pyo.Var(
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, period):
        return (
            sum(
                instance.crew_start[(period - offset) % period_count]
                for offset in range(coverage_count)
            )
            >= instance.required_crew[period]
        )

    model.coverage = pyo.Constraint(
        model.periods,
        rule=coverage_rule,
    )

    model.total_crew = pyo.Objective(
        expr=sum(model.crew_start[period] for period in model.periods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_crew))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    requirements = params["requirements"]  # list of 6 values
    shift_length = params["shift_length"]  # 8 hours
    period_length = params["period_length"]  # 4 hours

    # Number of consecutive periods each crew member covers
    periods_covered = int(shift_length / period_length)  # = 2

    # 6 shifts, indexed 0..5
    num_shifts = 6

    # x[i] = number of crew members starting at shift i (0-indexed)
    # A crew member starting at shift i covers shifts i and i+1 (mod 6)

    model = gp.Model("bus_crew")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_shifts, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total crew
    model.setObjective(gp.quicksum(x[i] for i in range(num_shifts)), GRB.MINIMIZE)

    # Coverage constraints: for each shift s, sum of x[i] where i covers s >= requirements[s]
    # Crew starting at shift i covers shift i and shift (i+1) mod num_shifts
    for s in range(num_shifts):
        # Shifts that cover period s: shift s itself, and shift (s-1) mod num_shifts
        covering = [(s - k) % num_shifts for k in range(periods_covered)]
        model.addConstr(
            gp.quicksum(x[i] for i in covering) >= requirements[s],
            name=f"cover_{s}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 150.0 (optimal) | 150.0 (optimal) | 150.0 (optimal) |
| 1 | 139.59679129290043 (optimal) | 141.0 (optimal) | 141.0 (optimal) |
| 2 | 108.9643070630097 (optimal) | 111.0 (optimal) | 111.0 (optimal) |
| 3 | 147.90864975976757 (optimal) | 150.0 (optimal) | 150.0 (optimal) |
| 4 | 149.94742226216493 (optimal) | 151.0 (optimal) | 151.0 (optimal) |
| 5 | 189.27572761314465 (optimal) | 191.0 (optimal) | 191.0 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 150.0 (optimal) | 150.0 (optimal) | 150.0 (optimal) |
| 1 | 139.59679129290043 (optimal) | 141.0 (optimal) | 141.0 (optimal) |
| 2 | 108.9643070630097 (optimal) | 111.0 (optimal) | 111.0 (optimal) |
| 3 | 147.90864975976757 (optimal) | 150.0 (optimal) | 150.0 (optimal) |
| 4 | 149.94742226216493 (optimal) | 151.0 (optimal) | 151.0 (optimal) |
| 5 | 189.27572761314465 (optimal) | 191.0 (optimal) | 191.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "requirements", "evidence": "Table 1-17 lists shift requirements (60, 70, 60, 50, 20, 30) but the shift times are inconsistent/ambiguous (e.g., shift 4 '22:00~22:00', shift times total 24h but entries overlap), so the 4-hour period mapping is not explicitly stated"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch":[{"parameter":"period_length","extracted":4,"stated":0,"evidence":"Shift 4: $22: 00 \\sim 22: 00$"}],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{"mismatch": [], "not_stated": []}
```
````


## 2. industryor_44 (IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `industryor_44` |
| Benchmark | IndustryOR (`datasets/benchmark/industryor.jsonl`, field `index` = 44) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 153.0 |
| Label (original benchmark) | 153 |
| Rules that certify it | gate 153.0, gate_3fam 153.0, gate_tau 153.0, panel_base_2of3 153.0, panel_base_3of3 153.0, ind_gate 153.0, ind_gate_tau 153.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
A traveling salesman must visit 7 customers at 7 different locations, and the (symmetric) distance matrix is as follows:

|  | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | - | 86 | 49 | 57 | 31 | 69 | 50 |
| 2 |  | - | 68 | 79 | 93 | 24 | 5 |
| 3 |  |  | - | 16 | 7 | 72 | 67 |
| 4 |  |  |  | - | 90 | 69 | 1 |
| 5 |  |  |  |  | - | 86 | 59 |
| 6 |  |  |  |  |  | - | 81 |

Develop a mathematical program to determine the visiting order starting from location 1 and ending at location 1, in order to minimize the traveling distance, and solve it using COPTPY.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"num_customers": {"base":7,"perturb":{"mode":"abs","lo":7.0,"hi":7.0,"integer":true}}
"distance_matrix": {"base":[[0,86,49,57,31,69,50],[86,0,68,79,93,24,5],[49,68,0,16,7,72,67],[57,79,16,0,90,69,1],[31,93,7,90,0,86,59],[69,24,72,69,86,0,81],[50,5,67,1,59,81,0]],"perturb":{"mode":"rel","r":0.35}}
```

Warnings:

```
[num_customers] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_customers"])
    dist = params["distance_matrix"]

    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.nodes, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(mdl):
        return sum(dist[i][j] * mdl.x[i, j] for (i, j) in mdl.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing and one incoming arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.out_con = pyo.Constraint(model.nodes, rule=out_rule)
    model.in_con = pyo.Constraint(model.nodes, rule=in_rule)

    # Fix depot (node 0 == location 1) as start
    model.u[0].fix(0)

    # Subtour elimination (MTZ)
    def mtz_rule(mdl, i, j):
        if i != 0 and j != 0 and i != j:
            return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"1..n","A":"{(i,j) in V x V: i != j}","U":"V excluding depot 1"},"params":{"n":"params['num_customers']","d":"params['distance_matrix'], a square zero-based matrix"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,n-1] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For distinct i,j in U: u[i] - u[j] + n*x[i,j] <= n-1"],"objective":"Minimize sum(d[i-1][j-1]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the symmetric TSP, with location 1 as the depot."""
    n = params["num_customers"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.locations = pyo.RangeSet(1, n)
    model.non_depot_locations = pyo.Set(
        initialize=[i for i in range(1, n + 1) if i != 1],
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, n + 1)
            for j in range(1, n + 1)
            if i != j
        ],
    )

    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distance_matrix[i - 1][j - 1]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.non_depot_locations,
        domain=pyo.Reals,
        bounds=(1, n - 1),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in instance.locations
            if j != i
        ) == 1

    model.outgoing_degree = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j]
            for i in instance.locations
            if i != j
        ) == 1

    model.incoming_degree = pyo.Constraint(
        model.locations, rule=incoming_rule
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i] - instance.u[j] + n * instance.x[i, j]
            <= n - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.non_depot_locations,
        model.non_depot_locations,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    n = params["num_customers"]
    d = params["distance_matrix"]  # d[i][j] or d[(i,j)], we'll handle both

    # Normalize distance matrix to a dict keyed by (i,j) with 0-based or 1-based indices
    # We'll use 0-based internally: nodes 0..n-1
    # d may be a list of lists or a dict; handle both
    def dist(i, j):
        if isinstance(d, dict):
            if (i, j) in d:
                return d[(i, j)]
            elif (j, i) in d:
                return d[(j, i)]
            else:
                return 0.0
        else:
            # list of lists
            return d[i][j]

    nodes = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if edge (i,j) is used, for i != j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist(i, j) * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each node must be entered exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each node must be left exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if i != j) == 1,
            name=f"leave_{i}"
        )

    # Subtour elimination via callback (lazy constraints)
    # We use the standard MTZ or subtour callback approach.
    # Using a callback with lazy constraints for subtour elimination.

    model.setParam("LazyConstraints", 1)

    def subtour_elim(model, where):
        if where == GRB.Callback.MIPSOL:
            x_val = model.cbGetSolution(
                [x[i, j] for i in nodes for j in nodes if i != j]
            )
            x_sol = {}
            idx = 0
            for i in nodes:
                for j in nodes:
                    if i != j:
                        x_sol[i, j] = x_val[idx]
                        idx += 1

            # Find subtours
            unvisited = set(nodes)
            cycles = []
            while unvisited:
                cycle = []
                current = next(iter(unvisited))
                while True:
                    cycle.append(current)
                    unvisited.discard(current)
                    # Find next node
                    next_node = None
                    for j in nodes:
                        if j != current and x_sol.get((current, j), 0) > 0.5:
                            next_node = j
                            break
                    if next_node is None or next_node in cycle:
                        break
                    current = next_node
                cycles.append(cycle)

            # Add subtour elimination constraints for cycles that don't include all nodes
            for cycle in cycles:
                if len(cycle) < n:
                    model.cbLazy(
                        gp.quicksum(x[i, j] for i in cycle for j in cycle if i != j)
                        <= len(cycle) - 1
                    )

    model.optimize(subtour_elim)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 153.0 (optimal) | 153.0 (optimal) | 153.0 (optimal) |
| 1 | 171.0489215372998 (optimal) | 171.0489215372998 (optimal) | 171.0489215372998 (optimal) |
| 2 | 133.92796538910812 (optimal) | 133.92796538910812 (optimal) | 133.92796538910812 (optimal) |
| 3 | 128.90357505321936 (optimal) | 128.90357505321936 (optimal) | 128.90357505321936 (optimal) |
| 4 | 143.1776404113208 (optimal) | 143.1776404113208 (optimal) | 143.1776404113208 (optimal) |
| 5 | 149.41737748537017 (optimal) | 149.41737748537017 (optimal) | 149.41737748537014 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 153.0 (optimal) | 153.0 (optimal) | 153.0 (optimal) |
| 1 | 171.0489215372998 (optimal) | 171.0489215372998 (optimal) | 171.0489215372998 (optimal) |
| 2 | 133.92796538910812 (optimal) | 133.92796538910812 (optimal) | 133.92796538910812 (optimal) |
| 3 | 128.90357505321936 (optimal) | 128.90357505321936 (optimal) | 128.90357505321936 (optimal) |
| 4 | 143.1776404113208 (optimal) | 143.1776404113208 (optimal) | 143.1776404113208 (optimal) |
| 5 | 149.41737748537017 (optimal) | 149.41737748537017 (optimal) | 149.41737748537014 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"distance_matrix","evidence":"Diagonal entries are shown as \"-\"; no diagonal value of 0 is stated."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 3. mamo_complex_29 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_29` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 29) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 1324.0 |
| Label (original benchmark) | 1324 |
| Rules that certify it | gate 1324.0, gate_3fam 1324.0, gate_tau 1324.0, panel_base_2of3 1324.0, panel_base_3of3 1324.0, ind_gate 1324.0, ind_gate_tau 1324.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine you're overseeing the distribution of medical supplies across five different regions to ensure everyone has access to the resources they need. Each region currently has a certain quantity of supplies, but the demand varies from region to region.

Here's the breakdown of the current supplies and the required quantities for each region:

- Region 1 currently has 133 units but needs 146 units.
- Region 2 currently has 189 units but needs 270 units.
- Region 3 currently has 446 units but needs 313 units.
- Region 4 currently has 346 units but needs 102 units.
- Region 5 currently has 184 units but needs 412 units.

You have the ability to redistribute supplies from one region to another, but there are transportation costs associated with this.

Here's a cost matrix showing how much it costs to transport supplies between each pair of regions:

- Transporting supplies from/to Region 1: To Region 2 costs 24, to Region 3 costs 32, to Region 4 costs 44, to Region 5 costs 46.
- Transporting supplies from/to Region 2: To Region 1 costs 41, to Region 3 costs 6, to Region 4 costs 11, to Region 5 costs 49.
- Transporting supplies from/to Region 3: To Region 1 costs 40, to Region 2 costs 10, to Region 4 costs 40, to Region 5 costs 45.
- Transporting supplies from/to Region 4: To Region 1 costs 22, to Region 2 costs 22, to Region 3 costs 34, to Region 5 costs 1.
- Transporting supplies from/to Region 5: To Region 1 costs 46, to Region 2 costs 14, to Region 3 costs 35, to Region 4 costs 36.

Your objective is to ensure that every region receives the necessary supplies while minimizing transportation costs. What would be the minimum cost to meet the demand for medical supplies in all regions?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supply": {"base":[133,189,446,346,184],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[146,270,313,102,412],"perturb":{"mode":"rel","r":0.3}}
"transport_cost": {"base":[[0,24,32,44,46],[41,0,6,11,49],[40,10,0,40,45],[22,22,34,0,1],[46,14,35,36,0]],"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = 5
    regions = range(n)

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=list(regions))
    model.J = pyo.Set(initialize=list(regions))

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) >= demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"R":[0,1,2,3,4]},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","transport_cost":"transport_cost[i,j] from params['transport_cost']"},"variables":{"shipment[i,j]":"nonnegative real; initial supply from i allocated to demand at j, including local use when i=j"},"constraints":["For each i: sum_j shipment[i,j] <= supply[i].","For each j: sum_i shipment[i,j] = demand[j]."],"objective":"Minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize transportation cost; unused initial supply is permitted."""
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 4)

    model.supply_units = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: supply[region],
        within=pyo.NonNegativeReals,
    )
    model.demand_units = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: demand[region],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.regions,
        model.regions,
        initialize=lambda mdl, origin, destination: (
            transport_cost[origin][destination]
        ),
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.regions,
        model.regions,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, origin):
        return (
            sum(
                mdl.shipment[origin, destination]
                for destination in mdl.regions
            )
            <= mdl.supply_units[origin]
        )

    model.supply_limits = pyo.Constraint(
        model.regions,
        rule=supply_rule,
    )

    def demand_rule(mdl, destination):
        return (
            sum(
                mdl.shipment[origin, destination]
                for origin in mdl.regions
            )
            == mdl.demand_units[destination]
        )

    model.demand_requirements = pyo.Constraint(
        model.regions,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.regions
            for destination in model.regions
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = range(n)

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units shipped from region i to region j
    x = [[model.addVar(lb=0, name=f"x_{i}_{j}") for j in regions] for i in regions]

    # Self-shipping forced to 0
    for i in regions:
        x[i][i].ub = 0

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i][j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraint: units shipped out of i <= supply[i] + units shipped in
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j][i] for j in regions if j != i)
        outflow = gp.quicksum(x[i][j] for j in regions if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"demand_{i}")
        model.addConstr(outflow <= supply[i] + inflow, name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1324.0 (optimal) | 1324.0 (optimal) | 1324.0 (optimal) |
| 1 | 1830.6616261956501 (optimal) | 1830.6616261956501 (optimal) | 1830.6616261956501 (optimal) |
| 2 | none (infeasible or solve failed) | none (no_feasible_solution) | none (infeasible) |
| 3 | none (infeasible or solve failed) | none (no_feasible_solution) | none (infeasible) |
| 4 | 1005.5677309203406 (optimal) | 1005.5677309203406 (optimal) | 1005.5677309203406 (optimal) |
| 5 | 1506.1982101745803 (optimal) | 1506.1982101745803 (optimal) | 1506.1982101745803 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1324.0 (optimal) | 1324.0 (optimal) | 1324.0 (optimal) |
| 1 | 2879.021717345649 (optimal) | 2879.021717345649 (optimal) | 2879.0217173456485 (optimal) |
| 2 | 966.7956773601078 (optimal) | 966.7956773601078 (optimal) | 966.7956773601078 (optimal) |
| 3 | 1806.3067620744655 (optimal) | 1806.3067620744655 (optimal) | 1806.3067620744655 (optimal) |
| 4 | none (infeasible or solve failed) | none (no_feasible_solution) | none (infeasible) |
| 5 | 1280.8362238156337 (optimal) | 1280.8362238156337 (optimal) | 1280.8362238156337 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"transport_cost","evidence":"no value in the statement for diagonal self-shipping costs"}]}
```

#### Family C (Claude Sonnet 5.5)

Status unparsed; attempts 3; flag_mismatch None; flag_not_stated None; flag_any None.

```json
{"mismatch": [{"parameter": "transport_cost", "extracted": [[0,24,32,44,46],[41,0,6,11,49],[40,10,0,40,45],[22,22,34,0,1],[46,14,35,36,0]], "stated": [[0,24,32,44,46],[41,0,6,11,49],[40,10,0,40,45],[22,22,34,0,1],[46,14,35,36,0]], "evidence": "The statement says Region 2 to Region 1 costs 41, but the cost matrix description uses 'from/to' language implying symmetry is not guaranteed; however the actual mismatch is that Region 3 to Region 2 costs 10 per statement ('To Region 2 costs 10') yet the extracted matrix row 3 column 2 is 10 — no numeric mismatch found here. Re-examining: statement row 1 (Region 2): 'To Region 1 costs 41, to Region 3 costs 6, to Region 4 costs 11, to Region 5 costs 49' matches [41,0,6,11,49]. No mismatch detected."}], "not_stated": []}

Let me redo this carefully.

{"mismatch": [], "not_stated": []}
```


## 4. mamo_complex_32 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_32` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 32) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 47.0 |
| Label (original benchmark) | 47 |
| Rules that certify it | gate 47.0, gate_3fam 47.0, gate_tau 47.0, panel_base_2of3 47.0, panel_base_3of3 47.0, ind_gate 47.0, ind_gate_tau 47.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 47.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Embark on a journey through a bustling transport network in the heart of a bustling metropolis, featuring 9 critical nodes that form the backbone of this city's logistic framework. From the primary dispatch center to the ultimate distribution hub, each node plays a pivotal role in ensuring goods and resources flow seamlessly across the city.

Here's a detailed glimpse into the transport capacities (in thousands of units) between these nodes, ensuring that every node is a cog in the machine that keeps the city running:

- From Node 0 (The Source): Goods can be dispatched to Node 1 (13 units), Node 2 (19 units), Node 3 (17 units), Node 4 (7 units), Node 5 (7 units), Node 6 (11 units), Node 7 (7 units), and Node 8 (7 units).
- From Node 1: Goods can move on to Node 0 (9 units), Node 2 (19 units), Node 3 (20 units), Node 4 (10 units), Node 5 (19 units), Node 6 (20 units), Node 7 (19 units), and Node 8 (3 units).
- From Node 2: Goods can be transported to Node 0 (0 units), Node 1 (16 units), Node 3 (0 units), Node 4 (10 units), Node 5 (2 units), Node 6 (14 units), Node 7 (9 units), and Node 8 (9 units).
- From Node 3: Goods can be routed to Node 0 (6 units), Node 1 (0 units), Node 2 (5 units), Node 4 (7 units), Node 5 (18 units), Node 6 (15 units), Node 7 (20 units), and Node 8 (7 units).
- From Node 4: Goods can be forwarded to Node 0 (18 units), Node 1 (19 units), Node 2 (12 units), Node 3 (0 units), Node 5 (16 units), Node 6 (20 units), Node 7 (10 units), and Node 8 (4 units).
- From Node 5: Goods can be sent to Node 0 (3 units), Node 1 (4 units), Node 2 (8 units), Node 3 (9 units), Node 4 (20 units), Node 6 (7 units), Node 7 (8 units), and Node 8 (1 unit).
- From Node 6: Goods can be transported to Node 0 (3 units), Node 1 (14 units), Node 2 (14 units), Node 3 (16 units), Node 4 (1 unit), Node 5 (12 units), Node 7 (10 units), and Node 8 (10 units).
- From Node 7: Goods can move on to Node 0 (9 units), Node 1 (20 units), Node 2 (19 units), Node 3 (4 units), Node 4 (9 units), Node 5 (16 units), Node 6 (1 unit), and Node 8 (6 units).
- From Node 8 (The Destination): Goods from Node 0 (7 units), Node 1 (15 units), Node 2 (14 units), Node 3 (18 units), Node 4 (18 units), Node 5 (11 units), Node 6 (18 units) can be finally distributed.

A capacity of "0" signifies the absence of a direct route between those particular nodes, indicating the need for strategic planning to navigate goods through this intricate network.

Your mission is to calculate the maximum volume of goods (in thousands of units) that can be transported from Node 0, the primary dispatch center, to Node 8, the ultimate distribution hub, per unit time. This calculation must ensure that the flow of goods through each connection does not exceed its transportation capacity. What is the maximum volume of goods that can be moved from the source to the destination in thousands of units?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_0_1": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":26.0,"integer":true}}
"capacity_0_2": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_0_3": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":34.0,"integer":true}}
"capacity_0_4": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_0_5": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_0_6": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":22.0,"integer":true}}
"capacity_0_7": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_0_8": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_1_0": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_1_2": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_1_3": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_1_4": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_1_5": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_1_6": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_1_7": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_1_8": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":6.0,"integer":true}}
"capacity_2_0": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":0.0,"integer":true}}
"capacity_2_1": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_2_3": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":0.0,"integer":true}}
"capacity_2_4": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_2_5": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_2_6": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_2_7": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_2_8": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_3_0": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_3_1": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":0.0,"integer":true}}
"capacity_3_2": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":true}}
"capacity_3_4": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_3_5": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
"capacity_3_6": {"base":15,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"capacity_3_7": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_3_8": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_4_0": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
"capacity_4_1": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_4_2": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_4_3": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":0.0,"integer":true}}
"capacity_4_5": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_4_6": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_4_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_4_8": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_5_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":6.0,"integer":true}}
"capacity_5_1": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_5_2": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":16.0,"integer":true}}
"capacity_5_3": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_5_4": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_5_6": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_5_7": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":16.0,"integer":true}}
"capacity_5_8": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":2.0,"integer":true}}
"capacity_6_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":6.0,"integer":true}}
"capacity_6_1": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_6_2": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_6_3": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_6_4": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":2.0,"integer":true}}
"capacity_6_5": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_6_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_6_8": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_7_0": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_7_1": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_7_2": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":38.0,"integer":true}}
"capacity_7_3": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_7_4": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":18.0,"integer":true}}
"capacity_7_5": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_7_6": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":2.0,"integer":true}}
"capacity_7_8": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_8_0": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":14.0,"integer":true}}
"capacity_8_1": {"base":15,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"capacity_8_2": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_8_3": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
"capacity_8_4": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
"capacity_8_5": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":22.0,"integer":true}}
"capacity_8_6": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
```

Warnings:

```
[capacity_2_0] degenerate abs range (lo == hi); perturbation has no effect
[capacity_2_3] degenerate abs range (lo == hi); perturbation has no effect
[capacity_3_1] degenerate abs range (lo == hi); perturbation has no effect
[capacity_4_3] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    arcs = []
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = "capacity_{}_{}".format(i, j)
            if key in params:
                arcs.append((i, j))

    capacity = {arc: params["capacity_{}_{}".format(arc[0], arc[1])] for arc in arcs}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= capacity[(i, j)]
    model.cap = pyo.Constraint(model.arcs, rule=cap_rule)

    def flow_balance_rule(m, i):
        inflow = sum(m.flow[j, i] for (j, k) in arcs if k == i)
        outflow = sum(m.flow[i, j] for (k, j) in arcs if k == i)
        if i == source:
            return outflow - inflow >= 0
        if i == sink:
            return inflow - outflow >= 0
        return outflow - inflow == 0

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    model.objective = pyo.Objective(
        expr=sum(model.flow[source, j] for (k, j) in arcs if k == source)
        - sum(model.flow[j, source] for (j, k) in arcs if k == source),
        sense=pyo.maximize,
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j and (i,j) != (8,7)}","T":"{1,...,7}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,k] for (i,k) in A) = sum(flow[k,j] for (k,j) in A) for every k in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = tuple(range(9))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j and (i, j) != (8, 7)
    )
    incoming = {
        node: tuple((i, j) for i, j in arcs if j == node)
        for node in nodes
    }
    outgoing = {
        node: tuple((i, j) for i, j in arcs if i == node)
        for node in nodes
    }

    model.node_set = pyo.Set(initialize=nodes)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs)
    model.transit_set = pyo.Set(initialize=range(1, 8))

    model.arc_capacity = pyo.Param(
        model.arc_set,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )
    model.flow = pyo.Var(
        model.arc_set,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.arc_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arc_set,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[i, j] for i, j in incoming[node])
            == sum(network.flow[i, j] for i, j in outgoing[node])
        )

    model.flow_balance = pyo.Constraint(
        model.transit_set,
        rule=conservation_rule,
    )

    model.total_flow_objective = pyo.Objective(
        expr=(
            sum(model.flow[i, j] for i, j in outgoing[0])
            - sum(model.flow[i, j] for i, j in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Nodes: 0 through 8
    # Source: 0, Sink: 8
    # Edges: all (i,j) where i != j, except (8, 7) which doesn't exist per params
    # Build edge list from params
    
    num_nodes = 9
    edges = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    edges.append((i, j))

    capacity = {}
    for (i, j) in edges:
        capacity[(i, j)] = params[f"capacity_{i}_{j}"]

    source = 0
    sink = 8

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"flow_{i}_{j}")

    model.update()

    # Objective: maximize flow into sink
    model.setObjective(
        gp.quicksum(flow[(i, sink)] for (i, j) in edges if j == sink),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in range(num_nodes):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 47.0 (optimal) | 47.0 (optimal) | 47.0 (optimal) |
| 1 | 43.0 (optimal) | 43.0 (optimal) | 43.0 (optimal) |
| 2 | 30.0 (optimal) | 30.0 (optimal) | 30.0 (optimal) |
| 3 | 30.0 (optimal) | 30.0 (optimal) | 30.0 (optimal) |
| 4 | 51.0 (optimal) | 51.0 (optimal) | 51.0 (optimal) |
| 5 | 61.0 (optimal) | 61.0 (optimal) | 61.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 47.0 (optimal) | 47.0 (optimal) | 47.0 (optimal) |
| 1 | 43.0 (optimal) | 43.0 (optimal) | 43.0 (optimal) |
| 2 | 30.0 (optimal) | 30.0 (optimal) | 30.0 (optimal) |
| 3 | 30.0 (optimal) | 30.0 (optimal) | 30.0 (optimal) |
| 4 | 51.0 (optimal) | 51.0 (optimal) | 51.0 (optimal) |
| 5 | 61.0 (optimal) | 61.0 (optimal) | 61.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "capacity_8_0", "evidence": "no value in the statement"}, {"parameter": "capacity_8_1", "evidence": "no value in the statement"}, {"parameter": "capacity_8_2", "evidence": "no value in the statement"}, {"parameter": "capacity_8_3", "evidence": "no value in the statement"}, {"parameter": "capacity_8_4", "evidence": "no value in the statement"}, {"parameter": "capacity_8_5", "evidence": "no value in the statement"}, {"parameter": "capacity_8_6", "evidence": "no value in the statement"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
The Node 8 section lists capacities from other nodes *into* Node 8 (i.e., the incoming edges), but the extracted parameters treat them as capacities *from* Node 8 to those nodes. I need to check each value and direction carefully.

The statement says "From Node 8 (The Destination): Goods from Node 0 (7 units), Node 1 (15 units), Node 2 (14 units), Node 3 (18 units), Node 4 (18 units), Node 5 (11 units), Node 6 (18 units) can be finally distributed." This describes incoming flows to Node 8, not outgoing flows from Node 8. However, the extracted parameters are labeled `capacity_8_X` (from node 8 to node X), which is the reverse direction. That is a modeling choice, not a factual mismatch with the numbers themselves — but the values themselves need checking against what the statement gives elsewhere.

Let me check the values the statement actually gives for edges into Node 8 against the other nodes' outgoing lists:
- Node 0 → Node 8: 7 ✓ (matches `capacity_0_8 = 7`)
- Node 1 → Node 8: 3 (statement "Node 8 (3 units)" under Node 1); Node 8 section says 15. The extracted `capacity_8_1 = 15` matches the Node 8 section's "Node 1 (15 units)", but `capacity_1_8 = 3` matches Node 1's outgoing list. These are different edges entirely if treated as Node 8 → others, but as Node 8 section values they are stated.
- Node 7 → Node 8: Node 8 section does not mention Node 7 at all.

The Node 8 section omits Node 7, so `capacity_8_7` (or the Node 7→8 capacity from that section's perspective) is not stated there. But `capacity_7_8 = 6` is stated under Node 7's outgoing list, so that's fine.

The key issue: `capacity_8_X` parameters are extracted as outgoing from Node 8, but the statement's Node 8 section lists *incoming* capacities. The numbers in the Node 8 section differ from what the respective source nodes' outgoing lists say (e.g., Node 1→8 is listed as 3 under Node 1, but 15 under Node 8's section). The extracted `capacity_8_1 = 15` etc. are taken from the Node 8 section as if they are outgoing from Node 8 — the statement never states outgoing capacities from Node 8 to anywhere.

```json
{
  "mismatch": [],
  "not_stated": [
    {"parameter": "capacity_8_0", "evidence": "The Node 8 section lists incoming flows ('Goods from Node 0 (7 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 0 is stated."},
    {"parameter": "capacity_8_1", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 1 (15 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 1 is stated."},
    {"parameter": "capacity_8_2", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 2 (14 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 2 is stated."},
    {"parameter": "capacity_8_3", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 3 (18 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 3 is stated."},
    {"parameter": "capacity_8_4", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 4 (18 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 4 is stated."},
    {"parameter": "capacity_8_5", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 5 (11 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 5 is stated."},
    {"parameter": "capacity_8_6", "evidence": "The Node 8 section lists incoming flows ('Goods from...Node 6 (18 units)...'), not outgoing capacities from Node 8; no outgoing capacity from Node 8 to Node 6 is stated."}
  ]
}
```
````


## 5. mamo_complex_63 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_63` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 63) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 6218.0 |
| Label (original benchmark) | 6218 |
| Rules that certify it | gate 6218.0, panel_base_2of3 6218.0, panel_base_3of3 6218.0, ind_gate 6218.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine you are tasked with managing the distribution of medical supplies among seven regional hospitals to ensure each has enough supplies to handle an impending health crisis. Each hospital starts with a certain stock of supplies but requires a different amount to be fully prepared.

Here’s the current stock and the required supplies for each hospital:

- Hospital 1 has 160 units but needs 19 units.
- Hospital 2 has 353 units but needs 138 units.
- Hospital 3 has 171 units but needs 110 units.
- Hospital 4 has 193 units but needs 446 units.
- Hospital 5 has 102 units but needs 341 units.
- Hospital 6 has 429 units but needs 428 units.
- Hospital 7 has 284 units but needs 47 units.

To aid in your task, you can transport supplies between hospitals, but there are costs associated with each transfer depending on the routes taken. Here is the cost matrix showing the transfer costs between each pair of hospitals:

- From/To Hospital 1: To 2 costs 12, to 3 costs 47, to 4 costs 39, to 5 costs 4, to 6 costs 21, to 7 costs 31.
- From/To Hospital 2: To 1 costs 14, to 3 costs 39, to 4 costs 12, to 5 costs 31, to 6 costs 29, to 7 costs 15.
- From/To Hospital 3: To 1 costs 15, to 2 costs 6, to 4 costs 26, to 5 costs 12, to 6 costs 5, to 7 costs 3.
- From/To Hospital 4: To 1 costs 39, to 2 costs 47, to 3 costs 42, to 5 costs 33, to 6 costs 48, to 7 costs 2.
- From/To Hospital 5: To 1 costs 35, to 2 costs 25, to 3 costs 46, to 4 costs 12, to 6 costs 25, to 7 costs 45.
- From/To Hospital 6: To 1 costs 39, to 2 costs 28, to 3 costs 28, to 4 costs 11, to 5 costs 16, to 7 costs 13.
- From/To Hospital 7: To 1 costs 42, to 2 costs 43, to 3 costs 49, to 4 costs 41, to 5 costs 41, to 6 costs 18.

Your goal is to ensure that every hospital has the supplies it requires at the lowest possible transportation cost. What would be the minimum cost to ensure all hospitals are adequately supplied?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"stock": {"base":[160,353,171,193,102,429,284],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[19,138,110,446,341,428,47],"perturb":{"mode":"rel","r":0.3}}
"transfer_cost": {"base":[[0,12,47,39,4,21,31],[14,0,39,12,31,29,15],[15,6,0,26,12,5,3],[39,47,42,0,33,48,2],[35,25,46,12,0,25,45],[39,28,28,11,16,0,13],[42,43,49,41,41,18,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    n = len(stock)
    hospitals = list(range(n))

    model = pyo.ConcreteModel()
    model.hosp = pyo.Set(initialize=hospitals)

    # flow[i, j]: units shipped from hospital i to hospital j (i != j)
    model.flow = pyo.Var(model.hosp, model.hosp, domain=pyo.NonNegativeReals)

    # Fix diagonal to zero (no self-transfer)
    for i in hospitals:
        model.flow[i, i].fix(0)

    # Cost objective
    def cost_rule(mdl):
        return sum(
            transfer_cost[i][j] * mdl.flow[i, j]
            for i in hospitals
            for j in hospitals
            if i != j
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Each hospital's final stock must meet demand:
    # initial stock - outflow + inflow >= demand
    def balance_rule(mdl, i):
        outflow = sum(mdl.flow[i, j] for j in hospitals if j != i)
        inflow = sum(mdl.flow[j, i] for j in hospitals if j != i)
        return stock[i] - outflow + inflow >= demand[i]

    model.balance = pyo.Constraint(model.hosp, rule=balance_rule)

    # Cannot ship more than available initial stock out of a hospital
    def supply_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in hospitals if j != i) <= stock[i]

    model.supply_limit = pyo.Constraint(model.hosp, rule=supply_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"H":"0..6","A":"{(i,j) in H x H: i != j}"},"params":{"stock":"nonnegative vector indexed by H, from params['stock']","demand":"nonnegative vector indexed by H, from params['demand']","transfer_cost":"nonnegative matrix indexed by H x H, from params['transfer_cost']"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["stock[h] + sum(transfer[i,h] for i != h) - sum(transfer[h,j] for j != h) >= demand[h], for each h in H"],"objective":"minimize sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-seven vectors and a 7-by-7 cost matrix.

    Input sequences use zero-based hospital indices. Transfers may pass
    through intermediate hospitals, provided every final stock meets demand.
    """
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    model = pyo.ConcreteModel()

    model.hospitals = pyo.RangeSet(0, 6)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.hospitals
            for j in model.hospitals
            if i != j
        ],
    )

    model.initial_stock = pyo.Param(
        model.hospitals,
        initialize={i: stock[i] for i in model.hospitals},
        within=pyo.NonNegativeReals,
    )
    model.required_supply = pyo.Param(
        model.hospitals,
        initialize={i: demand[i] for i in model.hospitals},
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.hospitals,
        model.hospitals,
        initialize={
            (i, j): transfer_cost[i][j]
            for i in model.hospitals
            for j in model.hospitals
        },
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(
        model.routes,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(instance, h):
        incoming = sum(
            instance.transfer[i, h]
            for i in instance.hospitals
            if i != h
        )
        outgoing = sum(
            instance.transfer[h, j]
            for j in instance.hospitals
            if j != h
        )
        return (
            instance.initial_stock[h] + incoming - outgoing
            >= instance.required_supply[h]
        )

    model.supply_balance = pyo.Constraint(
        model.hospitals,
        rule=supply_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.transfer[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by retrieving the objective below.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, RuntimeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    stock = params["stock"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]

    n = len(stock)
    hospitals = range(n)

    model = gp.Model("hospital_supply")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from hospital i to hospital j
    x = [[None] * n for _ in hospitals]
    for i in hospitals:
        for j in hospitals:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    obj = gp.LinExpr()
    for i in hospitals:
        for j in hospitals:
            if i != j:
                obj += transfer_cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: for each hospital, stock - outflow + inflow >= demand
    for i in hospitals:
        outflow = gp.quicksum(x[i][j] for j in hospitals if j != i)
        inflow = gp.quicksum(x[j][i] for j in hospitals if j != i)
        model.addConstr(stock[i] - outflow + inflow >= demand[i], name=f"balance_{i}")

    # Cannot send more than available stock net of what's needed
    # (non-negativity of remaining stock after outflow)
    for i in hospitals:
        outflow = gp.quicksum(x[i][j] for j in hospitals if j != i)
        model.addConstr(outflow <= stock[i], name=f"supply_cap_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 6218.0 (optimal) | 6218.0 (optimal) | 6218.0 (optimal) |
| 1 | 3803.48450145529 (optimal) | 3803.48450145529 (optimal) | 3803.4845014552902 (optimal) |
| 2 | 5689.248556705255 (optimal) | 5688.03416376903 (optimal) | 5689.248556705255 (optimal) |
| 3 | 8529.472734254516 (optimal) | 7810.6123519005305 (optimal) | 8529.472734254516 (optimal) |
| 4 | none (infeasible_or_unbounded) | none (solve_failed) | none (infeasible) |
| 5 | 4694.974568175844 (optimal) | 4694.974568175844 (optimal) | 4694.974568175844 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 6218.0 (optimal) | 6218.0 (optimal) | 6218.0 (optimal) |
| 1 | 3803.48450145529 (optimal) | 3803.48450145529 (optimal) | 3803.4845014552902 (optimal) |
| 2 | 5689.248556705255 (optimal) | 5688.03416376903 (optimal) | 5689.248556705255 (optimal) |
| 3 | 8529.472734254516 (optimal) | 7810.6123519005305 (optimal) | 8529.472734254516 (optimal) |
| 4 | none (infeasible_or_unbounded) | none (solve_failed) | none (infeasible) |
| 5 | 4694.974568175844 (optimal) | 4694.974568175844 (optimal) | 4694.974568175844 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"transfer_cost","evidence":"The diagonal entries are not stated; zeros were filled in to complete the matrix."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
I'll compare each parameter against the statement systematically.

**stock** and **demand**: Both match the statement exactly.

**transfer_cost**: Checking each row against the stated costs.

Row 1 (from Hospital 1): stated to 2=12, 3=47, 4=39, 5=4, 6=21, 7=31. Extracted: [0,12,47,39,4,21,31]. ✓

Row 2 (from Hospital 2): stated to 1=14, 3=39, 4=12, 5=31, 6=29, 7=15. Extracted: [14,0,39,12,31,29,15]. ✓

Row 3 (from Hospital 3): stated to 1=15, 2=6, 4=26, 5=12, 6=5, 7=3. Extracted: [15,6,0,26,12,5,3]. ✓

Row 4 (from Hospital 4): stated to 1=39, 2=47, 3=42, 5=33, 6=48, 7=2. Extracted: [39,47,42,0,33,48,2]. ✓

Row 5 (from Hospital 5): stated to 1=35, 2=25, 3=46, 4=12, 6=25, 7=45. Extracted: [35,25,46,12,0,25,45]. ✓

Row 6 (from Hospital 6): stated to 1=39, 2=28, 3=28, 4=11, 5=16, 7=13. Extracted: [39,28,28,11,16,0,13]. ✓

Row 7 (from Hospital 7): stated to 1=42, 2=43, 3=49, 4=41, 5=41, 6=18. Extracted: [42,43,49,41,41,18,0]. ✓

All parameters match.

```json
{"mismatch": [], "not_stated": []}
```
````


## 6. mamo_complex_132 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_132` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 132) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 1494.0 |
| Label (original benchmark) | 1494 |
| Rules that certify it | gate 1494.0, gate_3fam 1494.0, gate_tau 1494.0, panel_base_2of3 1494.0, panel_base_3of3 1494.0, ind_gate 1494.0, ind_gate_tau 1494.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine you are managing resources for five different cities, each with its own specific needs and supplies. The cities are facing a scarcity of a critical resource, and your task is to ensure that all cities meet their requirements by redistributing the available resources most efficiently.

Initially, the cities have the following amounts of resources:
- City 1 has 221 units.
- City 2 has 98 units.
- City 3 has 337 units.
- City 4 has 425 units.
- City 5 has 250 units.

The requirements for each city to adequately meet its needs are:
- City 1 needs 128 units.
- City 2 needs 317 units.
- City 3 needs 394 units.
- City 4 needs 108 units.
- City 5 needs 101 units.

To transfer resources between these cities, there are associated costs, which differ depending on the route taken. Here’s the cost matrix for transporting resources between each pair of cities:
- From/to City 1: To City 2 costs 20, to City 3 costs 39, to City 4 costs 4, to City 5 costs 45.
- From/to City 2: To City 1 costs 1, to City 3 costs 8, to City 4 costs 23, to City 5 costs 44.
- From/to City 3: To City 1 costs 5, to City 2 costs 46, to City 4 costs 36, to City 5 costs 15.
- From/to City 4: To City 1 costs 3, to City 2 costs 5, to City 3 costs 10, to City 5 costs 27.
- From/to City 5: To City 1 costs 37, to City 2 costs 15, to City 3 costs 7, to City 4 costs 45.

Your mission is to redistribute the resources so that each city meets its required amount at the lowest possible transportation cost. What would be the minimum cost to ensure all cities have the resources they need?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supply": {"base":[221,98,337,425,250],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[128,317,394,108,101],"perturb":{"mode":"rel","r":0.3}}
"cost": {"base":[[0,20,39,4,45],[1,0,8,23,44],[5,46,0,36,15],[3,5,10,0,27],[37,15,7,45,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    cities = list(range(len(supply)))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=cities, ordered=True)

    # Flow variables: x[i,j] units shipped from i to j (diagonal excluded).
    off_diag = [(i, j) for i in cities for j in cities if i != j]
    model.od = pyo.Set(initialize=off_diag, dimen=2)
    model.x = pyo.Var(model.od, domain=pyo.NonNegativeReals)

    # Objective: minimize total transfer cost.
    def cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.od)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Each city's final holdings must be at least its demand.
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    def balance_rule(m, c):
        inflow = sum(m.x[i, c] for i in cities if i != c)
        outflow = sum(m.x[c, j] for j in cities if j != c)
        return supply[c] + inflow - outflow >= demand[c]
    model.balance = pyo.Constraint(model.C, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"C":"0..4 (cities 1..5)","A":"{(i,j) in C x C: i != j}"},"params":{"supply":"supply[i] from params['supply'][i]","demand":"demand[i] from params['demand'][i]","cost":"cost[i,j] from params['cost'][i][j]"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["For each i in C: supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i]"],"objective":"minimize sum(cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve resource redistribution using zero-based supply, demand, and cost arrays."""
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 4)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.city_supply = pyo.Param(
        model.cities,
        initialize={city: params["supply"][city] for city in model.cities},
    )
    model.city_demand = pyo.Param(
        model.cities,
        initialize={city: params["demand"][city] for city in model.cities},
    )
    model.transfer_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params["cost"][origin][destination]
            for origin, destination in model.routes
        },
    )

    model.transfer = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def resource_balance_rule(model, city):
        incoming = sum(
            model.transfer[other, city]
            for other in model.cities
            if other != city
        )
        outgoing = sum(
            model.transfer[city, other]
            for other in model.cities
            if other != city
        )
        return (
            model.city_supply[city] + incoming - outgoing
            >= model.city_demand[city]
        )

    model.resource_balance = pyo.Constraint(
        model.cities, rule=resource_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # list of 5 values, index 0..4
    demand = params["demand"]  # list of 5 values, index 0..4
    cost   = params["cost"]    # 5x5 matrix, cost[i][j]

    n = 5
    cities = range(n)

    model = gp.Model("resource_redistribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from city i to city j (i != j)
    x = {
        (i, j): model.addVar(lb=0.0, name=f"x_{i}_{j}")
        for i in cities
        for j in cities
        if i != j
    }

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in cities:
        inflow  = gp.quicksum(x[j, i] for j in cities if j != i)
        outflow = gp.quicksum(x[i, j] for j in cities if j != i)
        model.addConstr(
            supply[i] + inflow - outflow >= demand[i],
            name=f"balance_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1494.0 (optimal) | 1494.0 (optimal) | 1494.0 (optimal) |
| 1 | 1183.8183077329663 (optimal) | 1183.8183077329663 (optimal) | 1183.818307732966 (optimal) |
| 2 | 645.506644046634 (optimal) | 645.506644046634 (optimal) | 645.506644046634 (optimal) |
| 3 | 2033.2578336249637 (optimal) | 2033.2578336249637 (optimal) | 2033.2578336249637 (optimal) |
| 4 | 1169.7009341739076 (optimal) | 1169.7009341739076 (optimal) | 1169.7009341739076 (optimal) |
| 5 | 1955.2428277210392 (optimal) | 1955.2428277210392 (optimal) | 1955.2428277210392 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1494.0 (optimal) | 1494.0 (optimal) | 1494.0 (optimal) |
| 1 | 1183.8183077329663 (optimal) | 1183.8183077329663 (optimal) | 1183.818307732966 (optimal) |
| 2 | 645.506644046634 (optimal) | 645.506644046634 (optimal) | 645.506644046634 (optimal) |
| 3 | 2033.2578336249637 (optimal) | 2033.2578336249637 (optimal) | 2033.2578336249637 (optimal) |
| 4 | 1169.7009341739076 (optimal) | 1169.7009341739076 (optimal) | 1169.7009341739076 (optimal) |
| 5 | 1955.2428277210392 (optimal) | 1955.2428277210392 (optimal) | 1955.2428277210392 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"cost (diagonal entries)","evidence":"no value in the statement"}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
I'll compare each extracted parameter against the statement.

**supply**: [221, 98, 337, 425, 250] — matches exactly.

**demand**: [128, 317, 394, 108, 101] — matches exactly.

**cost**: The statement gives a 5×5 matrix (excluding self-routes). Let me check row by row.

- Row 1 (from City 1): to C2=20, C3=39, C4=4, C5=45 → [0,20,39,4,45] ✓
- Row 2 (from City 2): to C1=1, C3=8, C4=23, C5=44 → [1,0,8,23,44] ✓
- Row 3 (from City 3): to C1=5, C2=46, C4=36, C5=15 → [5,46,0,36,15] ✓
- Row 4 (from City 4): to C1=3, C2=5, C3=10, C5=27 → [3,5,10,0,27] ✓
- Row 5 (from City 5): to C1=37, C2=15, C3=7, C4=45 → [37,15,7,45,0] — extracted has cost[5][4]=45, but the statement says "to City 4 costs 45". ✓

All values match. The diagonal zeros are filled in (not stated), but those are constants that follow directly from the problem structure (no self-transfer).

```json
{"mismatch": [], "not_stated": []}
```
````


## 7. mamo_complex_133 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_133` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 133) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 1490.0 |
| Label (original benchmark) | 1490 |
| Rules that certify it | gate 1490.0, gate_3fam 1490.0, gate_tau 1490.0, panel_base_2of3 1490.0, panel_base_3of3 1490.0, ind_gate 1490.0, ind_gate_tau 1490.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine you are in charge of managing food supplies for six different cities in a region. Each city has a certain amount of food resources, but they need a specific amount to make sure they're well-prepared for an unexpected food crisis.

Here's what each city has and what they need:

- City 1 has 255 tons of food, but the requirement is 251 tons.
- City 2 has 250 tons of food, but needs 200 tons.
- City 3 has 314 tons of food, but the demand here is 366 tons.
- City 4 has only 8 tons of food, but it needs 114 tons to be safe.
- City 5 has an abundance of 385 tons but only needs 59 tons.
- City 6 has 440 tons but needs 287 tons.

You have been given the responsibility to transport food from one city to another, but it incurs transportation costs. The cost varies depending on which cities you're moving food between. Here's the cost matrix that shows how much it costs to move food from one city to any other:

- Relocating supplies from/to City 1: To City 2 costs 26, to City 3 costs 39, to City 4 costs 13, to City 5 costs 37, to City 6 costs 28.
- Relocating from/to City 2: To City 1 costs 36, to City 3 costs 48, to City 4 costs 5, to City 5 costs 22, to City 6 costs 14.
- Relocating from/to City 3: To City 1 costs 38, to City 2 costs 36, to City 4 costs 12, to City 5 costs 45, to City 6 costs 36.
- Relocating from/to City 4: To City 1 costs 32, to City 2 costs 18, to City 3 costs 47, to City 5 costs 7, to City 6 costs 9.
- Relocating from/to City 5: To City 1 costs 18, to City 2 costs 6, to City 3 costs 12, to City 4 costs 20, to City 6 costs 42.
- Relocating from/to City 6: To City 1 costs 4, to City 2 costs 28, to City 3 costs 42, to City 4 costs 43, to City 5 costs 7.

Your objective is to ensure every city has the food resources it needs at the lowest possible transportation cost. Can you determine what would be the minimum cost to ensure all cities have enough food resources?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"supply": {"base":[255,250,314,8,385,440],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[251,200,366,114,59,287],"perturb":{"mode":"rel","r":0.3}}
"cost": {"base":[[0,26,39,13,37,28],[36,0,48,5,22,14],[38,36,0,12,45,36],[32,18,47,0,7,9],[18,6,12,20,0,42],[4,28,42,43,7,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = list(range(n))

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    # x[i, j]: tons of food transported from city i to city j
    model.x = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[i][j] * md.x[i, j] for (i, j) in md.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city cannot ship out more than it has.
    def supply_rule(md, i):
        return sum(md.x[i, j] for j in md.cities if j != i) <= supply[i]

    model.supply_con = pyo.Constraint(model.cities, rule=supply_rule)

    # Each city must end up with at least its demand:
    # local supply + inflows - outflows >= demand
    def demand_rule(md, j):
        inflow = sum(md.x[i, j] for i in md.cities if i != j)
        outflow = sum(md.x[j, k] for k in md.cities if k != j)
        return supply[j] + inflow - outflow >= demand[j]

    model.demand_con = pyo.Constraint(model.cities, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":"(i,j) in cities x cities with i != j"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][i]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative, for each arc"},"constraints":["For each city i: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(cost[i,j] * shipment[i,j] for all arcs)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six-city food redistribution problem using zero-based inputs."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.food_supply = pyo.Param(
        model.cities,
        initialize=lambda mdl, city: supply[city],
        within=pyo.NonNegativeReals,
    )
    model.food_demand = pyo.Param(
        model.cities,
        initialize=lambda mdl, city: demand[city],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: cost[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(mdl, city):
        incoming = sum(
            mdl.shipment[other, city]
            for other in mdl.cities
            if other != city
        )
        outgoing = sum(
            mdl.shipment[city, other]
            for other in mdl.cities
            if other != city
        )
        return (
            mdl.food_supply[city] + incoming - outgoing
            >= mdl.food_demand[city]
        )

    model.food_balance = pyo.Constraint(
        model.cities,
        rule=food_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = tons transported from city i to city j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}") for j in cities] for i in cities]

    # No self-transport
    for i in cities:
        model.addConstr(x[i][i] == 0, name=f"no_self_{i}")

    # Each city's net outflow <= surplus (can't ship more than available)
    # Supply balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in cities:
        inflow = gp.quicksum(x[j][i] for j in cities if j != i)
        outflow = gp.quicksum(x[i][j] for j in cities if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"demand_{i}")

    # Objective: minimize total transportation cost
    obj = gp.quicksum(cost[i][j] * x[i][j] for i in cities for j in cities if i != j)
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1490.0 (optimal) | 1490.0 (optimal) | 1490.0 (optimal) |
| 1 | 2125.0243148263294 (optimal) | 2125.0243148263294 (optimal) | 2125.0243148263294 (optimal) |
| 2 | 1007.9866772867942 (optimal) | 1007.9866772867942 (optimal) | 1007.9866772867942 (optimal) |
| 3 | 947.189068307565 (optimal) | 947.189068307565 (optimal) | 947.189068307565 (optimal) |
| 4 | 2129.341810492534 (optimal) | 2129.341810492534 (optimal) | 2129.341810492534 (optimal) |
| 5 | 2776.435846735732 (optimal) | 2776.435846735732 (optimal) | 2776.435846735732 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1490.0 (optimal) | 1490.0 (optimal) | 1490.0 (optimal) |
| 1 | 2125.0243148263294 (optimal) | 2125.0243148263294 (optimal) | 2125.0243148263294 (optimal) |
| 2 | 1007.9866772867942 (optimal) | 1007.9866772867942 (optimal) | 1007.9866772867942 (optimal) |
| 3 | 947.189068307565 (optimal) | 947.189068307565 (optimal) | 947.189068307565 (optimal) |
| 4 | 2129.341810492534 (optimal) | 2129.341810492534 (optimal) | 2129.341810492534 (optimal) |
| 5 | 2776.435846735732 (optimal) | 2776.435846735732 (optimal) | 2776.435846735732 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{
  "mismatch": [],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"cost","evidence":"The statement lists only costs between different cities; no diagonal values are stated."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
I need to compare each extracted parameter against the statement carefully.

**supply**: [255, 250, 314, 8, 385, 440] — matches the statement exactly.

**demand**: [251, 200, 366, 114, 59, 287] — matches the statement exactly.

**cost matrix**: Let me check each row against the statement.

- Row 1 (from City 1): [0, 26, 39, 13, 37, 28] — statement says to City 2: 26, City 3: 39, City 4: 13, City 5: 37, City 6: 28. ✓
- Row 2 (from City 2): [36, 0, 48, 5, 22, 14] — statement says to City 1: 36, City 3: 48, City 4: 5, City 5: 22, City 6: 14. ✓
- Row 3 (from City 3): [38, 36, 0, 12, 45, 36] — statement says to City 1: 38, City 2: 36, City 4: 12, City 5: 45, City 6: 36. ✓
- Row 4 (from City 4): [32, 18, 47, 0, 7, 9] — statement says to City 1: 32, City 2: 18, City 3: 47, City 5: 7, City 6: 9. ✓
- Row 5 (from City 5): [18, 6, 12, 20, 0, 42] — statement says to City 1: 18, City 2: 6, City 3: 12, City 4: 20, City 6: 42. ✓
- Row 6 (from City 6): [4, 28, 42, 43, 7, 0] — statement says to City 1: 4, City 2: 28, City 3: 42, City 4: 43, City 5: 7. ✓

All parameters match exactly.

```json
{"mismatch": [], "not_stated": []}
```
````


## 8. mamo_complex_138 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_138` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 138) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 257.0 |
| Label (original benchmark) | 257 |
| Rules that certify it | gate 257.0, gate_3fam 257.0, gate_tau 257.0, panel_base_2of3 257.0, panel_base_3of3 257.0, ind_gate 257.0, ind_gate_tau 257.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 257.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Consider a scenario where a logistics company needs to organize a delivery route across five warehouses. These warehouses are located in different cities labeled as A, B, C, D, and E. A delivery truck has to start from any one of these warehouses, deliver goods at each of the remaining four exactly once, and finally return to the starting warehouse. The challenge here is to plan the route in a way that minimizes the total travel cost. The cost could be based on various factors like distance, fuel usage, or time spent.

Here are the details of the travel costs between the warehouses:

The cost to travel from Warehouse A to B is 15 units, to C is 88 units, to D is 54 units, and to E is 92 units.

From Warehouse B, the cost to reach A is 15 units, to C is 29 units, to D is 98 units, and to E is 33 units.

For Warehouse C, the cost to get to A is 88 units, to B is 29 units, to D is 96 units, and to E is 96 units.

Moving from Warehouse D, it costs 54 units to reach A, 98 units to get to B, 96 units to C, and 63 units to E.

Lastly, from Warehouse E, the cost to go to A is 92 units, to B is 33 units, to C is 96 units, and to D is 63 units.

How can the logistics company plan the route so that the total travel cost is minimized for the delivery truck to visit each warehouse exactly once and return to the starting warehouse?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_matrix": {"base":[[0,15,88,54,92],[15,0,29,98,33],[88,29,0,96,96],[54,98,96,0,63],[92,33,96,63,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    nodes = list(range(n))

    model = pyo.ConcreteModel()

    cost = {(i, j): float(cost_matrix[i][j]) for i in nodes for j in nodes if i != j}

    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=list(cost.keys()), dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for (i, j) in m.A)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node: exactly one outgoing and one incoming arc
    model.out_deg = pyo.Constraint(
        model.N,
        rule=lambda m, i: sum(m.x[i, j] for j in nodes if j != i) == 1,
    )
    model.in_deg = pyo.Constraint(
        model.N,
        rule=lambda m, j: sum(m.x[i, j] for i in nodes if i != j) == 1,
    )

    # Subtour elimination via single-commodity flow (MTZ-style)
    # u[i] = number of nodes visited so far when arriving at node i
    model.u = pyo.Var(model.N, bounds=(1, n - 1))

    # Fix depot node 0 as the start (u[0] = 1); shift keeps formulation valid
    model.fix_depot = pyo.Constraint(expr=model.u[0] == 1)

    arcs_non_depot = [(i, j) for (i, j) in cost.keys() if i != 0 and j != 0]

    def mtz_rule(m, i, j):
        if i != 0 and j != 0 and i != j:
            return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= (n - 2)
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(arcs_non_depot, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":[0,1,2,3,4],"R":[1,2,3,4],"A":"{(i,j) in V x V: i != j}"},"params":{"cost_matrix":"Input 5x5 matrix indexed in warehouse order A,B,C,D,E; diagonal unused"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,4] for i in R"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For distinct i,j in R: u[i] - u[j] + 5*x[i,j] <= 4"],"objective":"Minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    # Warehouse indices 0 through 4 correspond to A through E.
    model.warehouses = pyo.RangeSet(0, 4)
    model.nonroot_warehouses = pyo.RangeSet(1, 4)
    model.travel_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.warehouses
            for j in model.warehouses
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.travel_arcs,
        initialize={
            (i, j): float(cost_matrix[i][j])
            for i, j in model.travel_arcs
        },
        within=pyo.Reals,
    )

    model.route_arc = pyo.Var(model.travel_arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.nonroot_warehouses,
        domain=pyo.Reals,
        bounds=(1, 4),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.route_arc[i, j]
            for j in instance.warehouses
            if j != i
        ) == 1

    model.one_departure = pyo.Constraint(
        model.warehouses,
        rule=outgoing_rule,
    )

    def incoming_rule(instance, j):
        return sum(
            instance.route_arc[i, j]
            for i in instance.warehouses
            if i != j
        ) == 1

    model.one_arrival = pyo.Constraint(
        model.warehouses,
        rule=incoming_rule,
    )

    # Warehouse A is an arbitrary reference point for ordering the tour.
    # Every Hamiltonian cycle contains A, so this does not restrict the route.
    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[i]
            - instance.visit_order[j]
            + 5 * instance.route_arc[i, j]
            <= 4
        )

    model.subtour_elimination = pyo.Constraint(
        model.nonroot_warehouses,
        model.nonroot_warehouses,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route_arc[i, j]
            for i, j in model.travel_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import Model, GRB, quicksum


def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)
    if n < 3:
        return {"objective": None, "status": "trivial"}

    model = Model("tsp")
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    u = model.addVars(n, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    model.setObjective(
        quicksum(cost[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    for i in range(n):
        model.addConstr(quicksum(x[i, j] for j in range(n) if j != i) == 1)
        model.addConstr(quicksum(x[j, i] for j in range(n) if j != i) == 1)

    # MTZ subtour elimination (fix u[0] = 0)
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + (n - 1) * x[i, j] <= n - 2)

    model.Params.LogToConsole = 0
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_solution"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 257.0 (optimal) | 257.0 (optimal) | 257.0 (optimal) |
| 1 | 190.76276968333593 (optimal) | 190.76276968333593 (optimal) | 190.76276968333593 (optimal) |
| 2 | 242.13671558997277 (optimal) | 242.13671558997277 (optimal) | 242.13671558997277 (optimal) |
| 3 | 249.80477266789438 (optimal) | 249.80477266789438 (optimal) | 249.80477266789438 (optimal) |
| 4 | 220.93100054871493 (optimal) | 220.93100054871493 (optimal) | 220.93100054871493 (optimal) |
| 5 | 259.12612315971427 (optimal) | 259.12612315971427 (optimal) | 259.1261231597143 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 257.0 (optimal) | 257.0 (optimal) | 257.0 (optimal) |
| 1 | 190.76276968333593 (optimal) | 190.76276968333593 (optimal) | 190.76276968333593 (optimal) |
| 2 | 242.13671558997277 (optimal) | 242.13671558997277 (optimal) | 242.13671558997277 (optimal) |
| 3 | 249.80477266789438 (optimal) | 249.80477266789438 (optimal) | 249.80477266789438 (optimal) |
| 4 | 220.93100054871493 (optimal) | 220.93100054871493 (optimal) | 220.93100054871493 (optimal) |
| 5 | 259.12612315971427 (optimal) | 259.12612315971427 (optimal) | 259.1261231597143 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"cost_matrix","evidence":"The statement gives no values for the diagonal entries (A to A, B to B, C to C, D to D, or E to E)."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 9. mamo_complex_155 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_155` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 155) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 96.0 |
| Label (original benchmark) | 96 |
| Rules that certify it | gate 96.0, panel_base_2of3 96.0, panel_base_3of3 96.0, ind_gate 96.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 96.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Embark on a journey through a complex network of digital data highways, designed to facilitate the swift and secure transmission of information across 9 strategic relay stations. This network, vital for the operation of a futuristic city, relies on its capacity to handle vast amounts of data, ensuring that communication flows from its source to the intended destination without a hitch.

Here's a detailed blueprint of the data flow capacities (in terabytes per hour) from one relay station to another within this intricate system:

- From Station 0 (Source): Has the capability to dispatch data to Station 1 (15 TB), Station 2 (1 TB), Station 3 (9 TB), Station 4 (18 TB), Station 5 (12 TB), Station 6 (18 TB), Station 7 (6 TB), and Station 8 (17 TB).
- From Station 1: Can transmit data to Station 0 (14 TB), Station 2 (13 TB), Station 3 (11 TB), Station 4 (14 TB), Station 5 (10 TB), Station 6 (15 TB), Station 7 (4 TB), and Station 8 (15 TB).
- From Station 2: Can route data to Station 0 (3 TB), Station 3 (2 TB), Station 4 (14 TB), Station 5 (16 TB), Station 6 (7 TB), Station 7 (12 TB), and Station 8 (4 TB).
- From Station 3: Can forward data to Station 0 (5 TB), Station 1 (20 TB), Station 4 (9 TB), Station 5 (1 TB), Station 6 (12 TB), Station 7 (1 TB), and Station 8 (20 TB).
- From Station 4: Can push data to Station 0 (11 TB), Station 1 (18 TB), Station 2 (12 TB), Station 3 (3 TB), Station 5 (4 TB), Station 6 (16 TB), Station 7 (15 TB), and Station 8 (2 TB).
- From Station 5: Can channel data to Station 0 (13 TB), Station 1 (8 TB), Station 2 (8 TB), Station 3 (6 TB), Station 4 (4 TB), Station 6 (8 TB), Station 7 (10 TB), and Station 8 (11 TB).
- From Station 6: Can send data to Station 0 (12 TB), Station 1 (1 TB), Station 2 (3 TB), Station 3 (4 TB), Station 4 (11 TB), Station 5 (8 TB), Station 7 (10 TB), and Station 8 (19 TB).
- From Station 7: Can relay data to Station 0 (18 TB), Station 1 (3 TB), Station 2 (9 TB), Station 3 (5 TB), Station 4 (9 TB), Station 5 (17 TB), Station 6 (10 TB), and Station 8 (13 TB).
- From Station 8 (Destination): Data can be reflected back to Station 0 (9 TB), Station 1 (8 TB), Station 2 (12 TB), Station 3 (2 TB), Station 4 (5 TB), Station 5 (2 TB), Station 6 (16 TB), and Station 7 (5 TB).

In this virtual scenario, a capacity of "0" indicates that there is no direct data link between the specified stations, requiring the data to be rerouted through other nodes in the network.

Your mission is to calculate the maximum amount of data (in terabytes per hour) that can be transmitted from Station 0 (the source) to Station 8 (the destination), ensuring that the traffic flowing through each data link does not exceed its maximum capacity. What is the optimal amount of data that can be relayed from the source to the destination per hour?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_matrix": {"base":[[0,15,1,9,18,12,18,6,17],[14,0,13,11,14,10,15,4,15],[3,0,0,2,14,16,7,12,4],[5,20,0,0,9,1,12,1,20],[11,18,12,3,0,4,16,15,2],[13,8,8,6,4,0,8,10,11],[12,1,3,4,11,8,0,10,19],[18,3,9,5,9,17,10,0,13],[9,8,12,2,5,2,16,5,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap = params["capacity_matrix"]
    n = 9
    source = 0
    sink = 8

    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals, bounds=(0, None))

    def edge_ub(mdl, i, j):
        return mdl.flow[i, j] <= cap[i][j]
    model.edge_cap = pyo.Constraint(model.edges, rule=edge_ub)

    def flow_balance(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in nodes if i != k)
        outflow = sum(mdl.flow[k, j] for j in nodes if j != k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance = pyo.Constraint(model.nodes, rule=flow_balance)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in nodes if j != source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j}","T":"1..7"},"params":{"capacity_matrix":"input directed capacities","c[i,j]":"capacity_matrix[i][j] for (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= c[i,j] for every (i,j) in A","sum(flow[i,j] for j != i) == sum(flow[j,i] for j != i) for every i in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 8)
    model.transit_stations = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.stations
            for j in model.stations
            if i != j
        ],
    )

    model.edge_capacity = pyo.Param(
        model.arcs,
        initialize=lambda instance, i, j: capacity_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.edge_capacity[i, j]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(instance, i):
        return (
            sum(
                instance.flow[i, j]
                for j in instance.stations
                if j != i
            )
            == sum(
                instance.flow[j, i]
                for j in instance.stations
                if j != i
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.stations if j != 0)
            - sum(model.flow[j, 0] for j in model.stations if j != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix = params["capacity_matrix"]
    
    n = 9
    source = 0
    sink = 8
    
    # Build edge list from capacity matrix
    edges = []
    cap = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                c = capacity_matrix[i][j]
                if c > 0:
                    edges.append((i, j))
                    cap[(i, j)] = c
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables for each edge
    flow = model.addVars(edges, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 96.0 (optimal) | 96.0 (optimal) | 96.0 (optimal) |
| 1 | 95.789499143189 (optimal) | 95.789499143189 (optimal) | 95.789499143189 (optimal) |
| 2 | 87.6973503674312 (optimal) | 87.6973503674312 (optimal) | 87.6973503674312 (optimal) |
| 3 | 95.94434421743028 (optimal) | 95.94434421743028 (optimal) | 95.94434421743027 (optimal) |
| 4 | 89.19138826850099 (optimal) | 89.19138826850099 (optimal) | 89.19138826850099 (optimal) |
| 5 | 122.14668497128828 (optimal) | 89.69910234083129 (optimal) | 122.1466849712883 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 96.0 (optimal) | 96.0 (optimal) | 96.0 (optimal) |
| 1 | 95.789499143189 (optimal) | 95.789499143189 (optimal) | 95.789499143189 (optimal) |
| 2 | 87.6973503674312 (optimal) | 87.6973503674312 (optimal) | 87.6973503674312 (optimal) |
| 3 | 95.94434421743028 (optimal) | 95.94434421743028 (optimal) | 95.94434421743027 (optimal) |
| 4 | 89.19138826850099 (optimal) | 89.19138826850099 (optimal) | 89.19138826850099 (optimal) |
| 5 | 122.14668497128828 (optimal) | 89.69910234083129 (optimal) | 122.1466849712883 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity_matrix","evidence":"The statement does not give values for self-links, Station 2 → Station 1, or Station 3 → Station 2; these entries were filled with 0."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
I'll compare each row of the extracted capacity matrix against the statement.

Row 0 (from Station 0): extracted [0,15,1,9,18,12,18,6,17] — matches statement.
Row 1 (from Station 1): extracted [14,0,13,11,14,10,15,4,15] — matches statement.
Row 2 (from Station 2): extracted [3,0,0,2,14,16,7,12,4] — statement lists Station 2 → Station 1 with no value given (Station 1 is skipped entirely in the list), so the extracted value of 0 for c[2][1] is not stated. Same for c[2][2] (self-loop, trivially 0, fine).
Row 3 (from Station 3): extracted [5,20,0,0,9,1,12,1,20] — statement skips Station 2 and Station 3 (self), so c[3][2]=0 is not stated.
Row 4 (from Station 4): extracted [11,18,12,3,0,4,16,15,2] — matches statement.
Row 5 (from Station 5): extracted [13,8,8,6,4,0,8,10,11] — matches statement.
Row 6 (from Station 6): extracted [12,1,3,4,11,8,0,10,19] — matches statement.
Row 7 (from Station 7): extracted [18,3,9,5,9,17,10,0,13] — matches statement.
Row 8 (from Station 8): extracted [9,8,12,2,5,2,16,5,0] — matches statement.

For rows 2 and 3, the statement simply omits certain destination stations (implying no direct link, i.e., 0), but the statement says a capacity of "0" means no direct link — it doesn't explicitly state those values, they were inferred/filled in.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "capacity_matrix[2][1]",
      "evidence": "From Station 2: Can route data to Station 0 (3 TB), Station 3 (2 TB), Station 4 (14 TB), Station 5 (16 TB), Station 6 (7 TB), Station 7 (12 TB), and Station 8 (4 TB). — Station 1 is not listed; the 0 value was filled in."
    },
    {
      "parameter": "capacity_matrix[3][2]",
      "evidence": "From Station 3: Can forward data to Station 0 (5 TB), Station 1 (20 TB), Station 4 (9 TB), Station 5 (1 TB), Station 6 (12 TB), Station 7 (1 TB), and Station 8 (20 TB). — Station 2 is not listed; the 0 value was filled in."
    }
  ]
}
```
````


## 10. mamo_complex_164 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_164` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 164) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 60.0 |
| Label (original benchmark) | 60 |
| Rules that certify it | gate 60.0, gate_3fam 60.0, gate_tau 60.0, panel_base_2of3 60.0, panel_base_3of3 60.0, ind_gate 60.0, ind_gate_tau 60.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 60.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine a complex transportation network across 9 key hub cities that are tasked with delivering critical supplies from a central distribution center to a remote area in need. Each city (or hub) in this network can send and receive supplies through established routes, each with a specific maximum capacity. The goal is to maximize the flow of supplies from the source hub to the destination hub, ensuring that the delivery system operates at its peak efficiency without overloading any route.

Here's a detailed look at the capacities, in tons of supplies, that each route can handle between the cities:

- From City 0 (Source): Can send supplies to City 2 (20 tons), City 3 (10 tons), City 5 (2 tons), City 6 (11 tons), City 7 (5 tons), and City 8 (12 tons).
- City 1: Can receive and then send supplies to City 0 (7 tons), City 2 (5 tons), City 3 (9 tons), City 4 (9 tons), City 5 (16 tons), City 6 (1 ton), City 7 (17 tons), and City 8 (7 tons).
- City 2: Can manage supplies from City 0 (3 tons), and then distribute to City 1 (17 tons), City 3 (1 ton), City 4 (5 tons), City 5 (18 tons), City 6 (13 tons), City 7 (12 tons), and City 8 (14 tons).
- City 3: Starts with supplies from City 0 (9 tons), forwarding to City 1 (10 tons), City 2 (2 tons), City 4 (10 tons), City 5 (11 tons), City 6 (11 tons), City 7 (5 tons), and City 8 (10 tons).
- City 4: Receives from City 0 (7 tons) and redistributes to City 1 (5 tons), City 2 (1 ton), City 3 (19 tons), City 5 (19 tons), City 6 (12 tons), City 7 (14 tons), and City 8 (15 tons).
- City 5: Gathers supplies from City 0 (16 tons) and can send out to City 1 (4 tons), City 2 (6 tons), City 3 (15 tons), City 4 (19 tons), City 6 (0 tons), and City 8 (20 tons).
- City 6: Channels supplies from City 0 (3 tons) towards City 1 (0 tons), City 2 (17 tons), City 3 (16 tons), City 4 (19 tons), City 5 (8 tons), City 7 (8 tons), and City 8 (9 tons).
- City 7: Starts with resources from City 0 (14 tons), sending to City 1 (11 tons), City 2 (13 tons), City 3 (17 tons), City 4 (10 tons), City 5 (13 tons), City 6 (20 tons), and City 8 (16 tons).
- City 8 (Destination): Can receive from City 0 (20 tons), City 1 (5 tons), City 2 (20 tons), City 3 (16 tons), City 4 (0 tons), City 5 (15 tons), City 6 (1 ton), and City 7 (12 tons).

In this scenario, a "0" indicates that there is no established route for supplies to move directly between those two cities.

The challenge lies in determining the maximum tonnage of supplies that can be transported from City 0 (the source) to City 8 (the destination) without exceeding the capacity of any individual route in the network. What is the optimal value of supplies, in tons, that can be moved through this network?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cap_0_2": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"cap_0_3": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_0_5": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"cap_0_6": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_0_7": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_0_8": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_1_0": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_1_2": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_1_3": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_1_4": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_1_5": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_1_6": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":15.0,"integer":true}}
"cap_1_7": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_1_8": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_2_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"cap_2_1": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_2_3": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":15.0,"integer":true}}
"cap_2_4": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_2_5": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_2_6": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_2_7": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_2_8": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_3_0": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_3_1": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_3_2": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"cap_3_4": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_3_5": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_3_6": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_3_7": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_3_8": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_4_0": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_4_1": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_4_2": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":15.0,"integer":true}}
"cap_4_3": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_4_5": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_4_6": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_4_7": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_4_8": {"base":15,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_5_0": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_5_1": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"cap_5_2": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_5_3": {"base":15,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_5_4": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_5_6": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":true}}
"cap_5_8": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"cap_6_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"cap_6_1": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":true}}
"cap_6_2": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_6_3": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_6_4": {"base":19,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_6_5": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_6_7": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_6_8": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_7_0": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_7_1": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_7_2": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_7_3": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_7_4": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_7_5": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"cap_7_6": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"cap_7_8": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_8_1": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
"cap_8_2": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"cap_8_3": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_8_4": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":true}}
"cap_8_5": {"base":15,"perturb":{"mode":"abs","lo":0.0,"hi":35.0,"integer":true}}
"cap_8_6": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":15.0,"integer":true}}
"cap_8_7": {"base":12,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":true}}
"num_cities": {"base":9,"perturb":{"mode":"abs","lo":9.0,"hi":9.0,"integer":true}}
```

Warnings:

```
[num_cities] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = params["num_cities"]
    source = 0
    sink = N - 1

    arcs = []
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j))

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def cap_bounds(m, i, j):
        return (0.0, params["cap_%d_%d" % (i, j)])

    model.flow = pyo.Var(model.arcs, bounds=cap_bounds)

    def flow_balance(m, v):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == v)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == v)
        if v == source:
            return outflow - inflow >= 0
        elif v == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(range(N), rule=flow_balance)

    def obj_expr(m):
        return sum(m.flow[source, j] for (i, j) in arcs if i == source)

    model.obj = pyo.Objective(rule=obj_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# {
#   "sets": {"N": "range(num_cities)", "A": "(i,j) in N x N with i != j, excluding (0,1),(0,4),(5,7),(8,0)"},
#   "params": {"num_cities": "params['num_cities'] (fixed at 9)", "capacity[i,j]": "params[f'cap_{i}_{j}'] for every (i,j) in A"},
#   "variables": {"flow[i,j]": "continuous nonnegative for (i,j) in A", "flow_value": "continuous nonnegative"},
#   "constraints": ["flow[i,j] <= capacity[i,j] for every (i,j) in A", "outflow[v] - inflow[v] = flow_value if v=0, -flow_value if v=num_cities-1, otherwise 0, for every v in N"],
#   "objective": "maximize flow_value"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    nodes = tuple(range(num_cities))
    excluded_arcs = {(0, 1), (0, 4), (5, 7), (8, 0)}
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
        and (origin, destination) not in excluded_arcs
    )
    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }

    outgoing = {
        city: tuple(arc for arc in arcs if arc[0] == city)
        for city in nodes
    }
    incoming = {
        city: tuple(arc for arc in arcs if arc[1] == city)
        for city in nodes
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=nodes, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.routes,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)
    model.flow_value = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(block, origin, destination):
        return (
            block.flow[origin, destination]
            <= block.capacity[origin, destination]
        )

    model.route_limits = pyo.Constraint(
        model.routes,
        rule=capacity_rule,
    )

    def balance_rule(block, city):
        net_outflow = (
            pyo.quicksum(block.flow[arc] for arc in outgoing[city])
            - pyo.quicksum(block.flow[arc] for arc in incoming[city])
        )
        if city == 0:
            return net_outflow == block.flow_value
        if city == num_cities - 1:
            return net_outflow == -block.flow_value
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.cities,
        rule=balance_rule,
    )
    model.total_flow = pyo.Objective(
        expr=model.flow_value,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions still propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_cities = int(params["num_cities"])
    source = 0
    sink = num_cities - 1

    arcs = []
    for i in range(num_cities):
        for j in range(num_cities):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j, float(params[key])))

    model = gp.Model("maxflow")
    model.Params.OutputFlag = 0

    flow = {}
    for (i, j, cap) in arcs:
        flow[i, j] = model.addVar(lb=0.0, ub=cap, vtype=GRB.CONTINUOUS, name="f_%d_%d" % (i, j))

    # Net outflow of the source equals total shipped (the objective)
    total = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="total")
    model.addConstr(
        gp.quicksum(flow[source, j] for (i, j, _c) in arcs if i == source)
        - gp.quicksum(flow[k, source] for (k, l, _c) in arcs if l == source)
        == total
    )
    # Net inflow of the sink equals total received
    model.addConstr(
        gp.quicksum(flow[k, sink] for (k, l, _c) in arcs if l == sink)
        - gp.quicksum(flow[sink, j] for (i, j, _c) in arcs if i == sink)
        == total
    )

    # Flow conservation at every intermediate city
    for n in range(num_cities):
        if n == source or n == sink:
            continue
        model.addConstr(
            gp.quicksum(flow[i, j] for (i, j, _c) in arcs if j == n)
            - gp.quicksum(flow[i, j] for (i, j, _c) in arcs if i == n)
            == 0
        )

    model.setObjective(total, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 60.0 (optimal) | 60.0 (optimal) | 60.0 (optimal) |
| 1 | 82.0 (optimal) | 82.0 (optimal) | 82.0 (optimal) |
| 2 | 93.0 (optimal) | 93.0 (optimal) | 93.0 (optimal) |
| 3 | 99.0 (optimal) | 99.0 (optimal) | 99.0 (optimal) |
| 4 | 77.0 (optimal) | 77.0 (optimal) | 77.0 (optimal) |
| 5 | 69.0 (optimal) | 69.0 (optimal) | 69.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 60.0 (optimal) | 60.0 (optimal) | 60.0 (optimal) |
| 1 | 82.0 (optimal) | 82.0 (optimal) | 82.0 (optimal) |
| 2 | 93.0 (optimal) | 93.0 (optimal) | 93.0 (optimal) |
| 3 | 99.0 (optimal) | 99.0 (optimal) | 99.0 (optimal) |
| 4 | 77.0 (optimal) | 77.0 (optimal) | 77.0 (optimal) |
| 5 | 69.0 (optimal) | 69.0 (optimal) | 69.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{
  "mismatch": [],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch":[{"parameter":"cap_2_0","extracted":3,"stated":{"route":"0->2","capacity":3},"evidence":"City 2: Can manage supplies from City 0 (3 tons)"},{"parameter":"cap_3_0","extracted":9,"stated":{"route":"0->3","capacity":9},"evidence":"City 3: Starts with supplies from City 0 (9 tons)"},{"parameter":"cap_4_0","extracted":7,"stated":{"route":"0->4","capacity":7},"evidence":"City 4: Receives from City 0 (7 tons)"},{"parameter":"cap_5_0","extracted":16,"stated":{"route":"0->5","capacity":16},"evidence":"City 5: Gathers supplies from City 0 (16 tons)"},{"parameter":"cap_6_0","extracted":3,"stated":{"route":"0->6","capacity":3},"evidence":"City 6: Channels supplies from City 0 (3 tons)"},{"parameter":"cap_7_0","extracted":14,"stated":{"route":"0->7","capacity":14},"evidence":"City 7: Starts with resources from City 0 (14 tons)"},{"parameter":"cap_8_1","extracted":5,"stated":{"route":"1->8","capacity":5},"evidence":"City 8 (Destination): Can receive from City 0 (20 tons), City 1 (5 tons)"},{"parameter":"cap_8_2","extracted":20,"stated":{"route":"2->8","capacity":20},"evidence":"Can receive from ... City 2 (20 tons)"},{"parameter":"cap_8_3","extracted":16,"stated":{"route":"3->8","capacity":16},"evidence":"Can receive from ... City 3 (16 tons)"},{"parameter":"cap_8_4","extracted":0,"stated":{"route":"4->8","capacity":0},"evidence":"Can receive from ... City 4 (0 tons)"},{"parameter":"cap_8_5","extracted":15,"stated":{"route":"5->8","capacity":15},"evidence":"Can receive from ... City 5 (15 tons)"},{"parameter":"cap_8_6","extracted":1,"stated":{"route":"6->8","capacity":1},"evidence":"Can receive from ... City 6 (1 ton)"},{"parameter":"cap_8_7","extracted":12,"stated":{"route":"7->8","capacity":12},"evidence":"Can receive from ... City 7 (12 tons)"}],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
I'll check each extracted parameter against the statement systematically.

The statement describes capacities from each city's perspective. Let me check for mismatches:

- City 0 outgoing: 0→2=20, 0→3=10, 0→5=2, 0→6=11, 0→7=5, 0→8=12 ✓
- City 1: 1→0=7, 1→2=5, 1→3=9, 1→4=9, 1→5=16, 1→6=1, 1→7=17, 1→8=7 ✓
- City 2 incoming from 0: "City 2: Can manage supplies from City 0 (3 tons)" — this is cap_2_0=3, but the extracted cap_0_2=20 is stated under City 0. The "3 tons" here describes 2→0 direction (City 2's incoming from 0 described as a reverse route). Actually, the statement says City 2 "manages supplies from City 0 (3 tons)" which reads as cap_2_0=3. The extracted cap_2_0=3 ✓. City 2 outgoing: 2→1=17, 2→3=1, 2→4=5, 2→5=18, 2→6=13, 2→7=12, 2→8=14 ✓
- City 3: "Starts with supplies from City 0 (9 tons)" → cap_3_0=9 ✓; outgoing: 3→1=10, 3→2=2, 3→4=10, 3→5=11, 3→6=11, 3→7=5, 3→8=10 ✓
- City 4: "Receives from City 0 (7 tons)" → cap_4_0=7 ✓; outgoing: 4→1=5, 4→2=1, 4→3=19, 4→5=19, 4→6=12, 4→7=14, 4→8=15 ✓
- City 5: "Gathers supplies from City 0 (16 tons)" → cap_5_0=16 ✓; outgoing: 5→1=4, 5→2=6, 5→3=15, 5→4=19, 5→6=0, 5→8=20 ✓
- City 6: "Channels supplies from City 0 (3 tons)" → cap_6_0=3 ✓; outgoing: 6→1=0, 6→2=17, 6→3=16, 6→4=19, 6→5=8, 6→7=8, 6→8=9 ✓
- City 7: "Starts with resources from City 0 (14 tons)" → cap_7_0=14 ✓; outgoing: 7→1=11, 7→2=13, 7→3=17, 7→4=10, 7→5=13, 7→6=20, 7→8=16 ✓
- City 8 (Destination): receives from 0=20, 1=5, 2=20, 3=16, 4=0, 5=15, 6=1, 7=12. These describe cap_X_8 values. cap_0_8=12 is extracted but statement says "City 8 can receive from City 0 (20 tons)". However cap_0_8=12 was already set under City 0's outgoing. These conflict: City 0 says 0→8=12, City 8 says it receives from City 0 as 20 (which matches cap_0_2=20... no). This looks like cap_8_X outgoing routes listed under City 8, not incoming. The statement lists City 8's entries as what it "can receive" — those are the reverse routes (8→1, 8→2, etc.): 8→1=5, 8→2=20, 8→3=16, 8→4=0, 8→5=15, 8→6=1, 8→7=12 ✓. The "City 8 receives from City 0 (20 tons)" would be cap_0_8, but that's already stated as 12 under City 0. This is a mismatch.

```json
{"mismatch": [{"parameter": "cap_0_8", "extracted": 12, "stated": 20, "evidence": "City 8 (Destination): Can receive from City 0 (20 tons)"}], "not_stated": []}
```
````


## 11. mamo_complex_168 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_168` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 168) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 63.0 |
| Label (original benchmark) | 63 |
| Rules that certify it | gate 63.0, panel_base_2of3 63.0, panel_base_3of3 63.0, ind_gate 63.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 63.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine we're planning the logistics for a new high-speed data network connecting 8 major data centers across the country. This network is designed to optimize the flow of information, functioning much like a water distribution system, but for data. Each data center is connected to others through high-capacity data transmission lines, each with a specific capacity for data flow measured in terabits per second (Tbps).

Here's the setup of this futuristic data network, detailing the maximum data flow capacity from one center to another:

- From Data Center 0 (Source): Can send data to Data Center 1 (5 Tbps), Data Center 2 (16 Tbps), Data Center 3 (11 Tbps), Data Center 4 (2 Tbps), Data Center 5 (10 Tbps), Data Center 6 (17 Tbps), and Data Center 7 (2 Tbps).
- From Data Center 1: Can send data to Data Center 0 (8 Tbps), Data Center 2 (14 Tbps), Data Center 3 (14 Tbps), Data Center 4 (2 Tbps), Data Center 5 (7 Tbps), Data Center 6 (11 Tbps), and Data Center 7 (1 Tbps).
- From Data Center 2: Can send data to Data Center 0 (17 Tbps), Data Center 1 (20 Tbps), Data Center 3 (16 Tbps), Data Center 4 (13 Tbps), Data Center 6 (6 Tbps), and Data Center 7 (1 Tbps).
- From Data Center 3: Can send data to Data Center 0 (3 Tbps), Data Center 1 (16 Tbps), Data Center 2 (10 Tbps), Data Center 4 (19 Tbps), Data Center 5 (12 Tbps), Data Center 6 (3 Tbps), and Data Center 7 (15 Tbps).
- From Data Center 4: Can send data to Data Center 0 (15 Tbps), Data Center 1 (12 Tbps), Data Center 2 (19 Tbps), Data Center 3 (18 Tbps), Data Center 5 (14 Tbps), Data Center 6 (12 Tbps), and Data Center 7 (15 Tbps).
- From Data Center 5: Can send data to Data Center 0 (2 Tbps), Data Center 1 (20 Tbps), Data Center 2 (20 Tbps), Data Center 3 (17 Tbps), Data Center 4 (4 Tbps), Data Center 6 (10 Tbps), and Data Center 7 (17 Tbps).
- From Data Center 6: Can send data to Data Center 0 (15 Tbps), Data Center 1 (13 Tbps), Data Center 2 (13 Tbps), Data Center 3 (5 Tbps), Data Center 4 (10 Tbps), Data Center 5 (15 Tbps), and Data Center 7 (19 Tbps).
- From Data Center 7 (Destination): Can send data back to Data Center 0 (10 Tbps), Data Center 1 (3 Tbps), Data Center 2 (14 Tbps), Data Center 3 (11 Tbps), Data Center 4 (5 Tbps), Data Center 5 (20 Tbps), and Data Center 6 (4 Tbps).

In this network, a capacity of "0" indicates that there is no direct data line connecting those two centers.

The objective is to determine the maximum amount of data (in Tbps) that can be transmitted from Data Center 0 (the source) to Data Center 7 (the destination), ensuring that the flow through each data line does not exceed its specified capacity. What is the maximum amount of data that can be sent from the source to the destination in terabits per second?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_0_1": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_2": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_3": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_4": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_5": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_6": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_7": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_0": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_2": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_3": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_4": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_5": {"base":7,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_6": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_7": {"base":1,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_0": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_1": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_3": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_4": {"base":13,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_5": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_2_6": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_7": {"base":1,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_0": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_1": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_2": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_4": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_5": {"base":12,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_6": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_7": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_0": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_1": {"base":12,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_2": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_3": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_5": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_6": {"base":12,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_7": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_0": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_1": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_2": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_3": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_4": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_6": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_7": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_0": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_1": {"base":13,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_2": {"base":13,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_3": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_4": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_5": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_7": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_0": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_1": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_2": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_3": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_4": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_5": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_6": {"base":4,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7

    # Build arc list from params (all i != j)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    # Capacity parameter read from params dict
    def cap_init(m, i, j):
        return params["capacity_{}_{}".format(i, j)]

    model.cap = pyo.Param(model.ARC, initialize=cap_init, within=pyo.NonNegativeReals)

    # Flow variables
    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(m, i, j):
        return m.flow[i, j] <= m.cap[i, j]

    model.cap_con = pyo.Constraint(model.ARC, rule=cap_rule)

    # Flow conservation: source out - in = F, sink in - out = F, others balanced
    model.F = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(m, v):
        out_flow = sum(m.flow[v, j] for j in nodes if (v, j) in m.ARC)
        in_flow = sum(m.flow[i, v] for i in nodes if (i, v) in m.ARC)
        if v == source:
            return out_flow - in_flow == m.F
        elif v == sink:
            return in_flow - out_flow == m.F
        else:
            return out_flow - in_flow == 0

    model.balance = pyo.Constraint(model.NODE, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.F, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"{0,...,7}","A":"{(i,j) in V x V: i != j}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[v,j] - sum_i flow[i,v] = throughput if v=0, -throughput if v=7, and 0 otherwise, for every v in V"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.vertices = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, vertex):
        outgoing = sum(
            network.flow[vertex, j]
            for j in network.vertices
            if j != vertex
        )
        incoming = sum(
            network.flow[i, vertex]
            for i in network.vertices
            if i != vertex
        )

        if vertex == 0:
            return outgoing - incoming == network.throughput
        if vertex == 7:
            return outgoing - incoming == -network.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.vertices,
        rule=balance_rule,
    )

    model.max_throughput = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no solution can be loaded.
        # Still determine success solely by retrieving the objective below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    source = 0
    sink = 7

    # Build capacity dict from params
    cap = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    cap[(i, j)] = params[key]
                else:
                    cap[(i, j)] = 0.0

    edges = [(i, j) for i in range(n) for j in range(n) if i != j and cap.get((i, j), 0) > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[source, j] for (i, j) in edges if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 63.0 (optimal) | 63.0 (optimal) | 63.0 (optimal) |
| 1 | 57.77479631172628 (optimal) | 57.77479631172628 (optimal) | 59.22201261744935 (optimal) |
| 2 | 66.47289063834623 (optimal) | 66.47289063834623 (optimal) | 68.4671892345274 (optimal) |
| 3 | 57.58307731005003 (optimal) | 57.58307731005003 (optimal) | 63.70583377628491 (optimal) |
| 4 | 65.80115092108457 (optimal) | 65.80115092108457 (optimal) | 65.80115092108457 (optimal) |
| 5 | 66.43725343763383 (optimal) | 66.43725343763383 (optimal) | 66.43725343763383 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 63.0 (optimal) | 63.0 (optimal) | 63.0 (optimal) |
| 1 | 57.77479631172628 (optimal) | 57.77479631172628 (optimal) | 59.22201261744935 (optimal) |
| 2 | 66.47289063834623 (optimal) | 66.47289063834623 (optimal) | 68.4671892345274 (optimal) |
| 3 | 57.58307731005003 (optimal) | 57.58307731005003 (optimal) | 63.70583377628491 (optimal) |
| 4 | 65.80115092108457 (optimal) | 65.80115092108457 (optimal) | 65.80115092108457 (optimal) |
| 5 | 66.43725343763383 (optimal) | 66.43725343763383 (optimal) | 66.43725343763383 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "capacity_2_5", "evidence": "no value in the statement: DC 2 lists connections to 0, 1, 3, 4, 6, 7 only; the 0 Tbps default is not explicitly given for this line"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity_2_5","evidence":"no value in the statement"}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
The only issue is `capacity_2_5`. The statement's description of Data Center 2's connections omits any link to Data Center 5, so the value 0 was filled in rather than stated.

```json
{"mismatch": [], "not_stated": [{"parameter": "capacity_2_5", "evidence": "From Data Center 2: Can send data to Data Center 0 (17 Tbps), Data Center 1 (20 Tbps), Data Center 3 (16 Tbps), Data Center 4 (13 Tbps), Data Center 6 (6 Tbps), and Data Center 7 (1 Tbps). — no value given for DC 2 to DC 5"}]}
```
````


## 12. mamo_complex_170 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_170` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 170) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 54.0 |
| Label (original benchmark) | 54 |
| Rules that certify it | gate 54.0, gate_3fam 54.0, gate_tau 54.0, panel_base_2of3 54.0, panel_base_3of3 54.0, ind_gate 54.0, ind_gate_tau 54.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 54.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
In the heart of a bustling metropolis, there lies an intricate network of digital information pipelines connecting 8 crucial data centers. These centers, from the main server hub to the final relay station, are vital for processing and distributing vast amounts of data across the city. The connections between these data centers have specific bandwidth capacities that dictate the maximum flow of data (measured in terabytes per hour) that can be transmitted from one center to another.

Here's a breakdown of the network's layout and its capacities:

- From Data Center 0 (Source): Data can be sent to Center 1 (6 TB/h), Center 2 (16 TB/h), Center 3 (5 TB/h), Center 4 (6 TB/h), Center 5 (11 TB/h), Center 6 (6 TB/h), and Center 7 (4 TB/h).
- From Data Center 1: Data can be transmitted to Center 2 (8 TB/h), Center 3 (10 TB/h), Center 4 (6 TB/h), Center 5 (3 TB/h), Center 6 (6 TB/h), and Center 7 (14 TB/h).
- From Data Center 2: Can send data to Center 1 (6 TB/h), Center 3 (20 TB/h), Center 4 (7 TB/h), Center 5 (16 TB/h), Center 6 (13 TB/h), and Center 7 (14 TB/h).
- From Data Center 3: Has capacities to Center 1 (11 TB/h), Center 2 (19 TB/h), Center 4 (18 TB/h), Center 5 (5 TB/h), and Center 7 (8 TB/h).
- From Data Center 4: Can route data to Center 1 (1 TB/h), Center 2 (14 TB/h), Center 3 (18 TB/h), Center 5 (12 TB/h), Center 6 (4 TB/h), and Center 7 (7 TB/h).
- From Data Center 5: Can dispatch data to Center 1 (16 TB/h), Center 2 (3 TB/h), Center 3 (20 TB/h), Center 4 (7 TB/h), Center 6 (15 TB/h), and Center 7 (6 TB/h).
- From Data Center 6: Capable of sending to Center 1 (11 TB/h), Center 2 (4 TB/h), Center 3 (19 TB/h), Center 4 (7 TB/h), Center 5 (6 TB/h), and Center 7 (17 TB/h).
- From Data Center 7 (Destination): Can receive return data flow from Center 1 (5 TB/h), Center 2 (8 TB/h), Center 3 (17 TB/h), Center 4 (2 TB/h), Center 5 (5 TB/h), and Center 6 (4 TB/h).

In this network, a capacity of "0" signifies an absence of direct data transmission capability between any two given data centers.

The challenge is to determine the maximum amount of data that can be efficiently transmitted from Data Center 0 (the main server hub) to Data Center 7 (the final relay station) per hour, without exceeding the bandwidth capacities of the connections between the centers. What is the optimal value of data flow (in terabytes per hour) that can be achieved from the source to the destination?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_0_1": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_2": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_3": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_4": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_5": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_6": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_7": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_2": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_3": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_4": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_5": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_6": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_7": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_1": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_3": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_4": {"base":7,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_5": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_6": {"base":13,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_7": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_1": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_2": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_4": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_5": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_7": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_1": {"base":1,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_2": {"base":14,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_3": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_5": {"base":12,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_6": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"capacity_4_7": {"base":7,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_1": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_2": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_3": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_4": {"base":7,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_6": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"capacity_5_7": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_1": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_2": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_3": {"base":19,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_4": {"base":7,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_5": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"capacity_6_7": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_1": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_2": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_3": {"base":17,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_4": {"base":2,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_5": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"capacity_7_6": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"num_data_centers": {"base":8,"perturb":{"mode":"abs","lo":8.0,"hi":8.0,"integer":true}}
```

Warnings:

```
[num_data_centers] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_data_centers"])
    nodes = list(range(n))
    source = 0
    sink = n - 1

    # Directed edges: any i != j, with i not the sink and j not the source.
    # Missing capacity_*_* keys in params are treated as capacity 0.
    edge_keys = []
    for i in nodes:
        if i == sink:
            continue
        for j in nodes:
            if j == source:
                continue
            if i == j:
                continue
            edge_keys.append((i, j))

    cap = {}
    for (i, j) in edge_keys:
        pname = "capacity_%d_%d" % (i, j)
        cap[(i, j)] = params.get(pname, 0.0)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edge_keys, dimen=2)

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.edges, rule=cap_rule)

    # Flow conservation at every node except source and sink
    intermediate = [k for k in nodes if k != source and k != sink]

    def balance_rule(mdl, k):
        out_flow = sum(mdl.flow[k, j] for j in nodes if (k, j) in cap)
        in_flow = sum(mdl.flow[i, k] for i in nodes if (i, k) in cap)
        return out_flow - in_flow == 0
    model.balance_con = pyo.Constraint(intermediate, rule=balance_rule)

    # Objective: maximize net flow out of source
    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in nodes if (source, j) in cap)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"range(params['num_data_centers']); frozen size 8","A":"{(i,j): i in N, j in N\\{0}, i!=j, (i,j)!=(3,6)}","T":"N\\{0,7}"},"params":{"num_data_centers":"params['num_data_centers']","capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in T"],"objective":"maximize sum(flow[0,j] for (0,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_data_centers = params["num_data_centers"]
    if num_data_centers != 8:
        raise ValueError("num_data_centers must equal the frozen network size of 8.")

    nodes = tuple(range(int(num_data_centers)))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if destination != 0
        and origin != destination
        and (origin, destination) != (3, 6)
    )
    intermediate_nodes = tuple(node for node in nodes if node not in (0, 7))

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=intermediate_nodes, ordered=True
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, node):
        return (
            sum(network.flow[arc] for arc in incoming[node])
            == sum(network.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )
    model.objective = pyo.Objective(
        expr=sum(model.flow[arc] for arc in outgoing[0]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_data_centers"])  # should be 8

    # Build capacity dict from params
    # Edges explicitly listed in params
    edge_keys = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
        (1,2),(1,3),(1,4),(1,5),(1,6),(1,7),
        (2,1),(2,3),(2,4),(2,5),(2,6),(2,7),
        (3,1),(3,2),(3,4),(3,5),(3,7),
        (4,1),(4,2),(4,3),(4,5),(4,6),(4,7),
        (5,1),(5,2),(5,3),(5,4),(5,6),(5,7),
        (6,1),(6,2),(6,3),(6,4),(6,5),(6,7),
        (7,1),(7,2),(7,3),(7,4),(7,5),(7,6),
    ]

    capacity = {}
    for (i, j) in edge_keys:
        key = f"capacity_{i}_{j}"
        capacity[(i, j)] = params[key]

    source = 0
    sink = n - 1  # 7

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j), cap in capacity.items():
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[(source, j)] for (i, j) in capacity if i == source),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    nodes = list(range(n))
    for node in nodes:
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in capacity if i == node)
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in capacity if j == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 54.0 (optimal) | 54.0 (optimal) | 54.0 (optimal) |
| 1 | 49.681242446209495 (optimal) | 49.681242446209495 (optimal) | 49.68124244620949 (optimal) |
| 2 | 54.389227432827695 (optimal) | 54.389227432827695 (optimal) | 54.389227432827695 (optimal) |
| 3 | 62.76861832886421 (optimal) | 62.76861832886421 (optimal) | 62.76861832886421 (optimal) |
| 4 | 53.97504352690821 (optimal) | 53.97504352690821 (optimal) | 53.9750435269082 (optimal) |
| 5 | 60.73588666547878 (optimal) | 60.73588666547878 (optimal) | 60.73588666547879 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 54.0 (optimal) | 54.0 (optimal) | 54.0 (optimal) |
| 1 | 49.681242446209495 (optimal) | 49.681242446209495 (optimal) | 49.68124244620949 (optimal) |
| 2 | 54.389227432827695 (optimal) | 54.389227432827695 (optimal) | 54.389227432827695 (optimal) |
| 3 | 62.76861832886421 (optimal) | 62.76861832886421 (optimal) | 62.76861832886421 (optimal) |
| 4 | 53.97504352690821 (optimal) | 53.97504352690821 (optimal) | 53.9750435269082 (optimal) |
| 5 | 60.73588666547878 (optimal) | 60.73588666547878 (optimal) | 60.73588666547879 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{
  "mismatch": [
    {
      "parameter": "capacity_7_1",
      "extracted": 5,
      "stated": {"capacity_1_7": 5},
      "evidence": "From Data Center 7 (Destination): Can receive return data flow from Center 1 (5 TB/h)"
    },
    {
      "parameter": "capacity_7_2",
      "extracted": 8,
      "stated": {"capacity_2_7": 8},
      "evidence": "Can receive return data flow from ... Center 2 (8 TB/h)"
    },
    {
      "parameter": "capacity_7_3",
      "extracted": 17,
      "stated": {"capacity_3_7": 17},
      "evidence": "Can receive return data flow from ... Center 3 (17 TB/h)"
    },
    {
      "parameter": "capacity_7_4",
      "extracted": 2,
      "stated": {"capacity_4_7": 2},
      "evidence": "Can receive return data flow from ... Center 4 (2 TB/h)"
    },
    {
      "parameter": "capacity_7_5",
      "extracted": 5,
      "stated": {"capacity_5_7": 5},
      "evidence": "Can receive return data flow from ... Center 5 (5 TB/h)"
    },
    {
      "parameter": "capacity_7_6",
      "extracted": 4,
      "stated": {"capacity_6_7": 4},
      "evidence": "Can receive return data flow from ... Center 6 (4 TB/h)"
    }
  ],
  "not_stated": []
}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 13. mamo_complex_172 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_172` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 172) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 60.0 |
| Label (original benchmark) | 60 |
| Rules that certify it | gate 60.0, gate_3fam 60.0, gate_tau 60.0, panel_base_2of3 60.0, panel_base_3of3 60.0, ind_gate 60.0, ind_gate_tau 60.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 60.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Imagine a futuristic transportation network that connects 9 major cities across a vast region, designed to maximize the efficiency of cargo transport from the central hub to a key distribution center. Each city in this network is connected by high-capacity routes, with the ability to transport a significant volume of goods measured in thousands of tons.

Here's a detailed layout of the transportation capacities between each pair of cities:

- From City 0 (Central Hub): Cargo can be sent to City 1 (1 ton), City 2 (16 tons), City 3 (8 tons), City 4 (18 tons), City 5 (4 tons), City 6 (0 tons, indicating no direct route), City 7 (8 tons), and City 8 (5 tons).
- From City 1: Cargo can be dispatched to City 0 (15 tons), City 2 (11 tons), City 3 (8 tons), City 4 (13 tons), City 5 (2 tons), City 6 (1 ton), City 7 (7 tons), and City 8 (6 tons).
- From City 2: Shipments can go to City 0 (15 tons), City 1 (4 tons), City 3 (3 tons), City 4 (1 ton), City 5 (13 tons), City 6 (13 tons), City 7 (11 tons), and City 8 (9 tons).
- From City 3: Goods can be transported to City 0 (4 tons), City 1 (16 tons), City 2 (8 tons), City 4 (12 tons), City 5 (18 tons), City 6 (19 tons), City 7 (8 tons), and City 8 (11 tons).
- From City 4: Cargo movement is possible to City 0 (4 tons), City 1 (19 tons), City 2 (3 tons), City 3 (2 tons), City 5 (6 tons), City 6 (1 ton), City 7 (13 tons), and City 8 (14 tons).
- From City 5: Shipments can be directed to City 0 (6 tons), City 1 (19 tons), City 2 (15 tons), City 3 (10 tons), City 4 (16 tons), City 6 (17 tons), City 7 (15 tons), and City 8 (17 tons).
- From City 6: Cargo can be routed to City 0 (13 tons), City 1 (7 tons), City 2 (13 tons), City 3 (4 tons), City 4 (14 tons), City 5 (3 tons), City 7 (8 tons), and City 8 (8 tons).
- From City 7: Goods can be moved to City 0 (10 tons), City 1 (6 tons), City 2 (19 tons), City 3 (1 ton), City 4 (12 tons), City 5 (6 tons), City 6 (9 tons), and City 8 (14 tons).
- From City 8 (Key Distribution Center): This city receives and dispatches goods but primarily serves as the endpoint for cargo coming from the Central Hub.

A capacity of "0" in this context indicates that there is no established route for direct cargo transport between those two cities.

The challenge is to determine the maximum amount of cargo, in thousands of tons, that can be transported from the Central Hub (City 0) to the Key Distribution Center (City 8), ensuring that the flow of goods through each route does not surpass its highest capacity. What is the optimal value of cargo that can be moved from the Central Hub to the Key Distribution Center?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity": {"base":[[0,1,16,8,18,4,0,8,5],[15,0,11,8,13,2,1,7,6],[15,4,0,3,1,13,13,11,9],[4,16,8,0,12,18,19,8,11],[4,19,3,2,0,6,1,13,14],[6,19,15,10,16,0,17,15,17],[13,7,13,4,14,3,0,8,8],[10,6,19,1,12,6,9,0,14],[0,0,0,0,0,0,0,0,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 9
    source = 0
    sink = 8

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    # Flow variables on each directed arc, bounded by arc capacity
    model.Flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def flow_bound_rule(model, i, j):
        return model.Flow[i, j] <= capacity[i][j]
    model.FlowBoundCon = pyo.Constraint(arcs, rule=flow_bound_rule)

    # Flow conservation at every node
    def flow_conservation_rule(model, k):
        inflow = sum(model.Flow[i, k] for i in nodes if i != k)
        outflow = sum(model.Flow[k, j] for j in nodes if j != k)
        if k == source:
            return outflow - inflow == model.TotalFlow
        elif k == sink:
            return inflow - outflow == model.TotalFlow
        else:
            return inflow - outflow == 0

    model.TotalFlow = pyo.Var(domain=pyo.NonNegativeReals)
    model.FlowConservationCon = pyo.Constraint(nodes, rule=flow_conservation_rule)

    # Maximize net flow from source to sink
    model.Objective = pyo.Objective(expr=model.TotalFlow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.Objective))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"0..8","A":"{(i,j) in V x V: i != j}","T":"1..7"},"params":{"capacity":"params['capacity'], a nonnegative 9x9 matrix"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[v,j] for j != v) = sum(flow[i,v] for i != v) for v in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, 8)
    model.transit_cities = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination
        ],
    )

    model.arc_capacity = pyo.Param(
        model.cities,
        model.cities,
        initialize=lambda mdl, origin, destination: capacity_data[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return mdl.flow[origin, destination] <= mdl.arc_capacity[origin, destination]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(mdl, city):
        return (
            sum(
                mdl.flow[city, destination]
                for destination in mdl.cities
                if destination != city
            )
            == sum(
                mdl.flow[origin, city]
                for origin in mdl.cities
                if origin != city
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_cities, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in model.cities if destination != 0)
            - sum(model.flow[origin, 0] for origin in model.cities if origin != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    n = 9
    source, sink = 0, 8

    model = gp.Model("max_flow")
    model.Params.OutputFlag = 0

    flow = {}
    for i in range(n):
        for j in range(n):
            if i != j and capacity[i][j] > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], vtype=GRB.CONTINUOUS, name=f"flow_{i}_{j}")

    total = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="total")

    for k in range(n):
        if k == source or k == sink:
            continue
        inflow = gp.quicksum(flow[i, k] for (i, j) in flow if j == k)
        outflow = gp.quicksum(flow[k, j] for (i, j) in flow if i == k)
        model.addConstr(inflow - outflow == 0, name=f"balance_{k}")

    src_out = gp.quicksum(flow[source, j] for (i, j) in flow if i == source)
    model.addConstr(src_out == total, name="source_out")
    snk_in = gp.quicksum(flow[i, sink] for (i, j) in flow if j == sink)
    model.addConstr(snk_in == total, name="sink_in")

    model.setObjective(total, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    return {"objective": None, "status": "no_solution"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 60.0 (optimal) | 60.0 (optimal) | 60.0 (optimal) |
| 1 | 54.97956531842471 (optimal) | 54.979565318424704 (optimal) | 54.97956531842471 (optimal) |
| 2 | 57.04573743431192 (optimal) | 57.04573743431192 (optimal) | 57.04573743431192 (optimal) |
| 3 | 57.922505740705894 (optimal) | 57.92250574070589 (optimal) | 57.92250574070589 (optimal) |
| 4 | 59.672461799310256 (optimal) | 59.67246179931025 (optimal) | 59.67246179931024 (optimal) |
| 5 | 67.4658658840873 (optimal) | 67.4658658840873 (optimal) | 67.4658658840873 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 60.0 (optimal) | 60.0 (optimal) | 60.0 (optimal) |
| 1 | 54.97956531842471 (optimal) | 54.979565318424704 (optimal) | 54.97956531842471 (optimal) |
| 2 | 57.04573743431192 (optimal) | 57.04573743431192 (optimal) | 57.04573743431192 (optimal) |
| 3 | 57.922505740705894 (optimal) | 57.92250574070589 (optimal) | 57.92250574070589 (optimal) |
| 4 | 59.672461799310256 (optimal) | 59.67246179931025 (optimal) | 59.67246179931024 (optimal) |
| 5 | 67.4658658840873 (optimal) | 67.4658658840873 (optimal) | 67.4658658840873 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "capacity[8][*] (outgoing arcs from City 8)", "evidence": "This city receives and dispatches goods but primarily serves as the endpoint for cargo coming from the Central Hub."}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity","evidence":"From City 8 (Key Distribution Center): This city receives and dispatches goods but primarily serves as the endpoint for cargo coming from the Central Hub."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
I'll check each row of the extracted capacity matrix against the statement.

Row 0 (from City 0): [0,1,16,8,18,4,0,8,5] — matches the statement.
Row 1 (from City 1): [15,0,11,8,13,2,1,7,6] — matches.
Row 2 (from City 2): [15,4,0,3,1,13,13,11,9] — matches.
Row 3 (from City 3): [4,16,8,0,12,18,19,8,11] — matches.
Row 4 (from City 4): [4,19,3,2,0,6,1,13,14] — matches.
Row 5 (from City 5): [6,19,15,10,16,0,17,15,17] — matches.
Row 6 (from City 6): [13,7,13,4,14,3,0,8,8] — matches.
Row 7 (from City 7): [10,6,19,1,12,6,9,0,14] — matches.
Row 8 (from City 8): [0,0,0,0,0,0,0,0,0] — the statement says City 8 "primarily serves as the endpoint" and gives no outgoing capacity values. The all-zeros row was filled in by inference, not stated explicitly.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "capacity",
      "evidence": "From City 8 (Key Distribution Center): This city receives and dispatches goods but primarily serves as the endpoint for cargo coming from the Central Hub. — no outgoing capacities are given for City 8; the all-zeros row was inferred."
    }
  ]
}
```
````


## 14. mamo_complex_175 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_175` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 175) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 62.0 |
| Label (original benchmark) | 62 |
| Rules that certify it | gate 62.0, gate_3fam 62.0, gate_tau 62.0, panel_base_2of3 62.0, panel_base_3of3 62.0, ind_gate 62.0, ind_gate_tau 62.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 62.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Welcome to the challenge of optimizing the logistics network of a futuristic city, connected by an advanced transportation system comprising 8 crucial nodes. This city's system is designed to maximize the efficiency of goods transport from the central distribution hub to a primary delivery station, passing through various checkpoints and distribution centers along the way.

Here's a detailed view of the transportation capacities (in thousands of units) that each route can handle:

- From Node 0 (Source): Can dispatch goods to Node 1 (3 units), Node 2 (7 units), Node 3 (2 units), Node 4 (18 units), Node 5 (18 units), Node 6 (14 units), and Node 7 (10 units).
- From Node 1: Can send goods to Node 0 (1 unit), Node 2 (10 units), Node 3 (16 units), Node 4 (14 units), Node 6 (6 units), and Node 7 (10 units).
- From Node 2: Can transport goods to Node 0 (4 units), Node 3 (7 units), Node 4 (2 units), Node 5 (2 units), Node 6 (6 units), and Node 7 (10 units).
- From Node 3: Can move goods to Node 0 (2 units), Node 1 (3 units), Node 2 (7 units), Node 4 (20 units), Node 5 (8 units), Node 6 (6 units), and Node 7 (10 units).
- From Node 4: Can dispatch goods to Node 0 (1 unit), Node 1 (20 units), Node 2 (4 units), Node 3 (8 units), Node 5 (13 units), Node 6 (8 units), and Node 7 (1 unit).
- From Node 5: Can send goods to Node 0 (16 units), Node 1 (9 units), Node 2 (17 units), Node 3 (17 units), Node 4 (11 units), Node 6 (7 units), and Node 7 (8 units).
- From Node 6: Can transport goods to Node 0 (3 units), Node 1 (7 units), Node 2 (14 units), Node 3 (1 unit), Node 4 (20 units), Node 5 (5 units), and Node 7 (13 units).
- From Node 7 (Destination): Can receive goods from Node 0 (3 units), Node 1 (6 units), Node 2 (5 units), Node 3 (1 unit), Node 4 (14 units), Node 5 (20 units), and Node 6 (9 units).

A capacity of "0" indicates there is no direct route available between those two nodes.

The goal is to determine the maximum amount of goods (in thousands of units) that can be transported from the central distribution hub (Node 0) to the primary delivery station (Node 7) without exceeding the transport capacity of any route.

What is the optimal value of goods (in thousands of units) that can be transported from the source to the destination?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_0_1": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_0_2": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_0_3": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_0_4": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":72.0,"integer":true}}
"capacity_0_5": {"base":18,"perturb":{"mode":"abs","lo":0.0,"hi":72.0,"integer":true}}
"capacity_0_6": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":56.0,"integer":true}}
"capacity_0_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_1_0": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_1_2": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_1_3": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":64.0,"integer":true}}
"capacity_1_4": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":56.0,"integer":true}}
"capacity_1_6": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_1_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_2_0": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":16.0,"integer":true}}
"capacity_2_3": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_2_4": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_2_5": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_2_6": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_2_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_3_0": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":8.0,"integer":true}}
"capacity_3_1": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_3_2": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_3_4": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":80.0,"integer":true}}
"capacity_3_5": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_3_6": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_3_7": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
"capacity_4_0": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_4_1": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":80.0,"integer":true}}
"capacity_4_2": {"base":4,"perturb":{"mode":"abs","lo":0.0,"hi":16.0,"integer":true}}
"capacity_4_3": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_4_5": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":52.0,"integer":true}}
"capacity_4_6": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_4_7": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_5_0": {"base":16,"perturb":{"mode":"abs","lo":0.0,"hi":64.0,"integer":true}}
"capacity_5_1": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
"capacity_5_2": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":68.0,"integer":true}}
"capacity_5_3": {"base":17,"perturb":{"mode":"abs","lo":0.0,"hi":68.0,"integer":true}}
"capacity_5_4": {"base":11,"perturb":{"mode":"abs","lo":0.0,"hi":44.0,"integer":true}}
"capacity_5_6": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_5_7": {"base":8,"perturb":{"mode":"abs","lo":0.0,"hi":32.0,"integer":true}}
"capacity_6_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_6_1": {"base":7,"perturb":{"mode":"abs","lo":0.0,"hi":28.0,"integer":true}}
"capacity_6_2": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":56.0,"integer":true}}
"capacity_6_3": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_6_4": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":80.0,"integer":true}}
"capacity_6_5": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_6_7": {"base":13,"perturb":{"mode":"abs","lo":0.0,"hi":52.0,"integer":true}}
"capacity_7_0": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":12.0,"integer":true}}
"capacity_7_1": {"base":6,"perturb":{"mode":"abs","lo":0.0,"hi":24.0,"integer":true}}
"capacity_7_2": {"base":5,"perturb":{"mode":"abs","lo":0.0,"hi":20.0,"integer":true}}
"capacity_7_3": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"capacity_7_4": {"base":14,"perturb":{"mode":"abs","lo":0.0,"hi":56.0,"integer":true}}
"capacity_7_5": {"base":20,"perturb":{"mode":"abs","lo":0.0,"hi":80.0,"integer":true}}
"capacity_7_6": {"base":9,"perturb":{"mode":"abs","lo":0.0,"hi":36.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))

    # Only include arcs that actually exist (capacity key present in params)
    def arc_exists(a, b):
        return ("capacity_%d_%d" % (a, b)) in params

    arcs = [(a, b) for a in nodes for b in nodes if a != b and arc_exists(a, b)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, a, b):
        return params["capacity_%d_%d" % (a, b)]

    model.cap = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    model.net_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def inflow(mdl, n):
        return sum(mdl.flow[i, n] for i in nodes if (i, n) in arcs)

    def outflow(mdl, n):
        return sum(mdl.flow[n, j] for j in nodes if (n, j) in arcs)

    def mass_balance_rule(mdl, n):
        if n == 0:
            return outflow(mdl, n) - inflow(mdl, n) == mdl.net_flow
        elif n == 7:
            return inflow(mdl, n) - outflow(mdl, n) == mdl.net_flow
        else:
            return inflow(mdl, n) == outflow(mdl, n)

    model.balance = pyo.Constraint(nodes, rule=mass_balance_rule)

    def ub_rule(mdl, a, b):
        return mdl.flow[a, b] <= mdl.cap[a, b]

    model.upper_bound = pyo.Constraint(model.arcs, rule=ub_rule)

    model.obj = pyo.Objective(expr=model.net_flow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j} minus {(1,5),(2,1)}"},"params":{"capacity[i,j]":"params['capacity_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=7, else 0, for every i in N"],"objective":"maximize throughput"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
        and (origin, destination) not in {(1, 5), (2, 1)}
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        node: tuple(destination for origin, destination in arcs if origin == node)
        for node in nodes
    }
    incoming = {
        node: tuple(origin for origin, destination in arcs if destination == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[node, destination]
                for destination in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[origin, node]
                for origin in incoming[node]
            )
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 7:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.max_flow = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.max_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    nodes = list(range(8))
    
    # All directed edges (i, j) where i != j, excluding self-loops
    # and edges not present (capacity_1_5 etc. not in params means no edge)
    edges = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
        (1,0),(1,2),(1,3),(1,4),(1,6),(1,7),
        (2,0),(2,3),(2,4),(2,5),(2,6),(2,7),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,6),(3,7),
        (4,0),(4,1),(4,2),(4,3),(4,5),(4,6),(4,7),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),(5,7),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,7),
        (7,0),(7,1),(7,2),(7,3),(7,4),(7,5),(7,6),
    ]
    
    capacity = {}
    for (i, j) in edges:
        key = f"capacity_{i}_{j}"
        if key in params:
            capacity[(i, j)] = params[key]
        else:
            capacity[(i, j)] = 0

    source = 0
    sink = 7

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[source, j] for j in nodes if (source, j) in flow) -
        gp.quicksum(flow[j, source] for j in nodes if (j, source) in flow),
        GRB.MAXIMIZE
    )

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow = gp.quicksum(flow[i, nd] for i in nodes if (i, nd) in flow)
        out_flow = gp.quicksum(flow[nd, j] for j in nodes if (nd, j) in flow)
        model.addConstr(in_flow == out_flow, name=f"conserve_{nd}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 62.0 (optimal) | 62.0 (optimal) | 62.0 (optimal) |
| 1 | 107.0 (optimal) | 107.0 (optimal) | 107.0 (optimal) |
| 2 | 113.0 (optimal) | 113.0 (optimal) | 113.0 (optimal) |
| 3 | 138.0 (optimal) | 138.0 (optimal) | 138.0 (optimal) |
| 4 | 103.0 (optimal) | 103.0 (optimal) | 103.0 (optimal) |
| 5 | 114.0 (optimal) | 114.0 (optimal) | 114.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 62.0 (optimal) | 62.0 (optimal) | 62.0 (optimal) |
| 1 | 107.0 (optimal) | 107.0 (optimal) | 107.0 (optimal) |
| 2 | 113.0 (optimal) | 113.0 (optimal) | 113.0 (optimal) |
| 3 | 138.0 (optimal) | 138.0 (optimal) | 138.0 (optimal) |
| 4 | 103.0 (optimal) | 103.0 (optimal) | 103.0 (optimal) |
| 5 | 114.0 (optimal) | 114.0 (optimal) | 114.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
```json
{"mismatch": [], "not_stated": [{"parameter": "capacity_7_0", "evidence": "Node 7 (Destination): Can receive goods from Node 0 (3 units)"}, {"parameter": "capacity_7_1", "evidence": "Node 7 (Destination): Can receive goods from Node 1 (6 units)"}, {"parameter": "capacity_7_2", "evidence": "Node 7 (Destination): Can receive goods from Node 2 (5 units)"}, {"parameter": "capacity_7_3", "evidence": "Node 7 (Destination): Can receive goods from Node 3 (1 unit)"}, {"parameter": "capacity_7_4", "evidence": "Node 7 (Destination): Can receive goods from Node 4 (14 units)"}, {"parameter": "capacity_7_5", "evidence": "Node 7 (Destination): Can receive goods from Node 5 (20 units)"}, {"parameter": "capacity_7_6", "evidence": "Node 7 (Destination): Can receive goods from Node 6 (9 units)"}]}
```
````

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch":[{"parameter":"capacity_7_0","extracted":3,"stated":"3 from node 0 to node 7","evidence":"From Node 7 (Destination): Can receive goods from Node 0 (3 units)"},{"parameter":"capacity_7_1","extracted":6,"stated":"6 from node 1 to node 7","evidence":"Can receive goods from ... Node 1 (6 units)"},{"parameter":"capacity_7_2","extracted":5,"stated":"5 from node 2 to node 7","evidence":"Can receive goods from ... Node 2 (5 units)"},{"parameter":"capacity_7_3","extracted":1,"stated":"1 from node 3 to node 7","evidence":"Can receive goods from ... Node 3 (1 unit)"},{"parameter":"capacity_7_4","extracted":14,"stated":"14 from node 4 to node 7","evidence":"Can receive goods from ... Node 4 (14 units)"},{"parameter":"capacity_7_5","extracted":20,"stated":"20 from node 5 to node 7","evidence":"Can receive goods from ... Node 5 (20 units)"},{"parameter":"capacity_7_6","extracted":9,"stated":"9 from node 6 to node 7","evidence":"Can receive goods from ... Node 6 (9 units)"}],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 15. mamo_complex_177 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_177` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 177) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 44.0 |
| Label (original benchmark) | 44 |
| Rules that certify it | panel_base_2of3 44.0, panel_base_3of3 44.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 44.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Welcome to the challenge of optimizing the network of a futuristic transportation system that interconnects 7 strategic hubs across a thriving metropolis. These hubs, ranging from the central dispatch center to the main distribution hub, are connected by a network of high-speed transit lanes, each with a distinct capacity limitation for vehicles per hour. 

Here's a breakdown of the transit system's capabilities, indicating the maximum number of vehicles that can move from one hub to another within an hour:

- From Hub 0 (Central Dispatch): Vehicles can move to Hub 1 (15 vehicles), Hub 2 (2 vehicles), Hub 3 (16 vehicles), Hub 4 (3 vehicles), Hub 5 (5 vehicles), and Hub 6 (3 vehicles).
- From Hub 1: Vehicles can move to Hub 0 (7 vehicles), Hub 4 (19 vehicles), Hub 5 (15 vehicles), and Hub 6 (16 vehicles).
- From Hub 2: Vehicles can move to Hub 0 (11 vehicles), Hub 1 (14 vehicles), Hub 3 (14 vehicles), Hub 4 (8 vehicles), Hub 5 (11 vehicles), and Hub 6 (6 vehicles).
- From Hub 3: Vehicles can move to Hub 0 (17 vehicles), Hub 1 (11 vehicles), Hub 2 (11 vehicles), Hub 4 (11 vehicles), Hub 5 (16 vehicles), and Hub 6 (19 vehicles).
- From Hub 4: Vehicles can move to Hub 0 (10 vehicles), Hub 1 (4 vehicles), Hub 2 (17 vehicles), Hub 3 (20 vehicles), Hub 5 (12 vehicles), and Hub 6 (17 vehicles).
- From Hub 5: Vehicles can move to Hub 0 (3 vehicles), Hub 2 (4 vehicles), Hub 3 (5 vehicles), Hub 4 (20 vehicles), and Hub 6 (4 vehicles).
- From Hub 6 (Main Distribution Hub): Vehicles can move back to Hub 0 (15 vehicles), Hub 1 (2 vehicles), Hub 2 (15 vehicles), Hub 3 (18 vehicles), Hub 4 (17 vehicles), and Hub 5 (7 vehicles).

In this advanced transit network, a capacity of "0" indicates that there is no direct transit lane connecting two specific hubs.

The objective is to determine the maximum capacity of vehicles that can be dispatched from Hub 0 (the Central Dispatch Center) to Hub 6 (the Main Distribution Hub) per hour, while ensuring that the flow through each transit lane does not exceed its specified capacity limit. 

What is the maximum number of vehicles that can be optimally dispatched from the Central Dispatch Center to the Main Distribution Hub within an hour?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacities": {"base":[[0,15,2,16,3,5,3],[7,0,0,0,19,15,16],[11,14,0,14,8,11,6],[17,11,11,0,11,16,19],[10,4,17,20,0,12,17],[3,0,4,5,20,0,4],[15,2,15,18,17,7,0]],"perturb":{"mode":"abs","lo":0.0,"hi":40.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    n = 7
    source = 0
    sink = 6

    arcs = [(i, j) for i in range(n) for j in range(n)
            if i != j and capacities[i][j] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.flow[i, j] for (i, j) in m.arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= capacities[i][j]
    model.cap_constraint = pyo.Constraint(model.arcs, rule=cap_rule)

    nodes = [v for v in range(n) if v != source and v != sink]

    def balance_rule(m, v):
        inflow = sum(m.flow[i, v] for (i, j) in m.arcs if j == v)
        outflow = sum(m.flow[v, j] for (i, j) in m.arcs if i == v)
        return inflow == outflow
    model.balance_constraint = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"H":"{0,...,6}","A":"{(i,j) in H x H: i != j}"},"params":{"capacities":"Nonnegative 7x7 matrix from params['capacities']"},"variables":{"flow[i,j]":"Nonnegative real for (i,j) in A","throughput":"Nonnegative real"},"constraints":["flow[i,j] <= capacities[i][j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=6, and 0 otherwise"],"objective":"Maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve maximum flow from hub 0 to hub 6 using a 7x7 capacity matrix."""
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(7)
            for destination in range(7)
            if origin != destination
        ],
    )

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: capacities[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return mdl.flow[origin, destination] <= mdl.arc_capacity[origin, destination]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(mdl, hub):
        outgoing = sum(
            mdl.flow[hub, destination]
            for destination in mdl.hubs
            if destination != hub
        )
        incoming = sum(
            mdl.flow[origin, hub]
            for origin in mdl.hubs
            if origin != hub
        )

        if hub == 0:
            return outgoing - incoming == mdl.throughput
        if hub == 6:
            return outgoing - incoming == -mdl.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.hubs, rule=balance_rule)
    model.max_throughput = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    
    n = 7
    source = 0
    sink = 6
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Build edge list from capacities matrix
    # capacities is indexed as capacities[i][j]
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = capacities[i][j]
            if cap > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")
    
    model.update()
    
    # Flow conservation constraints for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in flow if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in flow if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[source, j] for (i, j) in flow if i == source for _ in [None])
    # Rewrite cleanly
    total_flow = gp.quicksum(flow[i, j] for (i, j) in flow if i == source)
    
    model.setObjective(total_flow, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 44.0 (optimal) | 44.0 (optimal) | 44.0 (optimal) |
| 1 | 113.0 (optimal) | 97.0 (optimal) | 139.0 (optimal) |
| 2 | 121.0 (optimal) | 121.0 (optimal) | 136.0 (optimal) |
| 3 | 122.0 (optimal) | 99.0 (optimal) | 161.0 (optimal) |
| 4 | 125.0 (optimal) | 118.0 (optimal) | 154.0 (optimal) |
| 5 | 185.0 (optimal) | 138.0 (optimal) | 207.0 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 44.0 (optimal) | 44.0 (optimal) | 44.0 (optimal) |
| 1 | 113.0 (optimal) | 97.0 (optimal) | 139.0 (optimal) |
| 2 | 121.0 (optimal) | 121.0 (optimal) | 136.0 (optimal) |
| 3 | 122.0 (optimal) | 99.0 (optimal) | 161.0 (optimal) |
| 4 | 125.0 (optimal) | 118.0 (optimal) | 154.0 (optimal) |
| 5 | 185.0 (optimal) | 138.0 (optimal) | 207.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{
  "mismatch": [
    {
      "parameter": "capacities",
      "extracted": [[0,15,2,16,3,5,3],[7,0,0,0,19,15,16],[11,14,0,14,8,11,6],[17,11,11,0,11,16,19],[10,4,17,20,0,12,17],[3,0,4,5,20,0,4],[15,2,15,18,17,7,0]],
      "stated": [[0,15,2,16,3,5,3],[7,0,0,0,19,15,16],[11,14,0,14,8,11,6],[17,11,11,0,11,16,19],[10,4,17,20,0,12,17],[3,0,4,5,20,0,4],[15,2,15,18,17,7,0]],
      "evidence": "The statement does not include a direct arc from Hub 1 to Hub 2; the extracted matrix has 0 at [1][2], which is consistent, but the statement for Hub 2 lists an arc to Hub 1 with capacity 14, while the extracted matrix has 0 at [1][2] and 14 at [2][1], so the order is correct. However, the statement for Hub 1 lists arcs to Hubs 0,4,5,6; the extracted row 1 is [7,0,0,0,19,15,16], which matches. The statement for Hub 2 lists arcs to Hubs 0,1,3,4,5,6; extracted row 2 is [11,14,0,14,8,11,6], matches. The issue is that the statement for Hub 5 lists arcs to Hubs 0,2,3,4,6; extracted row 5 is [3,0,4,5,20,0,4], matches. No mismatch found."
    }
  ],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacities[0][0]","evidence":"no value in the statement"},{"parameter":"capacities[1][1]","evidence":"no value in the statement"},{"parameter":"capacities[1][2]","evidence":"no value in the statement"},{"parameter":"capacities[1][3]","evidence":"no value in the statement"},{"parameter":"capacities[2][2]","evidence":"no value in the statement"},{"parameter":"capacities[3][3]","evidence":"no value in the statement"},{"parameter":"capacities[4][4]","evidence":"no value in the statement"},{"parameter":"capacities[5][1]","evidence":"no value in the statement"},{"parameter":"capacities[5][5]","evidence":"no value in the statement"},{"parameter":"capacities[6][6]","evidence":"no value in the statement"}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
Checking each row of the extracted matrix against the statement:

- Row 0 (Hub 0): stated → Hub1=15, Hub2=2, Hub3=16, Hub4=3, Hub5=5, Hub6=3. Extracted: [0,15,2,16,3,5,3]. ✓
- Row 1 (Hub 1): stated → Hub0=7, Hub4=19, Hub5=15, Hub6=16. No Hub2 or Hub3 connection stated. Extracted: [7,0,0,0,19,15,16]. ✓
- Row 2 (Hub 2): stated → Hub0=11, Hub1=14, Hub3=14, Hub4=8, Hub5=11, Hub6=6. Extracted: [11,14,0,14,8,11,6]. ✓
- Row 3 (Hub 3): stated → Hub0=17, Hub1=11, Hub2=11, Hub4=11, Hub5=16, Hub6=19. Extracted: [17,11,11,0,11,16,19]. ✓
- Row 4 (Hub 4): stated → Hub0=10, Hub1=4, Hub2=17, Hub3=20, Hub5=12, Hub6=17. Extracted: [10,4,17,20,0,12,17]. ✓
- Row 5 (Hub 5): stated → Hub0=3, Hub2=4, Hub3=5, Hub4=20, Hub6=4. No Hub1 connection stated. Extracted: [3,0,4,5,20,0,4]. ✓
- Row 6 (Hub 6): stated → Hub0=15, Hub1=2, Hub2=15, Hub3=18, Hub4=17, Hub5=7. Extracted: [15,2,15,18,17,7,0]. ✓

All values match the statement exactly.

```json
{"mismatch": [], "not_stated": []}
```
````


## 16. mamo_complex_203 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_203` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 203) |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 12170.0 |
| Label (original benchmark) | 12170 |
| Rules that certify it | gate 12170.0, gate_3fam 12170.0, gate_tau 12170.0, panel_base_2of3 12170.0, panel_base_3of3 12170.0, ind_gate 12170.0 |
| Expert status (Xiao et al. 2025) | kept, same label; expert label 12170 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
The China Railroad Ministry is in the process of planning relocations of freight cars among 5 regions of the country to get ready for the fall harvest. The following presents the costs of moving a car between each pair of regions. The costs are as follows: moving a car from region 1 to region 2 costs 10 units, to region 3 costs 12 units, to region 4 costs 17 units, and to region 5 costs 34 units. From region 2 to region 1 costs 10 units, to region 3 costs 18 units, to region 4 costs 8 units, and to region 5 costs 46 units. From region 3, moving a car to region 1 costs 12 units, to region 2 costs 18 units, to region 4 costs 9 units, and to region 5 costs 27 units. From region 4, the cost to move a car to region 1 is 17 units, to region 2 is 8 units, to region 3 is 9 units, and to region 5 is 20 units. Lastly, from region 5 to region 1 the cost is 34 units, to region 2 is 46 units, to region 3 is 27 units, and to region 4 is 20 units. The following displays the current number of cars and the number needed for harvest shipping in each region. Region 1 currently has 115 cars but needs 300. Region 2 has 385 cars available but requires 400. Region 3 has 410 cars against a need of 800. Region 4 is currently equipped with 480 cars, yet the need is only for 200. Finally, region 5 has 610 cars available, with a need for 300 cars. Minimize the cost to move the cars such as the need is met. Provide your answer rounded to the nearest dollar.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"transport_cost": {"base":[[0,10,12,17,34],[10,0,18,8,46],[12,18,0,9,27],[17,8,9,0,20],[34,46,27,20,0]],"perturb":{"mode":"rel","r":0.5}}
"current_supply": {"base":[115,385,410,480,610],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[300,400,800,200,300],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    transport_cost = params["transport_cost"]
    current_supply = params["current_supply"]
    demand = params["demand"]

    regions = list(range(5))

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions)
    model.pairs = pyo.Set(initialize=[(i, j) for i in regions for j in regions if i != j])

    model.x = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j] for (i, j) in m.pairs)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(m, r):
        inflow = sum(m.x[i, r] for i in regions if i != r)
        outflow = sum(m.x[r, j] for j in regions if j != r)
        return current_supply[r] + inflow - outflow >= demand[r]
    model.balance = pyo.Constraint(model.regions, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"R":[1,2,3,4,5],"A":"{(i,j) in R x R: i != j}"},"params":{"transport_cost":"nonnegative matrix indexed by R x R","current_supply":"nonnegative integer vector indexed by R","demand":"nonnegative integer vector indexed by R"},"variables":{"x[i,j]":"nonnegative integer for (i,j) in A; cars relocated"},"constraints":["For each i in R: current_supply[i] + sum(x[j,i] for j != i) - sum(x[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(transport_cost[i,j] * x[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept a 5-by-5 cost matrix and length-5 supply/demand sequences."""
    model = pyo.ConcreteModel()

    model.regions = pyo.RangeSet(1, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(1, 6)
            for destination in range(1, 6)
            if origin != destination
        ],
    )

    model.transport_cost = pyo.Param(
        model.regions,
        model.regions,
        initialize=lambda instance, origin, destination: params["transport_cost"][
            origin - 1
        ][destination - 1],
        within=pyo.NonNegativeReals,
    )
    model.current_supply = pyo.Param(
        model.regions,
        initialize=lambda instance, region: params["current_supply"][region - 1],
        within=pyo.NonNegativeIntegers,
    )
    model.demand = pyo.Param(
        model.regions,
        initialize=lambda instance, region: params["demand"][region - 1],
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def regional_balance_rule(instance, region):
        incoming = sum(
            instance.x[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.x[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.current_supply[region] + incoming - outgoing
            >= instance.demand[region]
        )

    model.regional_balance = pyo.Constraint(
        model.regions, rule=regional_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    transport_cost = params["transport_cost"]  # 5x5 matrix (list of lists), 0-indexed or 1-indexed?
    current_supply = params["current_supply"]  # list of 5 values
    demand = params["demand"]                  # list of 5 values

    n = 5
    regions = range(n)

    model = gp.Model("freight_car_relocation")
    model.setParam("OutputFlag", 0)

    # x[i][j] = number of cars moved from region i to region j (i != j)
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: cars sent out from region i <= available surplus
    # Net flow: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j, i] for j in regions if j != i)
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        model.addConstr(
            current_supply[i] + inflow - outflow >= demand[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 12170.0 (optimal) | 12170.0 (optimal) | 12170.0 (optimal) |
| 1 | 11146.767162643748 (optimal) | 11146.767162643748 (optimal) | 11147.0 (optimal) |
| 2 | 9036.45189917506 (optimal) | 9036.45189917506 (optimal) | 9036.0 (optimal) |
| 3 | 8463.934412893053 (optimal) | 8463.934412893053 (optimal) | 8464.0 (optimal) |
| 4 | 11596.624250778306 (optimal) | 11596.624250778306 (optimal) | 11597.0 (optimal) |
| 5 | 13774.196488280237 (optimal) | 13774.196488280237 (optimal) | 13774.0 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 2, 3]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 12170.0 (optimal) | 12170.0 (optimal) | 12170.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: current_supply[1] = '103.72502361277124', value type=<class 'float'>. \| Value not in parameter domain NonNegativeIntegers) | none (infeasible) |
| 2 | 3790.749535474932 (optimal) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: current_supply[1] = '148.77711119392507', value type=<class 'float'>. \| Value not in parameter domain NonNegativeIntegers) | 3791.0 (optimal) |
| 3 | 6962.376923552114 (optimal) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: current_supply[1] = '106.83173076895103', value type=<class 'float'>. \| Value not in parameter domain NonNegativeIntegers) | 6962.0 (optimal) |
| 4 | none (infeasible_or_unbounded) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: current_supply[1] = '101.71847465278363', value type=<class 'float'>. \| Value not in parameter domain NonNegativeIntegers) | none (infeasible) |
| 5 | none (infeasible_or_unbounded) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: current_supply[1] = '85.38915714231709', value type=<class 'float'>. \| Value not in parameter domain NonNegativeIntegers) | none (infeasible) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"transport_cost","evidence":"The statement gives costs only between distinct regions; it does not state the five diagonal values of 0."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```


## 17. mamo_complex_204 (Mamo ComplexLP)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `mamo_complex_204` |
| Benchmark | Mamo ComplexLP (`datasets/benchmark/mamo_complex_test.jsonl`, field `index` = 204) |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 1.0 |
| Label (original benchmark) | 1 |
| Rules that certify it | panel_base_2of3 1.0, panel_base_3of3 1.0 |
| Expert status (Xiao et al. 2025) | removed |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |

### 2. Problem text

```
Before one World Cup championship, there are 5 types of securities available for sale. The price of each share of the security is fixed and the payoff of it will be contingent on the outcome of the outcome of the world cup. The information of the 5 securities are shown in Table 1. Here, for example, Security 1’s payoff is 1 if either Argentina, Brazil, or England wins the world cup, and the payoff is 0 if Germany or Spain wins. The Share Limit is the maximum number of shares one can purchase, and Price is the current purchasing price per share of each security. There are five countries, Argentina, Brazil, England, Spain, Germany. Security 1 has a price of 0.75 and a share limit of 10. The payoff for this security is $1 in Argentina, $1 in Brazil, $1 in England, 0 in Germany, and 0 in Spain. Security 2 is priced at 0.35 with a share limit of 5. The payoff is 0 for Argentina, Brazil, or England, but it's $1 for Germany and Spain. Security 3 has a price of 0.40 and a share limit of 10. Similar to Security 2, the payoff is $1 for Argentina, $1 for Spain, and $1 for England, and 0 payoff for Germany and Brazil. Security 4, with a price of 0.75 and a share limit of 10, has payoff of $1 across all countries except for Spain. Security 5 is priced at 0.65, has a share limit of 5, and has payoff of $1 in Brazil, Germany and Spain, 0 in Argentina and England. Find the maximum worst-case revenue. Provide your answer rounded to nearest dollar.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"price": {"base":[0.75,0.35,0.4,0.75,0.65],"perturb":{"mode":"rel","r":0.5}}
"share_limit": {"base":[10,5,10,10,5],"perturb":{"mode":"rel","r":0.5}}
"payoff": {"base":[[1,1,1,0,0],[0,0,0,1,1],[1,0,1,0,1],[1,1,1,1,0],[0,1,0,1,1]],"perturb":{"mode":"abs","lo":0.0,"hi":1.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    num_sec = len(price)
    num_out = len(payoff[0])

    model = pyo.ConcreteModel()

    model.sec = pyo.RangeSet(1, num_sec)
    model.out = pyo.RangeSet(1, num_out)

    model.x = pyo.Var(model.sec, domain=pyo.NonNegativeReals)

    model.revenue = pyo.Var(model.out, domain=pyo.Reals)

    def revenue_rule(mdl, o):
        return mdl.revenue[o] == sum(payoff[s - 1][o - 1] * mdl.x[s] for s in mdl.sec)
    model.revenue_con = pyo.Constraint(model.out, rule=revenue_rule)

    def limit_rule(mdl, s):
        return mdl.x[s] <= share_limit[s - 1]
    model.limit_con = pyo.Constraint(model.sec, rule=limit_rule)

    model.worst = pyo.Var(domain=pyo.Reals)

    def worst_rule(mdl, o):
        return mdl.worst <= mdl.revenue[o]
    model.worst_con = pyo.Constraint(model.out, rule=worst_rule)

    def obj_rule(mdl):
        cost = sum(price[s - 1] * mdl.x[s] for s in mdl.sec)
        return mdl.worst - cost
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"securities":[0,1,2,3,4],"countries":["Argentina","Brazil","England","Germany","Spain"]},"params":{"price":"params['price'][i]","share_limit":"params['share_limit'][i]","payoff":"params['payoff'][i][j], columns follow countries order"},"variables":{"shares[i]":"NonNegativeIntegers","worst_case_revenue":"Reals"},"constraints":["shares[i] <= share_limit[i] for each security i","worst_case_revenue <= sum(payoff[i,j]*shares[i] for i) - sum(price[i]*shares[i] for i) for each country j"],"objective":"maximize worst_case_revenue"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.securities = pyo.RangeSet(0, 4)
    model.countries = pyo.Set(
        initialize=["Argentina", "Brazil", "England", "Germany", "Spain"],
        ordered=True,
    )
    country_columns = {
        country: column
        for column, country in enumerate(model.countries)
    }

    model.purchase_price = pyo.Param(
        model.securities,
        initialize=lambda mdl, security: params["price"][security],
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        model.securities,
        initialize=lambda mdl, security: params["share_limit"][security],
        within=pyo.NonNegativeReals,
    )
    model.security_payoff = pyo.Param(
        model.securities,
        model.countries,
        initialize=lambda mdl, security, country: params["payoff"][security][
            country_columns[country]
        ],
        within=pyo.Reals,
    )

    model.shares = pyo.Var(
        model.securities,
        domain=pyo.NonNegativeIntegers,
    )
    model.worst_case_revenue = pyo.Var(domain=pyo.Reals)

    model.share_caps = pyo.Constraint(
        model.securities,
        rule=lambda mdl, security: (
            mdl.shares[security] <= mdl.purchase_limit[security]
        ),
    )

    def outcome_revenue_rule(mdl, country):
        return mdl.worst_case_revenue <= sum(
            (
                mdl.security_payoff[security, country]
                - mdl.purchase_price[security]
            )
            * mdl.shares[security]
            for security in mdl.securities
        )

    model.outcome_revenue_limits = pyo.Constraint(
        model.countries,
        rule=outcome_revenue_rule,
    )
    model.revenue_objective = pyo.Objective(
        expr=model.worst_case_revenue,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.revenue_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price = params["price"]           # list of 5 prices
    share_limit = params["share_limit"]  # list of 5 share limits
    payoff = params["payoff"]         # 5x5 matrix: payoff[i][j] = payoff of security i under country j

    n_securities = 5
    n_countries = 5

    model = gp.Model("world_cup_securities")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of shares purchased for each security
    x = [
        model.addVar(lb=0, ub=share_limit[i], vtype=GRB.CONTINUOUS, name=f"x_{i}")
        for i in range(n_securities)
    ]

    # Auxiliary variable: worst-case revenue (minimum over all country outcomes)
    z = model.addVar(lb=-GRB.INFINITY, name="z")

    # Maximize worst-case revenue
    model.setObjective(z, GRB.MAXIMIZE)

    # For each country outcome, revenue = sum of payoffs - cost of portfolio
    # cost = sum_i price[i] * x[i]  (paid upfront, fixed)
    # revenue under country j = sum_i payoff[i][j] * x[i] - sum_i price[i] * x[i]
    # z <= revenue under each country j

    cost = gp.quicksum(price[i] * x[i] for i in range(n_securities))

    for j in range(n_countries):
        revenue_j = gp.quicksum(payoff[i][j] * x[i] for i in range(n_securities)) - cost
        model.addConstr(z <= revenue_j, name=f"worst_case_country_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1.0 (optimal) | 0.9999999999999998 (optimal) | 1.0 (optimal) |
| 1 | 2.7100976732035633 (optimal) | 2.478357171071687 (optimal) | 3.0 (optimal) |
| 2 | 3.954867735848733 (optimal) | 3.5297162054478126 (optimal) | 4.0 (optimal) |
| 3 | 1.583425957362449 (optimal) | 1.3035915317883648 (optimal) | 2.0 (optimal) |
| 4 | 0.07790019978221885 (optimal) | 0.07230709116345005 (optimal) | 0.0 (optimal) |
| 5 | 4.255055527830258 (optimal) | 3.960900358319986 (optimal) | 4.0 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1.0 (optimal) | 0.9999999999999998 (optimal) | 1.0 (optimal) |
| 1 | 2.9712869135266087 (optimal) | 2.5311725416220945 (optimal) | 3.0 (optimal) |
| 2 | -0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) |
| 3 | -0.0 (optimal) | 0.0 (optimal) | 0.0 (optimal) |
| 4 | 1.5727747307379527 (optimal) | 1.2361519169214037 (optimal) | 2.0 (optimal) |
| 5 | 0.13202192553706915 (optimal) | 0.13011632458477262 (optimal) | 0.0 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch": [{"parameter": "payoff", "extracted": [[1, 1, 1, 0, 0], [0, 0, 0, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 0], [0, 1, 0, 1, 1]], "stated": [[1, 1, 1, 0, 0], [0, 0, 0, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 0], [0, 1, 0, 0, 1]], "evidence": "Security 5 ... has payoff of $1 in Brazil, Germany and Spain, 0 in Argentina and England"}], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"payoff","evidence":"Security 4 \"has payoff of $1 across all countries except for Spain\"; Spain’s payoff is not specified."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
Looking at each parameter against the statement:

**price**: [0.75, 0.35, 0.4, 0.75, 0.65] — matches exactly.

**share_limit**: [10, 5, 10, 10, 5] — matches exactly.

**payoff**: Check each row against the statement.
- Security 1: [1,1,1,0,0] — Argentina, Brazil, England = 1; Germany, Spain = 0. Matches.
- Security 2: [0,0,0,1,1] — 0 for Argentina, Brazil, England; 1 for Germany, Spain. Matches.
- Security 3: [1,0,1,0,1] — "$1 for Argentina, $1 for Spain, and $1 for England, and 0 payoff for Germany and Brazil." Extracted row is [1,0,1,0,1] (Argentina=1, Brazil=0, England=1, Germany=0, Spain=1). Matches.
- Security 4: [1,1,1,1,0] — "$1 across all countries except Spain." Argentina=1, Brazil=1, England=1, Germany=1, Spain=0. Matches.
- Security 5: [0,1,0,1,1] — "$1 in Brazil, Germany and Spain, 0 in Argentina and England." Argentina=0, Brazil=1, England=0, Germany=1, Spain=1. Matches.

All parameters match the statement.

```json
{"mismatch": [], "not_stated": []}
```
````

