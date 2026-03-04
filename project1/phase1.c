#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>   
#include <time.h>
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
} Account;

Account accounts[NUM_ACCOUNTS]; 
void deposit_unsafe(int account_id, double amount) {
    double temp = accounts[account_id].balance;  
    usleep(1);                                   
    temp = temp + amount;                        
    accounts[account_id].balance = temp;         
    accounts[account_id].transaction_count++;
}

void withdraw_unsafe(int account_id, double amount) {
    double temp = accounts[account_id].balance;  
    usleep(1);                                   
    temp = temp - amount;                        
    accounts[account_id].balance = temp;         
    accounts[account_id].transaction_count++;
}


void* teller_thread(void* arg) {
    int teller_id = *(int*)arg;
    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)(uintptr_t)pthread_self() ^ (unsigned int)teller_id;

    for (int i = 0; i < TRANSACTIONS_PER_THREAD; i++) {
        int acc = rand_r(&seed) % NUM_ACCOUNTS;
        double amount = (rand_r(&seed) % 100) + 1;
        int choice = rand_r(&seed) % 2;

        if (choice == 1) {
            deposit_unsafe(acc, amount);
            printf("Teller %d deposited %.2f into account %d\n", teller_id, amount, acc);
        } else {
            withdraw_unsafe(acc, amount);
            printf("Teller %d withdrew  %.2f from account %d\n", teller_id, amount, acc);
        }
    }

    return NULL;
}

int main() {
     

    
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        accounts[i].account_id = i;
        accounts[i].balance = INITIAL_BALANCE;
        accounts[i].transaction_count = 0;
    }

    printf("=== Phase 1: No mutex (race conditions) ===\n");

    double expected_total = NUM_ACCOUNTS * INITIAL_BALANCE;

    pthread_t threads[NUM_THREADS];
    int ids[NUM_THREADS];

    
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

    
    double actual_total = 0.0;
    printf("\n--- Final Balances ---\n");
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        printf("Account %d: %.2f  (%d transactions)\n",
               i, accounts[i].balance, accounts[i].transaction_count);
        actual_total += accounts[i].balance;
    }

    printf("\nExpected total: %.2f\n", expected_total);
    printf("Actual total:   %.2f\n", actual_total);
    printf("Difference:     %.2f\n", actual_total - expected_total);

    if (actual_total != expected_total) {
        printf("\nRace condition happened (this is expected in Phase 1).\n");
    } else {
        printf("\nNo mismatch this run. Run it again or increase threads/transactions.\n");
    }

    return 0;
}
