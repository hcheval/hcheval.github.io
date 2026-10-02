# Lab 4: Testing

We will first go through running some simple unit tests 
(simple ones using `pytest`, and later property-based tests with `hypothesis`).
Then, we will see a small example of mutations testing, 
and finally an example of a continuous integration workflow on github, 
that automates running the tests at every push. 

```bash
python -m venv .venv && source .venv/bin/activate
pip install pytest hypothesis
```

`pytest` discovers files matching `test_*.py` and runs functions starting with `test_`.

---

## pytest

Put the following in `utils.py`:

```python
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

def merge_sorted(a, b):
    result = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result

def parse_pair(s):
    """Parse 'a:b' into (int, int). Raises ValueError on bad input."""
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError(f"expected 'a:b', got '{s}'")
    return int(parts[0]), int(parts[1])
```

**Exercise:** Create `test_utils.py`. Write unit tests for all three functions.

For `clamp`: values inside the range, outside below, outside above, exactly on the boundaries, `lo == hi`.

For `merge_sorted`: normal case, one or both lists empty, duplicates across them.

For `parse_pair`: valid inputs and the various ways it can fail. Use `pytest.raises` for exceptions:

```python
import pytest

def test_parse_pair_no_separator():
    with pytest.raises(ValueError):
        parse_pair("hello")
```

Run with `pytest -v`.

**Exercise:** Add this to `utils.py`. It should return a sorted list with duplicates removed, but it has a bug.

```python
def unique_sorted(lst):
    result = sorted(lst)
    i = 0
    while i < len(result) - 1:
        if result[i] == result[i + 1]:
            result.pop(i)
        i += 1
    return result
```

Write tests that expose the bug. It passes on obvious inputs, so think about what specific pattern of duplicates would break it.

---

## Hypothesis

The idea behind property-based testing: instead of writing individual examples (`assert f(3) == 7`), state a property that should hold for all inputs and let the framework generate hundreds of random cases. When it finds a failure, it shrinks the input to the smallest counterexample.

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
```

A *strategy* describes how to generate values: `st.integers()`, `st.text()`, `st.lists(st.integers())`, `st.floats(allow_nan=False)`, etc. Strategies compose: `st.lists(st.integers()).map(sorted)` generates sorted lists.

**Exercise:** Write property-based tests for `clamp` and `merge_sorted`.

For `clamp`: result lands inside `[lo, hi]`, idempotence (`clamp(clamp(x, lo, hi), lo, hi) == clamp(x, lo, hi)`), no-op when input is already in range. The properties only make sense when `lo <= hi`, use `assume`:

```python
from hypothesis import assume

@given(st.integers(), st.integers(), st.integers())
def test_clamp_in_bounds(x, lo, hi):
    assume(lo <= hi)
    result = clamp(x, lo, hi)
    assert lo <= result <= hi
```

For `merge_sorted`, the inputs need to already be sorted. Generate them with `.map(sorted)`:

```python
sorted_lists = st.lists(st.integers()).map(sorted)
```

Properties: result is sorted, length is `len(a) + len(b)`, and the result is a permutation of `a + b` (check via `sorted(result) == sorted(a + b)`).

**Exercise:** Implement `chunk` and `flatten` in `chunking.py` so that the tests below pass.

```python
def chunk(lst, n):
    """Split lst into consecutive groups of n elements.
    The last group may be shorter.
    chunk([1,2,3,4,5], 2) -> [[1,2], [3,4], [5]]
    """
    ...

def flatten(lst_of_lsts):
    """Concatenate a list of lists into a single list.
    flatten([[1,2], [3,4], [5]]) -> [1,2,3,4,5]
    """
    ...
```

`test_chunking.py`:

```python
from hypothesis import given, assume
from hypothesis import strategies as st
from chunking import chunk, flatten

sizes = st.integers(min_value=1, max_value=50)

@given(st.lists(st.integers()), sizes)
def test_roundtrip(lst, n):
    assert flatten(chunk(lst, n)) == lst

@given(st.lists(st.integers()), sizes)
def test_all_chunks_correct_size(lst, n):
    chunks = chunk(lst, n)
    for c in chunks[:-1]:
        assert len(c) == n
    if chunks:
        assert 1 <= len(chunks[-1]) <= n

@given(st.lists(st.integers()), sizes)
def test_number_of_chunks(lst, n):
    import math
    chunks = chunk(lst, n)
    if not lst:
        assert chunks == []
    else:
        assert len(chunks) == math.ceil(len(lst) / n)

@given(st.lists(st.integers()), sizes)
def test_total_elements(lst, n):
    chunks = chunk(lst, n)
    assert sum(len(c) for c in chunks) == len(lst)

@given(st.lists(st.lists(st.integers(), max_size=10), max_size=10))
def test_flatten_then_chunk_preserves_elements(lst_of_lsts):
    flat = flatten(lst_of_lsts)
    assert flat == [x for sub in lst_of_lsts for x in sub]

def test_chunk_empty():
    assert chunk([], 3) == []

def test_flatten_empty():
    assert flatten([]) == []
    assert flatten([[], [], []]) == []
```

**Exercise:** Implement `merge_intervals` in `intervals.py` so that the tests below pass.

```python
def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.
    merge_intervals([(1, 3), (2, 5), (8, 10)]) -> [(1, 5), (8, 10)]
    merge_intervals([(1, 5), (2, 3)])           -> [(1, 5)]
    Each interval is (start, end) with start <= end.
    """
    ...
```

`test_intervals.py`:

```python
from hypothesis import given
from hypothesis import strategies as st
from intervals import merge_intervals

interval = st.tuples(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100),
).map(lambda t: (min(t), max(t)))

intervals = st.lists(interval, max_size=20)

def points_covered(ivs):
    return {x for a, b in ivs for x in range(a, b + 1)}

@given(intervals)
def test_output_sorted(ivs):
    result = merge_intervals(ivs)
    starts = [a for a, _ in result]
    assert starts == sorted(starts)

@given(intervals)
def test_output_non_overlapping(ivs):
    result = merge_intervals(ivs)
    for i in range(len(result) - 1):
        assert result[i][1] < result[i + 1][0]

@given(intervals)
def test_coverage_preserved(ivs):
    assert points_covered(ivs) == points_covered(merge_intervals(ivs))

@given(intervals)
def test_idempotent(ivs):
    once = merge_intervals(ivs)
    twice = merge_intervals(once)
    assert once == twice

@given(intervals)
def test_each_output_interval_valid(ivs):
    for a, b in merge_intervals(ivs):
        assert a <= b

@given(intervals, intervals)
def test_merge_union(ivs1, ivs2):
    """Merging the concatenation covers the union of both."""
    combined = merge_intervals(ivs1 + ivs2)
    separate = points_covered(merge_intervals(ivs1)) | points_covered(merge_intervals(ivs2))
    assert points_covered(combined) == separate

def test_empty():
    assert merge_intervals([]) == []
```

---

## Mutation testing

```bash
pip install mutmut
```

**Exercise:** Take `clamp` and its tests, put them in their own files (`clamp.py`, `test_clamp.py`), and run:

```bash
mutmut run --paths-to-mutate=clamp.py --tests-dir=.
mutmut results
```

`mutmut` modifies the source code (changing `<` to `<=`, swapping `lo` for `hi`, etc.) and re-runs the tests for each mutation. If the tests still pass after a mutation, that mutant "survived", meaning the test suite has a gap there. Inspect survivors with `mutmut show <id>`, write tests that catch them, repeat.

Do the same for `merge_sorted`. Goal: zero surviving mutants for both.

---

## CI

**Exercise:** Push the code to GitHub. Add `.github/workflows/tests.yml`:

```yaml
name: tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest hypothesis
      - run: pytest -v
```

Push and check the Actions tab.
