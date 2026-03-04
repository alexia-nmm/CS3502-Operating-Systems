#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>

#define NUM_ACCOUNTS 2
#define INITIAL_BALANCE 1000.0

#define NUM_THREADS 2
#define TRANSFERS_PER_THREAD 2000
#define MAX_AMOUNT 50


typedef struct {
    int account_id;
    double balance;
    int transaction_count;
    pthread_mutex_t lock;
} Account;

typedef struct {
    int from;
    int to;
} ThreadArgs;

Account accounts[NUM_ACCOUNTS];

double elapsed_seconds(struct timespec start, struct timespec end) {
    double sec = (double)(end.tv_sec - start.tv_sec);
    double nsec = (double)(end.tv_nsec - start.tv_nsec) / 1000000000.0;
    return sec + nsec;
}

void initialize_accounts() {
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        accounts[i].account_id = i;
        accounts[i].balance = INITIAL_BALANCE;
        accounts[i].transaction_count = 0;
        pthread_mutex_init(&accounts[i].lock, NULL);
    }
}

void cleanup_mutexes() {
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        pthread_mutex_destroy(&accounts[i].lock);
    }
}

double total_money() {
    double total = 0.0;
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        total += accounts[i].balance;
    }
    return total;
}
// Deadlock prevention using lock ordering
// Always lock the lower account ID first to avoid circular wait
int safe_transfer_ordered(int from, int to, double amount) {

    int first = (from < to) ? from : to;
    int second = (from < to) ? to : from;

    pthread_mutex_lock(&accounts[first].lock);
    pthread_mutex_lock(&accounts[second].lock);

    if (accounts[from].balance >= amount) {
        accounts[from].balance -= amount;
        accounts[to].balance += amount;
        accounts[from].transaction_count++;
        accounts[to].transaction_count++;
    }

    pthread_mutex_unlock(&accounts[second].lock);
    pthread_mutex_unlock(&accounts[first].lock);

    return 1;
}

void* worker(void* arg) {
    ThreadArgs* a = (ThreadArgs*)arg;
    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)(uintptr_t)pthread_self() ^ (unsigned int)a->from;

    for (int i = 0; i < TRANSFERS_PER_THREAD; i++) {
        double amt = (double)((rand_r(&seed) % MAX_AMOUNT) + 1);
        safe_transfer_ordered(a->from, a->to, amt);
        usleep(1);
    }

    return NULL;
}

int main() {

    printf("=== Phase 4: Deadlock Resolution (Lock Ordering) ===\n");

    initialize_accounts();

    double start_total = total_money();

    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    args[0].from = 0;
    args[0].to = 1;

    args[1].from = 1;
    args[1].to = 0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    int rc = pthread_create(&threads[0], NULL, worker, &args[0]);
	if (rc != 0) { fprintf(stderr, "pthread_create failed (code %d)\n", rc); exit(1); }

	rc = pthread_create(&threads[1], NULL, worker, &args[1]);
	if (rc != 0) { fprintf(stderr, "pthread_create failed (code %d)\n", rc); exit(1); }

    pthread_join(threads[0], NULL);
    pthread_join(threads[1], NULL);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double end_total = total_money();
    double seconds = elapsed_seconds(start, end);

    printf("\nTime: %.6f seconds\n", seconds);

    printf("\n--- Final Balances ---\n");
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        printf("Account %d: %.2f (%d transactions)\n",
               i, accounts[i].balance, accounts[i].transaction_count);
    }

    printf("\nStart total: %.2f\n", start_total);
    printf("End total:   %.2f\n", end_total);
    printf("Total diff:  %.2f\n", end_total - start_total);

    cleanup_mutexes();
    return 0;
}
