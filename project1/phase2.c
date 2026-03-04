
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <stdint.h>

#define NUM_ACCOUNTS 2
#define NUM_THREADS 4
#define TRANSACTIONS_PER_THREAD 10
#define INITIAL_BALANCE 1000.0

typedef struct {
    int account_id;
    double balance;
    int transaction_count;
    pthread_mutex_t lock; // mutex per account
} Account;

Account accounts[NUM_ACCOUNTS];


double total_deposits = 0.0;
double total_withdrawals = 0.0;
pthread_mutex_t totals_lock = PTHREAD_MUTEX_INITIALIZER;


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


void deposit_safe(int account_id, double amount) {
    pthread_mutex_lock(&accounts[account_id].lock);

    
    accounts[account_id].balance += amount;
    accounts[account_id].transaction_count++;

    pthread_mutex_unlock(&accounts[account_id].lock);

    
    pthread_mutex_lock(&totals_lock);
    total_deposits += amount;
    pthread_mutex_unlock(&totals_lock);
}

// TODO 1: withdrawal_safe with mutex protection
void withdrawal_safe(int account_id, double amount) {
    pthread_mutex_lock(&accounts[account_id].lock);

    
    accounts[account_id].balance -= amount;
    accounts[account_id].transaction_count++;

    pthread_mutex_unlock(&accounts[account_id].lock);

    pthread_mutex_lock(&totals_lock);
    total_withdrawals += amount;
    pthread_mutex_unlock(&totals_lock);
}

// TODO 2: teller_thread uses safe functions
void* teller_thread(void* arg) {
    int teller_id = *(int*)arg;
    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)(uintptr_t)pthread_self() ^ (unsigned int)teller_id;

    for (int i = 0; i < TRANSACTIONS_PER_THREAD; i++) {
        int acc = rand_r(&seed) % NUM_ACCOUNTS;
        double amount = (rand_r(&seed) % 100) + 1;
        int choice = rand_r(&seed) % 2;

        if (choice == 1) {
            deposit_safe(acc, amount);
            printf("Teller %d deposited %.2f into account %d\n", teller_id, amount, acc);
        } else {
            withdrawal_safe(acc, amount);
            printf("Teller %d withdrew  %.2f from account %d\n", teller_id, amount, acc);
        }
    }

    return NULL;
}

// TODO 4: cleanup mutexes after threads finish
void cleanup_mutexes() {
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        pthread_mutex_destroy(&accounts[i].lock);
    }
    pthread_mutex_destroy(&totals_lock);
}

int main() {

    
    total_deposits = 0.0;
    total_withdrawals = 0.0;

    initialize_accounts();

    printf("=== Phase 2: Mutex Protection + Timing ===\n");

    pthread_t threads[NUM_THREADS];
    int ids[NUM_THREADS];

    // TODO 3: performance timing (with locks)
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    
    for (int i = 0; i < NUM_THREADS; i++) {
    ids[i] = i;
    int rc = pthread_create(&threads[i], NULL, teller_thread, &ids[i]);
    if (rc != 0) {
        fprintf(stderr, "pthread_create failed for thread %d (code %d)\n", i, rc);
        exit(1);
    }
}

    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double time_with_locks = elapsed_seconds(start, end);

    
    double actual_total = 0.0;
    printf("\n--- Final Balances ---\n");
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        printf("Account %d: %.2f (%d transactions)\n",
               i, accounts[i].balance, accounts[i].transaction_count);
        actual_total += accounts[i].balance;
    }

    double initial_total = NUM_ACCOUNTS * INITIAL_BALANCE;

    
    double expected_total = initial_total + (total_deposits - total_withdrawals);

    printf("\nInitial total:   %.2f\n", initial_total);
    printf("Total deposits:  %.2f\n", total_deposits);
    printf("Total withdraws: %.2f\n", total_withdrawals);

    printf("\nExpected total:  %.2f\n", expected_total);
    printf("Actual total:    %.2f\n", actual_total);
    printf("Difference:      %.2f\n", actual_total - expected_total);

    printf("\nTime (with locks): %.6f seconds\n", time_with_locks);

    
    cleanup_mutexes();

    return 0;
}





