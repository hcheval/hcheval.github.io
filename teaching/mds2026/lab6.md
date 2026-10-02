# Lab 6: 


## Exercise 1 
A debugger is a tool that allows us to stop the execution of a program and inspect its state 
at a certain point. We will consider the builtin python debugger in the following,
but the principle applies to other tools like `gdb`. 

The basic way to use a debugger is to spawn an interactive debug shell and set a `breakpoint` 
(with the syntax `b <location>`, where `<location>` might be a line number, a function name, etc.).
The program will execute normally until it reaches that breakpoint, where it will pause. 
At that point, we can use commands like `p <variable>` to print the value of a variable at that point,
`c` to continue the execution until the next breakpoint, `n` to move to the next step in the execution
and `s` to step *into* a function call.


The following program is a simple parser and evaluator for arithmetic expressions. 
```
import re


def tokenize(expr):
    """Split an expression into numbers and operators."""
    return re.findall(r'\d+|[+\-*()]', expr)


def parse_factor(tokens, pos):
    """Parse a number or parenthesized expression."""
    if tokens[pos] == '(':
        val, pos = parse_expr(tokens, pos + 1)
        return val, pos + 1  # skip ')'
    return int(tokens[pos]), pos + 1


def parse_term(tokens, pos):
    """Parse multiplication."""
    left, pos = parse_factor(tokens, pos)
    if pos < len(tokens) and tokens[pos] == '*':
        right, pos = parse_term(tokens, pos + 1)
        return left * right, pos
    return left, pos


def parse_expr(tokens, pos):
    """Parse addition and subtraction."""
    left, pos = parse_term(tokens, pos)
    if pos < len(tokens) and tokens[pos] in ('+', '-'):
        op = tokens[pos]
        right, pos = parse_expr(tokens, pos + 1)
        if op == '+':
            return left + right, pos
        else:
            return left - right, pos
    return left, pos


def evaluate(expr):
    tokens = tokenize(expr)
    result, _ = parse_expr(tokens, 0)
    return result


tests = [
    ("2 + 3",         5),
    ("2 * 3 + 1",     7),
    ("10 - 3 - 2",    5),
    ("(10 - 3) * 2",  14),
]

for expr, expected in tests:
    result = evaluate(expr)
    status = "OK" if result == expected else "ERROR"
    print(f"{expr:>16} = {result:<4}  expected {expected:<4} [{status}]")
```
As you can see, the third test fails. 
Run the program in debug mode with `python -m pdb ex1.py` and try to identify 
where the bug is coming from. 


## Exercise 2 
Below is a barebones C implementation of dynamic vectors. 
```
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int* data;
    int size;
    int capacity;
} Vec;

Vec* vec_new(int capacity) {
    Vec* v = malloc(sizeof(Vec));
    v->data = malloc(capacity * sizeof(int));
    v->size = 0;
    v->capacity = capacity;
    return v;
}

void vec_push(Vec* v, int value) {
    if (v->size == v->capacity) {
        v->capacity *= 2;
        int* new_data = malloc(v->capacity * sizeof(int));
        memcpy(new_data, v->data, v->size * sizeof(int));
        free(v->data);
        v->data = new_data;
    }
    v->data[v->size++] = value;
}

void vec_free(Vec* v) {
    free(v->data);
    free(v);
}

int main() {
    Vec* scores = vec_new(2);
    vec_push(scores, 85);
    vec_push(scores, 92);

    int* top_score = &scores->data[1];

    vec_push(scores, 78);
    vec_push(scores, 95);
    vec_push(scores, 61);

    printf("Top score was: %d\n", *top_score);

    vec_free(scores);
    return 0;
}
```
If we compile and run it normally: `gcc -o ex2 ex2.c && ./ex2` we see that the output is wrong. 
Try to identify the problem and then 
compile it with the address sanitization option: `gcc -fsanitize=address -g -o ex2 ex2.c` to see if it can automatically detect it. 

The following C++ program, which "mock installs" packages together with their dependencies. 
It first builds a list of dependencies to install, and the installs them (simulated here by just printing "installing ...").
A simple compile and run `g++ -std=c++17 -o ex2b ex2b.cpp` shows again that some packages are missed. 
Same as before, try to discover what is happen, and then see if `g++ -std=c++17 -fsanitize=address -o ex2b ex2b.cpp && ./ex2b`
catches an error with the program.
```
#include <iostream>
#include <vector>
#include <set>
#include <map>
#include <string>

int main() {
    std::map<std::string, std::vector<std::string>> deps = {
        {"curl",    {"openssl", "nghttp2"}},
        {"openssl", {"zlib", "libcrypt"}},
        {"nghttp2", {"zlib"}},
        {"python",  {"zlib", "libffi", "readline"}},
    };

    std::cout << "Resolving dependencies... \n";
    std::vector<std::string> to_install = {"curl", "python", "vim"};
    std::set<std::string> seen(to_install.begin(), to_install.end());

    for (const auto& pkg : to_install) {
        if (deps.count(pkg)) {
            for (const auto& dep : deps[pkg]) {
                if (seen.insert(dep).second) {
                    to_install.push_back(dep);
                }
            }
        }
    }

    std::cout << "Packages to install: " << to_install.size() << " packages" << std::endl;
    for (const auto& pkg : to_install) {
        std::cout << "  installing " << pkg << std::endl;
    }
    std::cout << "done." << std::endl;
    return 0;
}
```

## Exercise 3 

Valgrind is a tool that runs programs in a managed execution environment 
where it can detect, among other things, memory errors like leaks or use-after-free's.
The following program contains 3 bugs related to memory-management. 
```
// Compile: gcc -g -o ex3 ex3.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* name;
    int*  grades;
    int   count;
} Student;

Student* new_student(const char* name, int grades[], int n) {
    Student* s = malloc(sizeof(Student));
    s->name = malloc(strlen(name));  
    strcpy(s->name, name);
    s->grades = malloc(n * sizeof(int));
    memcpy(s->grades, grades, n * sizeof(int));
    s->count = n;
    return s;
}

float average(Student* s) {
    int sum = 0;
    for (int i = 0; i <= s->count; i++) {  
        sum += s->grades[i];
    }
    return (float)sum / s->count;
}

void free_student(Student* s) {
    free(s->name);
    free(s);
}

int main() {
    int grades[] = {85, 90, 78, 92};
    Student* alice = new_student("Alice", grades, 4);
    printf("%s: avg = %.1f\n", alice->name, average(alice));
    free_student(alice);
    return 0;
}
```
Try first to identify them yourselves. Then, run the program in `valgrind`: 
`valgrind --leak-check=full ./ex3` and try to understand the output and to relate 
it to what actually happens in the code.  


## Exercise 4 

A profiler allows us to get statistics regarding the resources used by the program,
commonly CPU usage, or memory. An example is the `perf` program on Linux (search for installation instructions specific to your system). 

The following is a rather inefficient word frequency counter.
```
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> words;
    std::istringstream stream(text);
    std::string word;
    while (stream >> word) {
        for (auto& c : word) c = std::tolower(c);
        words.push_back(word);
    }
    return words;
}

std::vector<std::string> unique_words(const std::vector<std::string>& words) {
    std::vector<std::string> seen;
    for (const auto& w : words) {
        bool found = false;
        for (const auto& s : seen) {   
            if (s == w) { found = true; break; }
        }
        if (!found) seen.push_back(w);
    }
    return seen;
}

int count_word(const std::vector<std::string>& words, const std::string& target) {
    int n = 0;
    for (const auto& w : words) {   
        if (w == target) n++;
    }
    return n;
}

int main(int argc, char* argv[]) {
    const char* filename = argc > 1 ? argv[1] : "big.txt";
    std::ifstream file(filename);
    if (!file) { std::cerr << "cannot open " << filename << std::endl; return 1; }

    std::string text((std::istreambuf_iterator<char>(file)),
                      std::istreambuf_iterator<char>());

    auto words = tokenize(text);
    auto vocab = unique_words(words);

    std::vector<std::pair<std::string, int>> freqs;
    for (const auto& w : vocab) {
        freqs.push_back({w, count_word(words, w)});
    }

    std::partial_sort(freqs.begin(),
        freqs.begin() + std::min<size_t>(10, freqs.size()),
        freqs.end(),
        [](const auto& a, const auto& b) { return a.second > b.second; });

    for (int i = 0; i < 10 && i < (int)freqs.size(); i++) {
        std::cout << freqs[i].first << " " << freqs[i].second << std::endl;
    }
    return 0;
}

```
Compile it and 
run the executable through `perf` to generate a so-called "flamegraph": 
`perf record -g ./ex4 && perf script report flamegraph && firefox flamegraph.html` 
(change the browser accordingly if needed).

You can also try to run profile a real program on your machine, 
for instance `perf record -g openssl speed -seconds 3 sha256 && perf script report flamegraph && firefox flamegraph.html`

## Exercise 5 

C++ compiler errors related to templates are notoriously inscrutable. 
Below is a small example. 
```
/*
 * Compile: g++ -std=c++17 -o ex5 ex5.cpp
 */
#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <algorithm>

int main() {
    std::map<std::string, std::vector<int>> gradebook = {
        {"alice",   {90, 85, 92}},
        {"bob",     {78, 88}},
        {"charlie", {95, 70, 80}},
    };

    std::map<std::string, int> averages;
    for (auto& [name, scores] : gradebook) {
        int sum = 0;
        for (int s : scores) sum += s;
        averages[name] = sum / scores.size();
    }

    std::sort(averages.begin(), averages.end());

    std::cout << "Rankings:" << std::endl;
    for (auto& [name, avg] : averages) {
        std::cout << "  " << name << ": " << avg << std::endl;
    }

    return 0;
}

```
Try to compile the program and observe the crazy error message. 
Use an LLM to try to get a human-readable version of the message and how it relates to the program.