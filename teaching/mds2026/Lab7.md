# Lab 7: 

Threads let a program run several code sequences concurrently, 
sharing the same memory. 
The following exemplifies the POSIX threads API. 
Note that this is not part of the C standard library. 
The main points you should understand are the functions: 
pthread_create and pthread_join. 
The first one spawns a thread that will execute a function received as argument,
while the second makes the main thread wait for a thread to finishing execution
and get its result.

The program below spawns four threads. Each one prints a message,
sleeps for two seconds, then prints another message. `main` waits
for all four with `pthread_join` and then exits. 
Read the man page or ask an LLM for details. Why do the two functions have the signature they have? 
```
// sleep.c
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>

void* thread_routine(void* arg) {
    int id = *(int*)arg;
    printf("thread %d: going to sleep\n", id);
    sleep(2);
    printf("thread %d: woke up\n", id);
    return NULL;
}

int main(void) {
    pthread_t threads[4];
    int ids[4] = {1, 2, 3, 4};
    for (int i = 0; i < 4; i++)
        pthread_create(&threads[i], NULL, thread_routine, &ids[i]);
    for (int i = 0; i < 4; i++)
        pthread_join(threads[i], NULL);
    printf("all threads done\n");
    return 0;
}
```
Note that you need to link to the `thread` library for compilation.
```
gcc -pthread sleep.c -o sleep
./sleep
```
Measure the total runtime of the program. 


## Exercise 1

Before starting, download four large Wikipedia articles into the lab
directory:
```
curl -sL -A "mds2026-lab" -o a.html "https://en.wikipedia.org/wiki/Moon"
curl -sL -A "mds2026-lab" -o b.html "https://en.wikipedia.org/wiki/Jupiter"
curl -sL -A "mds2026-lab" -o c.html "https://en.wikipedia.org/wiki/Octopus"
curl -sL -A "mds2026-lab" -o d.html "https://en.wikipedia.org/wiki/Coffee"
```



In the example below, we want a program that computes repeated hash for 
several files (to simulate something computationally expensive). 
(you might need `sudo apt install libssl-dev` or analgous for your system).
The function to compute this is already given and you can ignore the details. 
Finish the implementation of the program by completing the `main` and `thread_routine`
functions. 
- Implement two versions: a single-threaded and a multithreaded version 
(with 4 threads, each compute the hash for one single file). 
The threads shouldn't need to do more than call the function with the respective argument.
- Compile the two versions in different executables (`hash1` and `hash4` below)
and compare their performance use the `hyperfine` benchmarker. 
```
gcc -pthread hash.c -o hash1 -lcrypto
gcc -pthread hash.c -o hash4 -lcrypto
hyperfine --warmup 2 ./hash1 ./hash4
```

```

#define OPENSSL_SUPPRESS_DEPRECATED
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <openssl/sha.h>

#define ITERS 2000000


const char* files[4] = {"a.html", "b.html", "c.html", "d.html"};
unsigned long results[4];

// you can ignore the details of this function beyond its signature 
unsigned long stretch_hash(const char* path) {
    FILE* f = fopen(path, "r");
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char* buf = malloc(sz);
    fread(buf, 1, sz, f);
    fclose(f);

    unsigned char digest[32];
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, buf, sz);
    SHA256_Final(digest, &ctx);
    free(buf);

    for (int i = 0; i < ITERS; i++) {
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, digest, 32);
        SHA256_Final(digest, &ctx);
    }

    unsigned long sum = 0;
    for (int i = 0; i < 32; i++) sum += digest[i];
    return sum;
}

void* thread_routine(void* arg) {
    // TO IMPLEMENT 
}

int main(int argc, char** argv) {
    // TO IMPLEMENT 
}
```



## Exercise 2

Generalize Exercise 1 to handle an arbitrary number of files and an
arbitrary number of threads (so, for example, all threads could be occupied at a certain time if we have more files than threads). 
Let the parameters be passed as CLI arguments.



## Exercise 3

Write a program containing two threads that each increase a counter 
(a global variable `int counter = 0`) a large number of times (say `100000`). 
The expected result should be `200000`. 
Run the program several times and notice that some runs return nonsense values. 

## Exercise 4 

The reason for the failure in Exercise 3 is that integer incrementation is a *non-atomic* operation,
meaning essentially that the two threads can become interleaved when executing its underlying primitive operations.
This is known as a data race, and is a root of whole field of problems and solutions, which are beyond the scope of this lab. 

In the program from Exercise 3, change the type of the global `int counter = 0;` 
to `_Atomic int counter = 0;` (you might need to compile with the flag `-std=c11` for this).
The program should now give the correct result. 
Benchmark the two versions again (this one and the one from `Exercise 4`) using `hyperfine`. 

